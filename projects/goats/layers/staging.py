from pathlib import Path

import geopandas as gpd

from alidade.models import (
    Layer,
    ProcessingStep,
    PythonAction,
    SingleSymbol,
    SvgMarker,
    Symbol,
)
from projects.goats.util import CRS


def reproject_staging(output: Path) -> None:
    project_dir = output.parent.parent
    gdf = gpd.read_file(project_dir / "data" / "staging.geojson").to_crs(CRS)
    gdf.to_file(output)


staging = Layer(
    id="staging_areas",
    name="Staging Areas",
    type="vector",
    source="./output/staging.shp",
    provider="ogr",
    crs=CRS,
    visible=True,
    geometry_type="Point",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="marker",
            layers=[
                SvgMarker(
                    name="data/goat.svg",
                    color="255,220,0,255",
                    size=6.0,
                )
            ],
        )
    ),
    processing_step=ProcessingStep(
        description="Reproject staging area points to EPSG:26910",
        action=PythonAction(fn=reproject_staging),
        depends_on=[],
        output=Path("output/staging.shp"),
    ),
)
