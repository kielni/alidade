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

BUFFER_METERS = 25 * 1_609.344  # 25 miles, in EPSG:3857 meters


def buffer_capitol_buildings(src: Path, output: Path) -> None:
    gdf = gpd.read_file(src)
    gdf["geometry"] = gdf.geometry.buffer(BUFFER_METERS)
    gdf.to_file(output)


capitol_buffer = Layer(
    id="capitol_buffer",
    name="State Capitol 25-Mile Buffer",
    type="vector",
    source="./output/capitol_buffer.shp",
    provider="ogr",
    crs="EPSG:3857",
    visible=True,
    geometry_type="Polygon",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            layers=[
                SimpleFill(
                    color="100,150,255,80",
                    outline_color="0,80,200,255",
                    outline_width=0.8,
                )
            ],
        )
    ),
    processing_step=ProcessingStep(
        description=(
            "Buffer each State Capitol building point by 25 miles (40,233.6 m in"
            " EPSG:3857) using geopandas."
        ),
        action=PythonAction(fn=buffer_capitol_buildings),
        depends_on=["state_capitol_bldgs"],
        output=Path("output/capitol_buffer.shp"),
    ),
)
