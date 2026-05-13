"""Processing helpers for the BufferAndQuery project."""

from __future__ import annotations

import subprocess
from pathlib import Path

import geopandas as gpd

_MILES_TO_METERS = 1609.344


def buffer_capitol_buildings(inputs: list[Path], output: Path) -> None:
    """Buffer State Capitol building points by 25 miles (40,233.6 m in EPSG:3857).

    Reads the input point shapefile, applies a planar buffer in the native CRS
    (EPSG:3857, units are meters), and writes dissolved polygons to output.
    """
    gdf = gpd.read_file(inputs[0])
    buffered = gdf.copy()
    buffered["geometry"] = gdf.geometry.buffer(25 * _MILES_TO_METERS)
    buffered.to_file(output)


def filter_capitol_buffers_near_parks(inputs: list[Path], output: Path) -> None:
    """Filter capitol buffers to those intersecting ≥1 national park; print count.

    inputs[0]: output/capitol_buffer.shp
    inputs[1]: output/national_parks.shp
    """
    capitol_buffers = gpd.read_file(inputs[0])
    national_parks_gdf = gpd.read_file(inputs[1])

    joined = gpd.sjoin(
        capitol_buffers,
        national_parks_gdf[["geometry"]],
        how="inner",
        predicate="intersects",
    )
    result = capitol_buffers.loc[joined.index.unique()]
    result.to_file(output)
    print(
        f"State capitols with 25-mile buffer intersecting a national park:"
        f" {len(result)}"
    )


def filter_national_parks(inputs: list[Path], output: Path) -> None:
    """Filter USAParks.shp to FCC='D83' (National Park Service units) with ogr2ogr.

    ogr2ogr is GDAL's vector data conversion and filtering tool.
    """
    subprocess.run(
        [
            "ogr2ogr",
            "-where",
            "FCC='D83'",
            str(output),
            str(inputs[0]),
        ],
        check=True,
    )
