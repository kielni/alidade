"""
Create 100 ft buffer around streams and riparian waterways.
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
from projects.goats.layers.park_boundary import park_boundary
from projects.goats.layers.water import water
from projects.goats.palette import WATER_EDGE, WATER_FILL_SEMI
from projects.goats.util import BUFFER_100FT_M, CRS, clip_park


def create_exclude_water_vegetation(layer: BoundLayer) -> None:
    """Buffer streams by 100 ft and clip to park boundary."""
    boundary, source = layer.inputs
    gdf = gpd.read_file(source.path).to_crs(CRS)
    buffered_geom = gdf.geometry.buffer(BUFFER_100FT_M).union_all()
    buffered = gpd.GeoDataFrame(geometry=[buffered_geom], crs=CRS)
    clip_park(buffered, boundary.path).to_file(layer.path, driver="GPKG")


exclude_water_vegetation = Layer(
    id="exclude_water_vegetation",
    name="Exclusion: Riparian Buffer",
    type="vector",
    inputs=[park_boundary, water],
    datasource="output/exclude_water_vegetation.gpkg",
    crs=CRS,
    geometry_type="Polygon",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            layers=[
                SimpleFill(
                    color=WATER_FILL_SEMI,
                    style="solid",
                    outline_color=WATER_EDGE,
                    outline_width=0.0,
                )
            ],
        )
    ),
    action=PythonAction(fn=create_exclude_water_vegetation),
)
