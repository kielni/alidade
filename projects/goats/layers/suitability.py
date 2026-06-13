"""
Weighted overlay suitability raster.

Inputs

  All vector layers are rasterized to match the slope.tif reference grid
  (CRS EPSG:26910, ~10 m resolution, clipped to park + 100 ft buffer).

  | Layer                       | Source                          | Role        |
  |-----------------------------|---------------------------------|-------------|
  | slope.tif                   | output/slope.tif                | factor      |
  | vegetation.gpkg             | output/vegetation.gpkg          | factor      |
  | priority_developed.gpkg     | output/priority_developed.gpkg  | factor      |
  | priority_roads_trails.gpkg  | output/priority_roads_trails.gpkg | factor    |
  | exclude_water_vegetation.gpkg | output/exclude_water_vegetation.gpkg | mask  |

Suitability scale: 1-4 (4 = most suitable, 0 = excluded / NoData)

Slope reclassification (inverted — steeper is more effective for goat grazing)
  slope=1  flat/gentle (0-15%)    → suitability 2
  slope=2  moderate   (15-27%)    → suitability 3
  slope=3  steep      (27-58%)    → suitability 4
  slope=4  too steep  (58%+)      → 0  (hard exclude)
  gdal_calc: (A==1)*2 + (A==2)*3 + (A==3)*4

Vegetation reclassification (rasterize ENHANCED_LIFEFORM field)
  Shrub                                      → 4  (primary target)
  Non-native Herbaceous                      → 3  (invasive, accessible)
  Herbaceous                                 → 3  (native grassland)
  Eucalyptus / Non-native Forest             → 1  (neutral)
  Forest / Deciduous/Evergreen Hardwood
    / Pine/Cypress                           → 1  (neutral)
  Riparian Forest                            → 0  (hard exclude via vegetation)
  Developed                                  → 0  (hard exclude)
  Use rasterio.features.rasterize with a per-feature burn-value lookup.

Priority reclassification (rasterize each buffer polygon; binary → 1-4 scale)
  inside buffer → 4,  outside → 1
  The two priority rasters are merged into a single priority layer before
  scoring: priority = max(priority_developed, priority_roads_trails), so a
  pixel inside either buffer gets 4 and a pixel outside both gets 1.

Weights (sum = 1.0)
  slope:    1/3
  vegetation: 1/3
  priority: 1/3   (combined from priority_developed and priority_roads_trails)

  priority_suit = np.maximum(priority_dev, priority_trails)
  suitability_raw = (
      slope_suit    * (1/3)
    + veg_suit      * (1/3)
    + priority_suit * (1/3)
  )

Exclusion masking (applied after weighted sum)
  Set to 0 where any hard-exclude condition is true:
    - slope=4         (too steep — already 0 from reclassify, belt-and-suspenders)
    - veg=0           (riparian forest or developed — already 0 from reclassify)
    - exclude_water_vegetation raster == 1  (100 ft riparian stream buffer)
  Final mask: np.where(exclude, 0, suitability_raw)

Display classification (4 buckets of non-zero values)
  Compute Jenks natural breaks on non-zero suitability_raw pixels → 4 classes.
  Reclassify non-zero values to 1-4 and write as Byte raster (0 = excluded).
  Color scheme: ColorBrewer Purples 4-class, transparent for excluded

Summary stats to print after build
  - Total park area (non-zero pixels x pixel_area_m2); display as acres
  - % excluded
  - % in each suitability class (1-4)
  - Median weighted score of non-zero pixels

Implementation approach
  PythonAction using rasterio + numpy + geopandas.
  Reference grid parameters (transform, shape, nodata) read from slope.tif.
  rasterio.features.rasterize for each vector layer.
  numpy for weighted sum, masking, and Jenks classification.
  Write final Byte raster with LZW compression.

"""

from typing import Any

import geopandas as gpd
import mapclassify
import numpy as np
import rasterio
import rasterio.features

from alidade.models import (
    BoundLayer,
    Layer,
    PaletteEntry,
    PalettedRenderer,
    PythonAction,
)
from projects.goats.layers.exclude_water_vegetation import exclude_water_vegetation
from projects.goats.layers.park_boundary import park_boundary
from projects.goats.layers.priority_developed import priority_developed
from projects.goats.layers.priority_roads_trails import priority_roads_trails
from projects.goats.layers.slope import slope
from projects.goats.layers.vegetation import vegetation
from projects.goats.palette import SUITABILITY
from projects.goats.util import CRS

M2_PER_ACRE = 4046.856

# Overlay weights: must sum to 1.0
WEIGHT_SLOPE = 1 / 3
WEIGHT_VEGETATION = 1 / 3
WEIGHT_PRIORITY = 1 / 3

# index = slope class (0=nodata, 1=flat, 2=moderate, 3=steep, 4=too-steep)
SLOPE_TO_SUITABILITY = np.array([0, 2, 3, 4, 0], dtype="uint8")

VEGETATION_SUITABILITY: dict[str, int] = {
    "Shrub": 4,
    "Non-native Herbaceous": 3,
    "Herbaceous": 3,
    "Eucalyptus": 1,
    "Non-native Forest": 1,
    "Forest": 1,
    "Deciduous Hardwood": 1,
    "Evergreen Hardwood": 1,
    "Pine/Cypress": 1,
    "Riparian Forest": 0,
    "Developed": 0,
}


