import geopandas as gpd

from alidade.models import (
    BoundLayer,
    Layer,
    PythonAction,
    SimpleFill,
    SingleSymbol,
    Symbol,
)
from projects.BufferAndQuery.layers.state_capitol_bldgs import state_capitol_bldgs

BUFFER_METERS = 25 * 1_609.344  # 25 miles, in EPSG:3857 meters


def buffer_capitol_buildings(layer: BoundLayer) -> None:
    (src,) = layer.inputs
    gdf = gpd.read_file(src.path)
    gdf["geometry"] = gdf.geometry.buffer(BUFFER_METERS)
    gdf.to_file(layer.path)


capitol_buffer = Layer(
    id="capitol_buffer",
    name="State Capitol 25-Mile Buffer",
    type="vector",
    inputs=[state_capitol_bldgs],
    datasource="output/capitol_buffer.shp",
    provider="ogr",
    crs="EPSG:3857",
    visible=True,
    geometry_type="Polygon",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            layers=[
                SimpleFill(
                    color="100,150,255,80",
                    outline_color="0,80,200,255",
                    outline_width=0.8,
                )
            ],
        )
    ),
    action=PythonAction(fn=buffer_capitol_buildings),
)
