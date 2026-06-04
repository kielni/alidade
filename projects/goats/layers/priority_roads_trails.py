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
from projects.goats.layers.roads_trails import roads_trails
from projects.goats.util import CRS, clip_park

BUFFER_METERS = 9.144  # 30 ft in metres

"""
Priority zone: 30 ft buffer along roads and trails.
High human foot traffic → high goat visibility and engagement potential.
"""


def create_priority_roads_trails(layer: BoundLayer) -> None:
    """Buffer roads and trails by 30 ft and clip to park boundary."""
    boundary, roads_trails = layer.inputs
    gdf = gpd.read_file(roads_trails.path).to_crs(CRS)
    buffered_geom = gdf.geometry.buffer(BUFFER_METERS).union_all()
    buffered = gpd.GeoDataFrame(geometry=[buffered_geom], crs=CRS)
    clip_park(buffered, boundary.path).to_file(layer.path, driver="GPKG")


priority_roads_trails = Layer(
    id="priority_roads_trails",
    name="Priority: Roads & Trails Buffer",
    type="vector",
    inputs=[park_boundary, roads_trails],
    datasource="output/priority_roads_trails.gpkg",
    provider="ogr",
    crs=CRS,
    visible=True,
    geometry_type="Polygon",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            layers=[
                SimpleFill(
                    color="255,200,0,128",
                    style="solid",
                    outline_color="180,140,0,200",
                    outline_width=0.5,
                )
            ],
        )
    ),
    action=PythonAction(fn=create_priority_roads_trails),
)
