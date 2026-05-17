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

# output/mall_buffers.shp: 5-mile buffer polygons around each of the 11 mall
# points. EPSG:2227 (US survey feet); 5 miles = 26,400 survey feet.
# Fields: id, name, mall_name, city (inherited from malls.shp).
_BUFFER_FT = 5 * 5280


def buffer_malls(src: Path, output: Path) -> None:
    gdf = gpd.read_file(src)
    gdf = gdf.copy()
    gdf["geometry"] = gdf.geometry.buffer(_BUFFER_FT)
    gdf.to_file(output)


mall_buffers = Layer(
    id="mall_buffers",
    name="Mall 5-Mile Buffers",
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
                    color="144,238,144,128",
                    outline_color="80,160,80,255",
                    outline_width=0.5,
                )
            ],
        )
    ),
    processing_step=ProcessingStep(
        description=("Buffer mall points by 5 miles (26,400 ft) in EPSG:2227"),
        action=PythonAction(fn=buffer_malls),
        depends_on=["mall_points"],
        output=Path("output/mall_buffers.shp"),
    ),
)
