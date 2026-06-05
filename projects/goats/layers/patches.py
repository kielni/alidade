"""
Grazeable patch polygons derived from the suitability raster.

Vectorize non-zero suitability pixels → convex hull → union overlapping hulls
→ bisect large patches → subtract riparian exclusions (re-explode if a creek
splits a patch) → clip to park boundary. Score each polygon by
suitability_sum / perimeter; patch_class 1–4 via Jenks natural breaks
(4 = highest score).
"""

import geopandas as gpd
import mapclassify
import rasterio
import rasterio.features
from rasterstats import zonal_stats
from shapely.geometry import box, shape
from shapely.geometry.base import BaseGeometry

from alidade.models import (
    BoundLayer,
    Layer,
    PythonAction,
    Rule,
    RuleRenderer,
    SimpleFill,
    Symbol,
)
from projects.goats.layers.exclude_water_vegetation import exclude_water_vegetation
from projects.goats.layers.park_boundary import park_boundary
from projects.goats.layers.suitability import suitability
from projects.goats.util import CRS, clip_park, hex_to_rgba

# about 1/8 acre
MIN_AREA_M2 = 500.0
# about 30 acres: 100 goats x 30 days
MAX_AREA_M2 = 120_000.0

# ColorBrewer Purples 4-class — darker = higher patch score
PATCH_CLASSES = [
    ("patch1", "Low", '"patch_class" = 1', "#f2f0f7"),
    ("patch2", "Moderate", '"patch_class" = 2', "#cbc9e2"),
    ("patch3", "High", '"patch_class" = 3', "#9e9ac8"),
    ("patch4", "Very high", '"patch_class" = 4', "#6a51a3"),
]


def _subdivide(geom: BaseGeometry, max_area_m2: float) -> list[BaseGeometry]:
    """Bisect a polygon along its longer axis until all parts are ≤ max_area_m2."""
    if geom.area <= max_area_m2:
        return [geom]
    minx, miny, maxx, maxy = geom.bounds
    if (maxx - minx) >= (maxy - miny):
        mid = (minx + maxx) / 2
        halves = [
            geom.intersection(box(minx, miny, mid, maxy)),
            geom.intersection(box(mid, miny, maxx, maxy)),
        ]
    else:
        mid = (miny + maxy) / 2
        halves = [
            geom.intersection(box(minx, miny, maxx, mid)),
            geom.intersection(box(minx, mid, maxx, maxy)),
        ]
    result = []
    for half in halves:
        if half.is_empty:
            continue
        for part in getattr(half, "geoms", [half]):
            if part.area > 0:
                result.extend(_subdivide(part, max_area_m2))
    return result


