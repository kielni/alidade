"""
Priority zone: 100 ft buffer around high human use developed area: buildings,
playgrounds, picnic areas).
"""

import geopandas as gpd

from alidade.models import (
    BoundLayer,
    Layer,
    PythonAction,
    SimpleFill,
    SingleSymbol,
    Symbol,
)
from projects.goats.layers.developed_area import developed_area
from projects.goats.layers.park_boundary import park_boundary
from projects.goats.util import BUFFER_100FT_M, CRS, clip_park


def create_priority_developed(layer: BoundLayer) -> None:
    """Buffer developed area by 100 ft and clip to park boundary."""
    boundary, developed = layer.inputs
    gdf = gpd.read_file(developed.path).to_crs(CRS)
    buffered_geom = gdf.geometry.buffer(BUFFER_100FT_M).union_all()
    buffered = gpd.GeoDataFrame(geometry=[buffered_geom], crs=CRS)
    clip_park(buffered, boundary.path).to_file(layer.path, driver="GPKG")


priority_developed = Layer(
    id="priority_developed",
    name="Priority: Developed Area Buffer",
    type="vector",
    inputs=[park_boundary, developed_area],
    datasource="output/priority_developed.gpkg",
    crs=CRS,
    geometry_type="Polygon",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            layers=[
                SimpleFill(
                    color="255,140,0,128",
                    style="solid",
                    outline_color="200,100,0,200",
                    outline_width=0.5,
                )
            ],
        )
    ),
    action=PythonAction(fn=create_priority_developed),
)
