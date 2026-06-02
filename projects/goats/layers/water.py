from pathlib import Path

import geopandas as gpd

from alidade.models import (
    Layer,
    ProcessingStep,
    PythonAction,
    SimpleLine,
    SingleSymbol,
    Symbol,
)
from projects.goats.util import CRS


def clip_water(boundary: Path, output: Path) -> None:
    project_dir = boundary.parent.parent
    gdf = gpd.read_file(project_dir / "data" / "water.geojson").to_crs(CRS)
    mask = gpd.read_file(boundary).to_crs(CRS)
    gpd.clip(gdf, mask).to_file(output)


water = Layer(
    id="riparian",
    name="Riparian Areas",
    type="vector",
    source="./output/water.shp",
    provider="ogr",
    crs=CRS,
    visible=True,
    geometry_type="LineString",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="line",
            layers=[
                SimpleLine(
                    line_color="68,119,170,255",
                    line_width=0.6,
                )
            ],
        )
    ),
    processing_step=ProcessingStep(
        description="Reproject and clip streams to park boundary",
        action=PythonAction(fn=clip_water),
        depends_on=["park_boundary"],
        output=Path("output/water.shp"),
    ),
)