def build_patches(layer: BoundLayer) -> None:
    """Vectorize suitability raster into scored grazeable patches."""
    boundary_layer, suitability_layer, exclusion_layer = layer.inputs

    with rasterio.open(suitability_layer.path) as src:
        data = src.read(1)
        transform = src.transform
        crs_raster = src.crs

    # Vectorize contiguous non-zero regions (one polygon per connected component)
    mask_data = (data > 0).astype("uint8")
    results = [
        {"geometry": shape(geom_dict)}
        for geom_dict, val in rasterio.features.shapes(mask_data, transform=transform)
        if val > 0
    ]
    gdf = gpd.GeoDataFrame(results, crs=crs_raster).to_crs(CRS)

    # Remove noise patches below minimum area
    gdf = gdf[gdf.geometry.area >= MIN_AREA_M2].copy()

    # Convex hull simplifies jagged pixel perimeters; must precede exclusion
    # subtraction — hull of a notched polygon re-fills the notch
    gdf.geometry = gdf.geometry.convex_hull

    # Union overlapping convex hulls into distinct non-overlapping patches,
    # then re-explode so each island is its own row
    gdf = (
        gpd.GeoDataFrame(geometry=[gdf.geometry.union_all()], crs=CRS)
        .explode(index_parts=False)
        .reset_index(drop=True)
    )

    # Bisect any patch that exceeds the target maximum manageable area
    split_geoms: list[BaseGeometry] = []
    for geom in gdf.geometry:
        split_geoms.extend(_subdivide(geom, MAX_AREA_M2))
    gdf = gpd.GeoDataFrame(geometry=split_geoms, crs=CRS).reset_index(drop=True)

    # Subtract riparian exclusion zones after hull; a creek crossing a patch
    # splits it into two separate patches, so re-explode and drop tiny fragments
    excl = gpd.read_file(exclusion_layer.path).to_crs(CRS).dissolve()
    if not excl.empty:
        excl_geom = excl.geometry.iloc[0]
        gdf.geometry = gdf.geometry.difference(excl_geom)
    gdf = gdf[~gdf.geometry.is_empty].copy()
    gdf = gdf.explode(index_parts=False).reset_index(drop=True)
    gdf = gdf[gdf.geometry.area >= MIN_AREA_M2].copy()

    # Clip to exact park boundary so patches don't extend into the buffer zone
    gdf = clip_park(gdf, boundary_layer.path).copy()
    gdf = gdf[~gdf.geometry.is_empty].copy()

    # Stable sequential ID assigned after all geometry operations are complete
    gdf = gdf.reset_index(drop=True)
    gdf["patch_id"] = gdf.index + 1

    # Perimeter, size, and weighted suitability sum per patch
    gdf["perimeter"] = gdf.geometry.length
    gdf["size_acres"] = (gdf.geometry.area / 4046.856).round(2)
    stats = zonal_stats(gdf, str(suitability_layer.path), stats=["sum"], nodata=0)
    gdf["suitability_sum"] = [float(s.get("sum") or 0.0) for s in stats]

    # score = suitability per unit of fencing (perimeter); clamp to avoid /0
    gdf["patch_score"] = gdf["suitability_sum"] / gdf["perimeter"].clip(lower=0.01)

    # Jenks 4-class classification stored as an integer column for the renderer
    valid = gdf["patch_score"] > 0
    if valid.sum() >= 4:
        jnb = mapclassify.NaturalBreaks(gdf.loc[valid, "patch_score"], k=4)
        gdf["patch_class"] = 0
        gdf.loc[valid, "patch_class"] = (jnb.yb + 1).astype(int)
    else:
        gdf["patch_class"] = 1

    for cls in range(1, 5):
        n = int((gdf["patch_class"] == cls).sum())
        print(f"  class {cls}: {n} patches")
    print(f"  total patches: {len(gdf)}")

    high = gdf[gdf["patch_class"] >= 3].sort_values("size_acres", ascending=False)
    print(f"\n  High + Very high patches ({len(high)} total):")
    for _, row in high.iterrows():
        label = "Very high" if int(row["patch_class"]) == 4 else "High     "
        print(f"    P{int(row['patch_id']):03d}  {label}  {row['size_acres']:.2f} ac")

    gdf.to_file(layer.path, driver="GPKG")


_rules = [
    Rule(key=key, label=label, filter=filt, symbol_index=i)
    for i, (key, label, filt, _) in enumerate(PATCH_CLASSES)
]

_symbols = [
    Symbol(
        type="fill",
        layers=[
            SimpleFill(
                color=hex_to_rgba(color, 200),
                style="solid",
                outline_color="0,0,0",
                outline_width=0.2,
            )
        ],
    )
    for _, _, _, color in PATCH_CLASSES
]

patches = Layer(
    id="grazeable_patches",
    name="Grazeable Patches",
    type="vector",
    inputs=[park_boundary, suitability, exclude_water_vegetation],
    datasource="output/patches.gpkg",
    provider="ogr",
    crs=CRS,
    visible=True,
    geometry_type="Polygon",
    renderer=RuleRenderer(
        rules_key="patch",
        rules=_rules,
        symbols=_symbols,
    ),
    action=PythonAction(fn=build_patches),
)
