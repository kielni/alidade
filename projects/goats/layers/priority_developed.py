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
from projects.goats.util import CRS, clip_park

BUFFER_METERS = 30.48  # 100 ft in metres

"""
Priority zone: 100 ft buffer around developed area (buildings, playgrounds, picnic
areas). High human use → high goat visibility and engagement potential.
"""


def create_priority_developed(layer: BoundLayer) -> None:
    """Buffer developed area by 100 ft and clip to park boundary."""
    boundary, developed = layer.inputs
    gdf = gpd.read_file(developed.path).to_crs(CRS)
    buffered_geom = gdf.geometry.buffer(BUFFER_METERS).union_all()
    buffered = gpd.GeoDataFrame(geometry=[buffered_geom], crs=CRS)
    clip_park(buffered, boundary.path).to_file(layer.path, driver="GPKG")


priority_developed = Layer(
    id="priority_developed",
    name="Priority: Developed Area Buffer",
    type="vector",
    inputs=[park_boundary, developed_area],
    datasource="output/priority_developed.gpkg",
    provider="ogr",
    crs=CRS,
    visible=True,
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
