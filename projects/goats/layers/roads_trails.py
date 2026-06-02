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


def clip_roads_trails(boundary: Path, output: Path) -> None:
    project_dir = boundary.parent.parent
    gdf = gpd.read_file(project_dir / "data" / "roads_trails.geojson")
    gdf = gdf[gdf.geom_type.isin(["LineString", "MultiLineString"])].copy()
    gdf = gdf.to_crs(CRS)
    mask = gpd.read_file(boundary).to_crs(CRS)
    gpd.clip(gdf, mask).to_file(output)


roads_trails = Layer(
    id="roads_trails",
    name="Roads & Trails",
    type="vector",
    source="./output/roads_trails.shp",
    provider="ogr",
    crs=CRS,
    visible=True,
    geometry_type="LineString",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="line",
            layers=[
                SimpleLine(
                    line_color="120,80,40,255",
                    line_width=0.5,
                )
            ],
        )
    ),
    processing_step=ProcessingStep(
        description="Reproject and clip roads and trails to park boundary",
        action=PythonAction(fn=clip_roads_trails),
        depends_on=["park_boundary"],
        output=Path("output/roads_trails.shp"),
    ),
)