def _rasterize_binary(
    gdf: gpd.GeoDataFrame,
    shape: tuple[int, int],
    transform: Any,
    *,
    inside_val: int,
    outside_val: int,
) -> np.ndarray:
    """Rasterize polygons to a uniform raster with distinct inside/outside values."""
    shapes = [(geom, inside_val) for geom in gdf.geometry if geom is not None]
    return rasterio.features.rasterize(
        shapes,
        out_shape=shape,
        transform=transform,
        fill=outside_val,
        dtype="uint8",
    )


def build_suitability(layer: BoundLayer) -> None:
    """Weighted overlay: slope + vegetation + priority buffers → suitability raster."""
    (
        boundary_layer,
        slope_layer,
        vegetation_layer,
        priority_developed_layer,
        priority_trails_layer,
        exclusion_layer,
    ) = layer.inputs

    with rasterio.open(slope_layer.path) as src:
        profile = src.profile.copy()
        slope_data = src.read(1)
        transform = src.transform
        shape = (src.height, src.width)

    # Invert slope classes: steep terrain is most effective for goat grazing
    slope_suit = SLOPE_TO_SUITABILITY[np.clip(slope_data, 0, 4)]

    # convert vector vegetation to raster to line up with slope
    veg_gdf = gpd.read_file(vegetation_layer.path).to_crs(CRS)
    veg_shapes = [
        (geom, VEGETATION_SUITABILITY.get(str(lf), 0))
        for geom, lf in zip(veg_gdf.geometry, veg_gdf["ENHANCED_LIFEFORM"])
        if geom is not None and not geom.is_empty
    ]
    veg_raster = rasterio.features.rasterize(
        veg_shapes,
        out_shape=shape,
        transform=transform,
        fill=0,
        dtype="uint8",
    )

    # convert vector priority areas to raster to line up with slope
    priority_developed_raster = _rasterize_binary(
        gpd.read_file(priority_developed_layer.path).to_crs(CRS),
        shape,
        transform,
        inside_val=4,
        outside_val=1,
    )
    priority_trails_raster = _rasterize_binary(
        gpd.read_file(priority_trails_layer.path).to_crs(CRS),
        shape,
        transform,
        inside_val=4,
        outside_val=1,
    )
    # convert vector exclusion areas to raster to line up with slope
    excl_raster = _rasterize_binary(
        gpd.read_file(exclusion_layer.path).to_crs(CRS),
        shape,
        transform,
        inside_val=1,
        outside_val=0,
    )

    # merge priority datasets: a pixel in either buffer scores 4, outside both scores 1
    priority_raster = np.maximum(priority_developed_raster, priority_trails_raster)

    # calculate per-pixel suitability
    suitability_raw = (
        slope_suit.astype(float) * WEIGHT_SLOPE
        + veg_raster.astype(float) * WEIGHT_VEGETATION
        + priority_raster.astype(float) * WEIGHT_PRIORITY
    )

    # adjust for excluded areas
    excluded = (slope_suit == 0) | (veg_raster == 0) | (excl_raster == 1)
    suitability_raw[excluded] = 0.0

    valid_mask = suitability_raw > 0
    valid_vals = suitability_raw[valid_mask]

    # find class boundaries
    jenks_breaks = mapclassify.NaturalBreaks(valid_vals, k=4)
    suitability_class = np.zeros(shape, dtype="uint8")
    suitability_class[valid_mask] = (jenks_breaks.yb + 1).astype("uint8")

    pixel_area_m2 = abs(transform.a * transform.e)
    valid_n = int(valid_mask.sum())
    acres = valid_n * pixel_area_m2 / M2_PER_ACRE
    print(f"  suitable area: {acres:.1f} acres")
    for cls in range(1, 5):
        n = int((suitability_class == cls).sum())
        print(f"  class {cls}: {n} px ({n / max(valid_n, 1) * 100:.1f}%)")
    print(f"  median weighted score: {float(np.median(valid_vals)):.2f}")

    park_gdf = gpd.read_file(boundary_layer.path).to_crs(CRS)

    # trim buffer area outside the park
    outside_park = rasterio.features.geometry_mask(
        [geom for geom in park_gdf.geometry if geom is not None],
        out_shape=shape,
        transform=transform,
        invert=False,
    )
    suitability_class[outside_park] = 0

    profile.update(dtype="uint8", count=1, nodata=0, compress="lzw")
    with rasterio.open(layer.path, "w", **profile) as dst:
        dst.write(suitability_class, 1)


suitability = Layer(
    id="suitability",
    name="Suitability",
    type="raster",
    inputs=[
        park_boundary,
        slope,
        vegetation,
        priority_developed,
        priority_roads_trails,
        exclude_water_vegetation,
    ],
    datasource="output/suitability.tif",
    provider="gdal",
    crs=CRS,
    visible=True,
    renderer=PalettedRenderer(
        entries=[
            PaletteEntry(value=1, color=SUITABILITY[0], label="Low"),
            PaletteEntry(value=2, color=SUITABILITY[1], label="Moderate"),
            PaletteEntry(value=3, color=SUITABILITY[2], label="High"),
            PaletteEntry(value=4, color=SUITABILITY[3], label="Very high"),
        ]
    ),
    action=PythonAction(fn=build_suitability),
)
