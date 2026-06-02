from pathlib import Path
from typing import cast

import geopandas as gpd
from shapely.geometry import MultiLineString, Polygon
from shapely.ops import linemerge

from alidade.models import (
    Layer,
    ProcessingStep,
    PythonAction,
    SimpleFill,
    SingleSymbol,
    Symbol,
)
from projects.goats.util import CRS

_SIMPLIFY_TOLERANCE_M = 10

"""
Strava .gpx from walk around developed area (buildings, playgrounds, picnic areas,
etc).

Use this to identify priority "high human use" areas
"""


def convert_developed_area(output: Path) -> None:
    project_dir = output.parent.parent
    src = project_dir / "data" / "Alum_Rock_developed_area.gpx"
    gdf = gpd.read_file(src, layer="tracks").to_crs(CRS)
    line = linemerge(cast(MultiLineString, gdf.geometry.iloc[0]))
    simplified = line.simplify(_SIMPLIFY_TOLERANCE_M, preserve_topology=True)
    poly = Polygon(list(simplified.coords))
    result = gpd.GeoDataFrame(
        gdf[["name"]].iloc[:1].reset_index(drop=True),
        geometry=[poly],
        crs=CRS,
    )
    result.to_file(output)


developed_area = Layer(
    id="developed_area",
    name="Developed Area",
    type="vector",
    source="./output/developed_area.shp",
    provider="ogr",
    crs=CRS,
    visible=True,
    geometry_type="Polygon",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            layers=[
                SimpleFill(
                    color="200,200,200,128",
                    outline_color="128,128,128,255",
                    outline_width=1.0,
                )
            ],
        )
    ),
    processing_step=ProcessingStep(
        description=(
            "Simplify GPX track (10 m tolerance), close ring, convert to"
            " polygon, reproject to EPSG:26910"
        ),
        action=PythonAction(fn=convert_developed_area),
        depends_on=[],
        output=Path("output/developed_area.shp"),
    ),
)
