"""
Strava .gpx from walk around developed area (buildings, playgrounds, picnic areas,
etc).

Use this to identify priority "high human use" areas
"""

from typing import cast

import geopandas as gpd
from shapely.geometry import MultiLineString, Polygon
from shapely.ops import linemerge

from alidade.models import (
    BoundLayer,
    Layer,
    PythonAction,
    SimpleFill,
    SingleSymbol,
    Symbol,
)
from projects.goats.palette import DEVELOPED_EDGE, DEVELOPED_FILL
from projects.goats.util import CRS

SIMPLIFY_TOLERANCE_M = 10


def convert_developed_area(layer: BoundLayer) -> None:
    """Convert GPX to .gpkg for developed area layer.

    Simplify GPX track (10 m tolerance), close ring, convert to polygon,
    reproject to EPSG:26910.
    """
    gdf = gpd.read_file(layer.raw_path, layer="tracks").to_crs(CRS)
    line = linemerge(cast(MultiLineString, gdf.geometry.iloc[0]))
    simplified = line.simplify(SIMPLIFY_TOLERANCE_M, preserve_topology=True)
    poly = Polygon(list(simplified.coords))
    result = gpd.GeoDataFrame(
        gdf[["name"]].iloc[:1].reset_index(drop=True),
        geometry=[poly],
        crs=CRS,
    )
    result.to_file(layer.path, driver="GeoJSON")


developed_area = Layer(
    id="developed_area",
    name="Developed Area",
    type="vector",
    raw_file="data/Alum_Rock_developed_area.gpx",
    source_description="GPS tracks of developed area perimeter",
    source_origin="Strava walk",
    datasource="output/developed_area.geojson",
    crs=CRS,
    geometry_type="Polygon",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            layers=[
                SimpleFill(
                    color=DEVELOPED_FILL,
                    outline_color=DEVELOPED_EDGE,
                    outline_width=1.0,
                )
            ],
        )
    ),
    action=PythonAction(fn=convert_developed_area),
)
