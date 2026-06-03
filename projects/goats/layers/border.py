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
from projects.goats.util import CRS

_BUFFER_M = 30.48  # 100 ft in metres (UTM units)


def create_border(boundary: Path, output: Path) -> None:
    """Buffer the park boundary by 100 ft to produce a clip mask.

    Roads run along the park perimeter; the 100 ft buffer ensures that
    roadside areas are included when clipping feature layers to the park.
    """
    gdf = gpd.read_file(boundary).to_crs(CRS)
    dissolved = gdf.dissolve()
    dissolved.geometry = dissolved.geometry.buffer(_BUFFER_M)
    dissolved.to_file(output, driver="GPKG")


border = Layer(
    id="clip_border",
    name="Clip Border (100 ft buffer)",
    type="vector",
    source="./output/border.gpkg",
    provider="ogr",
    crs=CRS,
    visible=False,
    geometry_type="Polygon",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            layers=[
                SimpleFill(
                    color="0,0,0,0",
                    style="no",
                    outline_color="100,100,200,180",
                    outline_width=0.5,
                )
            ],
        )
    ),
    processing_step=ProcessingStep(
        description="Buffer park boundary by 100 ft (30.48 m) to create clip border",
        action=PythonAction(fn=create_border),
        depends_on=["park_boundary"],
        output=Path("output/border.gpkg"),
    ),
)
