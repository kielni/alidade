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
from projects.goats.util import CRS

_BUFFER_M = 30.48  # 100 ft in metres (UTM units)


def create_border(layer: BoundLayer) -> None:
    """Buffer park boundary by 100 ft (30.48 m) to create clip border"""
    (boundary,) = layer.inputs
    gdf = gpd.read_file(boundary.path).to_crs(CRS)
    dissolved = gdf.dissolve()
    dissolved.geometry = dissolved.geometry.buffer(_BUFFER_M)
    dissolved.to_file(layer.path, driver="GPKG")


border = Layer(
    id="clip_border",
    name="Clip Border (100 ft buffer)",
    type="vector",
    inputs=[park_boundary],
    datasource="output/border.gpkg",
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
    action=PythonAction(fn=create_border),
)
