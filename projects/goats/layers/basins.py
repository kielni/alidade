"""
Terrain-derived grazing basin polygons.

DEM → pysheds (fill pits/depressions, resolve flats, D8 flow direction +
accumulation) → stream reaches labeled by scipy connected components →
non-stream cells labeled by D8 propagation to the reach they drain into →
vectorize → dissolve per basin ID → clip to park → subtract riparian exclusion
buffer (creek buffer splits cross-valley basins into north-face and south-face
units) → drop slivers → score each polygon by suitability_sum → Jenks 4-class
classification (4 = highest).

STREAM_THRESHOLD controls granularity: lower values produce smaller, more
numerous basins. Basin boundaries follow terrain ridgelines and drainage
divides; no convex hulls or rectangular bisection.
"""

import numpy as np
import geopandas as gpd
import mapclassify
import rasterio
import rasterio.features
from pysheds.grid import Grid
from rasterstats import zonal_stats
from scipy import ndimage
from shapely.geometry import shape

from alidade.models import (
    BoundLayer,
    Layer,
    PythonAction,
    Rule,
    RuleRenderer,
    SimpleFill,
    Symbol,
)
from projects.goats.layers.elevation import elevation
from projects.goats.layers.exclude_water_vegetation import exclude_water_vegetation
from projects.goats.layers.park_boundary import park_boundary
from projects.goats.layers.suitability import suitability
from projects.goats.palette import FEATURE_EDGE, SUITABILITY
from projects.goats.util import CRS, clip_park

# 1 acre minimum — filters slivers from riparian subtraction and park clipping
MIN_AREA_M2 = 4_047.0

# Cells with accumulation > this define the stream network. At 10 m resolution,
# 1 cell = 100 m²; 200 cells ≈ 5 acres contributing area. Lower → smaller basins.
STREAM_THRESHOLD = 20

# pysheds default D8 dirmap: (N, NE, E, SE, S, SW, W, NW)
_DIRMAP = (64, 128, 1, 2, 4, 8, 16, 32)

# Row, col offsets for each D8 direction value (row increases downward)
_D8_OFFSETS: dict[int, tuple[int, int]] = {
    64: (-1, 0),
    128: (-1, 1),
    1: (0, 1),
    2: (1, 1),
    4: (1, 0),
    8: (1, -1),
    16: (0, -1),
    32: (-1, -1),
}

# ColorBrewer Purples 4-class — darker = higher suitability sum
_BASIN_CLASSES = [
    ("basin1", "Low", '"basin_class" = 1', SUITABILITY[0]),
    ("basin2", "Moderate", '"basin_class" = 2', SUITABILITY[1]),
    ("basin3", "High", '"basin_class" = 3', SUITABILITY[2]),
    ("basin4", "Very high", '"basin_class" = 4', SUITABILITY[3]),
]


