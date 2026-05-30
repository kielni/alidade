"""2-mile buffer polygons around the 11 Bay Area mall points, EPSG:2227.

Source: output/mall_buffers.shp (generated from data/malls.shp).
EPSG:2227 uses US survey feet; 2 miles = 10,560 ft.
Fields: id, Street, mall_name, city (inherited from malls.shp).
"""

from pathlib import Path

import geopandas as gpd

from alidade.models import (
    Layer,
    ProcessingStep,
    PythonAction,
    SimpleFill,
    SingleSymbol,
    Symbol,
)

_BUFFER_FT = 2 * 5280


def buffer_malls(src: Path, output: Path) -> None:
    gdf = gpd.read_file(src)
    gdf = gdf.copy()
    gdf["geometry"] = gdf.geometry.buffer(_BUFFER_FT)
    gdf.to_file(output)


mall_buffers = Layer(
    id="mall_buffers",
    name="Mall 2-Mile Buffers",
    type="vector",
    source="./output/mall_buffers.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=True,
    geometry_type="Polygon",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            layers=[
                SimpleFill(
                    color="144,238,144,64",
                    outline_color="80,160,80,255",
                    outline_width=0.5,
                )
            ],
        )
    ),
    processing_step=ProcessingStep(
        description="Buffer mall points by 2 miles (10,560 ft) in EPSG:2227.",
        action=PythonAction(fn=buffer_malls),
        depends_on=["mall_points"],
        output=Path("output/mall_buffers.shp"),
    ),
)
