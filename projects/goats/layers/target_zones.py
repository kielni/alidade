"""
Target grazing polygons derived from the suitability raster.

  - Vectorize non-zero suitability pixels
  - morphological closing (buffer + negative buffer) to merge adjacent pixels
    and round staircase edges
  - union overlapping patches
  - Voronoi-split oversized patches using k-means cluster centers as seeds;
    split lines run through low-suitability terrain gaps between clusters
  - subtract riparian exclusions
  - clip to park

Score each polygon by
suitability_sum / perimeter; patch_class 1-4 via Jenks natural breaks
(4 = highest score).
"""

import math

import geopandas as gpd
import mapclassify
import numpy as np
import rasterio
import rasterio.features
import rasterio.mask
from rasterstats import zonal_stats
from scipy.cluster.vq import kmeans2
from shapely.geometry import MultiPoint, Point, shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import voronoi_diagram

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
from projects.goats.palette import BLACK, SUITABILITY
from projects.goats.util import CRS, clip_park

# about 1/8 acre
MIN_AREA_M2 = 500.0
# about 30 acres: 100 goats x 30 days
MAX_AREA_M2 = 120_000.0
# one pixel width at 10 m resolution — morphological closing distance
SMOOTH_M = 10.0

# darker = higher patch score
PATCH_CLASSES = [
    ("patch1", "Low", '"patch_class" = 1', SUITABILITY[0]),
    ("patch2", "Moderate", '"patch_class" = 2', SUITABILITY[1]),
    ("patch3", "High", '"patch_class" = 3', SUITABILITY[2]),
    ("patch4", "Very high", '"patch_class" = 4', SUITABILITY[3]),
]


def _voronoi_split(
    geom: BaseGeometry,
    suitability_path: object,
    max_area_m2: float,
) -> list[BaseGeometry]:
    """Split a polygon into N pieces using Voronoi regions seeded at suitability maxima.

    K-means cluster centers within the polygon's suitability pixels serve as
    Voronoi seeds; Voronoi boundaries between them pass through low-suitability
    gaps, which correspond to terrain transitions (rock bands, forest edges, etc.).
    """
    if geom.area <= max_area_m2:
        return [geom]

    n = math.ceil(geom.area / max_area_m2)

    try:
        with rasterio.open(suitability_path) as src:
            # fill outside the polygon with 0
            masked, mask_transform = rasterio.mask.mask(
                src, [geom], crop=True, nodata=0
            )
    except Exception:
        return [geom]

    data = masked[0]
    row_idx, col_idx = np.where(data > 0)

    if len(row_idx) < n:
        return [geom]

    # find n cluster centers in the pixel coordinate cloud
    # pixels are weighted by presence (not value), centers gravitate toward the
    # dense cores of high-suitability terrain rather than toward sparse edges
    xs = mask_transform.c + (col_idx + 0.5) * mask_transform.a
    ys = mask_transform.f + (row_idx + 0.5) * mask_transform.e
    coords = np.column_stack([xs, ys]).astype(float)

    centers, _ = kmeans2(coords, min(n, len(coords)), minit="points")
    seed_points = MultiPoint([Point(float(x), float(y)) for x, y in centers])

    # build Voronoi regions around the points
    # each region contains the area closer to its seed than to any other
    regions = voronoi_diagram(seed_points, envelope=geom.envelope)

    result: list[BaseGeometry] = []
    for region in regions.geoms:
        # clip to original polygon
        clipped = geom.intersection(region)
        if clipped.is_empty:
            continue
        for part in getattr(clipped, "geoms", [clipped]):
            if part.area > 0:
                result.append(part)

    return result if result else [geom]


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
        # convert geom_dict to Shapely geometry for geopandas
        {"geometry": shape(geom_dict)}
        # one geometry, value per contiguous region
        for geom_dict, val in rasterio.features.shapes(mask_data, transform=transform)
        if val > 0
    ]
    gdf = gpd.GeoDataFrame(results, crs=crs_raster).to_crs(CRS)
    # drop too-small polygons
    gdf = gdf[gdf.geometry.area >= MIN_AREA_M2].copy()

    # morphological closing to clean up rasterization artifacts
    # outward buffer: merge nearby polygons with small gaps
    # inward buffer: restore the original boundary, now smoothed
    gdf.geometry = gdf.geometry.buffer(SMOOTH_M).buffer(-SMOOTH_M)
    gdf = gdf[~gdf.geometry.is_empty].copy()
    gdf = gdf[gdf.geometry.area >= MIN_AREA_M2].copy()

    # Union overlapping patches, then re-explode so each island is its own row
    gdf = (
        # dissolve into one geometry; removes shared boundaries
        gpd.GeoDataFrame(geometry=[gdf.geometry.union_all()], crs=CRS)
        # split MultiPolygon back into Polygon rows
        .explode(index_parts=False).reset_index(drop=True)
    )

    # Voronoi-split patches that exceed the target area; k-means seeds are placed
    # at suitability maxima within the patch so split lines follow terrain gaps
    split_geoms: list[BaseGeometry] = []
    for geom in gdf.geometry:
        split_geoms.extend(_voronoi_split(geom, suitability_layer.path, MAX_AREA_M2))
    gdf = gpd.GeoDataFrame(geometry=split_geoms, crs=CRS).reset_index(drop=True)

    # Subtract riparian exclusion zones
    excl = gpd.read_file(exclusion_layer.path).to_crs(CRS).dissolve()
    if not excl.empty:
        excl_geom = excl.geometry.iloc[0]
        # subtract exclusion zone from each patch
        gdf.geometry = gdf.geometry.difference(excl_geom)
    # drop now-empty areas
    gdf = gdf[~gdf.geometry.is_empty].copy()
    # promote disconnected fragments to rows
    gdf = gdf.explode(index_parts=False).reset_index(drop=True)
    # drop too-small areas
    gdf = gdf[gdf.geometry.area >= MIN_AREA_M2].copy()

    # Clip to exact park boundary so patches don't extend into the buffer zone
    gdf = clip_park(gdf, boundary_layer.path).copy()
    gdf = gdf[~gdf.geometry.is_empty].copy()

    gdf = gdf.reset_index(drop=True)
    gdf["patch_id"] = gdf.index + 1

    gdf["perimeter"] = gdf.geometry.length
    gdf["size_acres"] = (gdf.geometry.area / 4046.856).round(2)
    stats = zonal_stats(gdf, str(suitability_layer.path), stats=["sum"], nodata=0)
    gdf["suitability_sum"] = [float(s.get("sum") or 0.0) for s in stats]

    # score = suitability per unit of fencing (perimeter); clamp to avoid /0
    gdf["patch_score"] = gdf["suitability_sum"] / gdf["perimeter"].clip(lower=0.01)

    valid = gdf["patch_score"] > 0
    if valid.sum() >= 4:
        # create 4 classes with natural breaks
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
                color=color,
                style="solid",
                outline_color=BLACK,
                outline_width=0.2,
            )
        ],
    )
    for _, _, _, color in PATCH_CLASSES
]

target_zones = Layer(
    id="grazeable_patches",
    name="Target Grazing Zones",
    type="vector",
    inputs=[park_boundary, suitability, exclude_water_vegetation],
    datasource="output/patches.gpkg",
    crs=CRS,
    geometry_type="Polygon",
    renderer=RuleRenderer(
        rules_key="patch",
        rules=_rules,
        symbols=_symbols,
    ),
    action=PythonAction(fn=build_patches),
)