def build_basins(layer: BoundLayer) -> None:
    """Delineate terrain drainage basins from DEM and score by suitability sum."""
    (
        boundary_layer,
        elevation_layer,
        suitability_layer,
        exclusion_layer,
    ) = layer.inputs

    with rasterio.open(elevation_layer.path) as src:
        dem_transform = src.transform

    # Hydrological conditioning
    grid = Grid.from_raster(str(elevation_layer.path))
    dem = grid.read_raster(str(elevation_layer.path))
    pit_filled = grid.fill_pits(dem)
    flooded = grid.fill_depressions(pit_filled)
    inflated = grid.resolve_flats(flooded)
    fdir = grid.flowdir(inflated, dirmap=_DIRMAP)
    acc = grid.accumulation(fdir, dirmap=_DIRMAP)

    acc_array = np.asarray(acc, dtype=float)
    fdir_array = np.asarray(fdir, dtype=np.int32)
    rows, cols = fdir_array.shape

    # Label each connected stream reach with a unique integer
    stream_mask = acc_array > STREAM_THRESHOLD
    stream_labels, n_reaches = ndimage.label(stream_mask, structure=np.ones((3, 3)))
    print(f"  stream reaches: {n_reaches}")

    # Propagate reach labels upstream along D8 flow paths. Processing in
    # decreasing accumulation order guarantees each cell's downstream neighbor
    # is already labeled before the current cell is visited.
    basin_array = stream_labels.astype(np.int32).copy()
    for flat_idx in np.argsort(acc_array.ravel())[::-1]:
        r, c = divmod(int(flat_idx), cols)
        if basin_array[r, c] != 0:
            continue
        offsets = _D8_OFFSETS.get(int(fdir_array[r, c]))
        if offsets is None:
            continue
        dr, dc = offsets
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            basin_array[r, c] = basin_array[nr, nc]

    # Cells draining out of the grid without passing through a stream reach
    # (e.g. north slopes exiting the park boundary directly) get their own
    # labels via connected components so they are not silently discarded.
    unlabeled = (basin_array == 0) & (acc_array > 0)
    if unlabeled.any():
        extra_labels, _ = ndimage.label(unlabeled, structure=np.ones((3, 3)))
        max_label = int(basin_array.max())
        basin_array[unlabeled] = extra_labels[unlabeled] + max_label

    # Vectorize; uint16 is sufficient for any park-scale basin count
    basin_u16 = np.clip(basin_array, 0, 65535).astype(np.uint16)
    polys = [
        {"geometry": shape(geom), "basin_id": int(val)}
        for geom, val in rasterio.features.shapes(basin_u16, transform=dem_transform)
        if int(val) > 0
    ]
    gdf = gpd.GeoDataFrame(polys, crs=CRS)

    # Merge pixel polygons belonging to the same basin into one polygon
    gdf = gdf.dissolve(by="basin_id").reset_index()

    gdf = clip_park(gdf, boundary_layer.path).copy()
    gdf = gdf[~gdf.geometry.is_empty].copy()

    # Riparian exclusion buffer splits basins that straddle the creek corridor;
    # re-explode so each slope face becomes its own row
    excl = gpd.read_file(exclusion_layer.path).to_crs(CRS).dissolve()
    if not excl.empty:
        excl_geom = excl.geometry.iloc[0]
        gdf.geometry = gdf.geometry.difference(excl_geom)
    gdf = gdf[~gdf.geometry.is_empty].copy()
    gdf = gdf.explode(index_parts=False).reset_index(drop=True)
    gdf = gdf[gdf.geometry.area >= MIN_AREA_M2].copy()

    gdf = gdf.reset_index(drop=True)
    gdf["basin_id"] = gdf.index + 1
    gdf["size_acres"] = (gdf.geometry.area / 4046.856).round(2)

    stats = zonal_stats(gdf, str(suitability_layer.path), stats=["sum"], nodata=0)
    gdf["suitability_sum"] = [float(s.get("sum") or 0.0) for s in stats]

    valid = gdf["suitability_sum"] > 0
    if valid.sum() >= 4:
        jnb = mapclassify.NaturalBreaks(gdf.loc[valid, "suitability_sum"], k=4)
        gdf["basin_class"] = 0
        gdf.loc[valid, "basin_class"] = (jnb.yb + 1).astype(int)
    else:
        gdf["basin_class"] = 1

    for cls in range(1, 5):
        n = int((gdf["basin_class"] == cls).sum())
        print(f"  class {cls}: {n} basins")
    print(f"  total basins: {len(gdf)}")

    high = gdf[gdf["basin_class"] >= 3].sort_values("suitability_sum", ascending=False)
    print(f"\n  High + Very high basins ({len(high)} total):")
    for _, row in high.iterrows():
        label = "Very high" if int(row["basin_class"]) == 4 else "High     "
        print(
            f"    B{int(row['basin_id']):03d}  {label}  "
            f"{row['size_acres']:.2f} ac  "
            f"suit={row['suitability_sum']:.1f}"
        )

    gdf.to_file(layer.path, driver="GPKG")


_rules = [
    Rule(key=key, label=label, filter=filt, symbol_index=i)
    for i, (key, label, filt, _) in enumerate(_BASIN_CLASSES)
]

_symbols = [
    Symbol(
        type="fill",
        layers=[
            SimpleFill(
                color=color,
                style="solid",
                outline_color=FEATURE_EDGE,
                outline_width=0.4,
            )
        ],
    )
    for _, _, _, color in _BASIN_CLASSES
]

basins = Layer(
    id="terrain_basins",
    name="Terrain Basins",
    type="vector",
    inputs=[park_boundary, elevation, suitability, exclude_water_vegetation],
    datasource="output/basins.gpkg",
    provider="ogr",
    crs=CRS,
    visible=True,
    geometry_type="Polygon",
    renderer=RuleRenderer(
        rules_key="basin",
        rules=_rules,
        symbols=_symbols,
    ),
    action=PythonAction(fn=build_basins),
)
