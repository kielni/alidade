"""
Weighted overlay suitability raster.

## Inputs

  All vector layers are rasterized to match the slope.tif reference grid
  (CRS EPSG:26910, ~10 m resolution, clipped to park + 100 ft buffer).

  | Layer                       | Source                          | Role        |
  |-----------------------------|---------------------------------|-------------|
  | slope.tif                   | output/slope.tif                | factor      |
  | vegetation.gpkg             | output/vegetation.gpkg          | factor      |
  | priority_developed.gpkg     | output/priority_developed.gpkg  | factor      |
  | priority_roads_trails.gpkg  | output/priority_roads_trails.gpkg | factor    |
  | exclude_water_vegetation.gpkg | output/exclude_water_vegetation.gpkg | mask  |

## Suitability scale: 1–4 (4 = most suitable, 0 = excluded / NoData)

### Slope reclassification (inverted — steeper is more effective for goat grazing)
  slope=1  flat/gentle (0–15%)    → suitability 2
  slope=2  moderate   (15–27%)    → suitability 3
  slope=3  steep      (27–58%)    → suitability 4
  slope=4  too steep  (58%+)      → 0  (hard exclude)
  gdal_calc: (A==1)*2 + (A==2)*3 + (A==3)*4

### Vegetation reclassification (rasterize ENHANCED_LIFEFORM field)
  Shrub                                      → 4  (primary target)
  Non-native Herbaceous                      → 3  (invasive, accessible)
  Herbaceous                                 → 3  (native grassland)
  Eucalyptus / Non-native Forest             → 1  (neutral)
  Forest / Deciduous/Evergreen Hardwood
    / Pine/Cypress                           → 1  (neutral)
  Riparian Forest                            → 0  (hard exclude via vegetation)
  Developed                                  → 0  (hard exclude)
  Use rasterio.features.rasterize with a per-feature burn-value lookup.

### Priority reclassification (rasterize each buffer polygon; binary → 1–4 scale)
  inside buffer → 4,  outside → 1
  Applies to both priority_developed and priority_roads_trails independently.

## Weights (sum = 1.0)
  slope:               0.25
  vegetation:          0.25
  priority_developed:  0.25
  priority_roads_trails: 0.25

  suitability_raw = (
      slope_suit      * 0.25
    + veg_suit        * 0.25
    + priority_dev    * 0.25
    + priority_trails * 0.25
  )

## Exclusion masking (applied after weighted sum)
  Set to 0 where any hard-exclude condition is true:
    - slope=4         (too steep — already 0 from reclassify, belt-and-suspenders)
    - veg=0           (riparian forest or developed — already 0 from reclassify)
    - exclude_water_vegetation raster == 1  (100 ft riparian stream buffer)
  Final mask: np.where(exclude, 0, suitability_raw)

  Q: is zero-score sufficient to communicate exclusion, or should exclusions be
  a separate display class (e.g., hatch or distinct color)?

## Display classification (4 buckets of non-zero values)
  Compute Jenks natural breaks on non-zero suitability_raw pixels → 4 classes.
  Reclassify non-zero values to 1–4 and write as Byte raster (0 = excluded).
  Color scheme: ColorBrewer Purples 4-class
    1 → #f2f0f7  (low suitability)
    2 → #cbc9e2
    3 → #9e9ac8
    4 → #6a51a3  (high suitability)
    0 → transparent / white (excluded)

## Summary stats to print after build
  - Total park area (non-zero pixels × pixel_area_m2); display as acres
  - % excluded
  - % in each suitability class (1–4)
  - Median weighted score of non-zero pixels

## Implementation approach
  PythonAction using rasterio + numpy + geopandas.
  Reference grid parameters (transform, shape, nodata) read from slope.tif.
  rasterio.features.rasterize for each vector layer.
  numpy for weighted sum, masking, and Jenks classification.
  Write final Byte raster with LZW compression.

## Output
  output/suitability.tif  — Byte, values 0–4, EPSG:26910, LZW compressed
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
from projects.goats.util import CRS

# index = slope class (0=nodata, 1=flat, 2=moderate, 3=steep, 4=too-steep)
_SLOPE_TO_SUIT = np.array([0, 2, 3, 4, 0], dtype="uint8")

_VEG_SUIT: dict[str, int] = {
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
    slope_suit = _SLOPE_TO_SUIT[np.clip(slope_data, 0, 4)]

    veg_gdf = gpd.read_file(vegetation_layer.path).to_crs(CRS)
    veg_shapes = [
        (geom, _VEG_SUIT.get(str(lf), 0))
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

    pdev_raster = _rasterize_binary(
        gpd.read_file(priority_developed_layer.path).to_crs(CRS),
        shape,
        transform,
        inside_val=4,
        outside_val=1,
    )
    ptrails_raster = _rasterize_binary(
        gpd.read_file(priority_trails_layer.path).to_crs(CRS),
        shape,
        transform,
        inside_val=4,
        outside_val=1,
    )
    excl_raster = _rasterize_binary(
        gpd.read_file(exclusion_layer.path).to_crs(CRS),
        shape,
        transform,
        inside_val=1,
        outside_val=0,
    )

    suitability_raw = (
        slope_suit.astype(float) * 0.25
        + veg_raster.astype(float) * 0.25
        + pdev_raster.astype(float) * 0.25
        + ptrails_raster.astype(float) * 0.25
    )

    excluded = (slope_suit == 0) | (veg_raster == 0) | (excl_raster == 1)
    suitability_raw[excluded] = 0.0

    valid_mask = suitability_raw > 0
    valid_vals = suitability_raw[valid_mask]
    jnb = mapclassify.NaturalBreaks(valid_vals, k=4)
    suitability_class = np.zeros(shape, dtype="uint8")
    suitability_class[valid_mask] = (jnb.yb + 1).astype("uint8")

    pixel_area_m2 = abs(transform.a * transform.e)
    valid_n = int(valid_mask.sum())
    acres = valid_n * pixel_area_m2 / 4046.856
    print(f"  suitable area: {acres:.1f} acres")
    for cls in range(1, 5):
        n = int((suitability_class == cls).sum())
        print(f"  class {cls}: {n} px ({n / max(valid_n, 1) * 100:.1f}%)")
    print(f"  median weighted score: {float(np.median(valid_vals)):.2f}")

    park_gdf = gpd.read_file(boundary_layer.path).to_crs(CRS)
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
            PaletteEntry(value=1, color="#f2f0f7", label="Low"),
            PaletteEntry(value=2, color="#cbc9e2", label="Moderate"),
            PaletteEntry(value=3, color="#9e9ac8", label="High"),
            PaletteEntry(value=4, color="#6a51a3", label="Very high"),
        ]
    ),
    action=PythonAction(fn=build_suitability),
)
