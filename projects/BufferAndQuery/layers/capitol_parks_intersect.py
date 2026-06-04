import geopandas as gpd

from alidade.models import (
    BoundLayer,
    Layer,
    PythonAction,
    SimpleFill,
    SingleSymbol,
    Symbol,
)
from projects.BufferAndQuery.layers.capitol_buffer import capitol_buffer
from projects.BufferAndQuery.layers.national_parks import national_parks


def filter_capitol_buffers_near_parks(layer: BoundLayer) -> None:
    buffers_layer, parks_layer = layer.inputs
    buffers = gpd.read_file(buffers_layer.path)
    parks = gpd.read_file(parks_layer.path)
    joined = gpd.sjoin(
        buffers, parks[["geometry"]], how="inner", predicate="intersects"
    )
    result = buffers.loc[joined.index.unique()]
    result.to_file(layer.path)
    print(
        f"State capitols with 25-mile buffer intersecting a national park:"
        f" {len(result)}"
    )


capitol_parks_intersect = Layer(
    id="capitol_parks_intersect",
    name="Capitol Buffers Intersecting National Parks",
    type="vector",
    inputs=[capitol_buffer, national_parks],
    datasource="output/capitol_parks_intersect.shp",
    provider="ogr",
    crs="EPSG:3857",
    visible=True,
    geometry_type="Polygon",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            layers=[
                SimpleFill(
                    color="255,160,50,110",
                    outline_color="200,90,0,255",
                    outline_width=1.0,
                )
            ],
        )
    ),
    action=PythonAction(fn=filter_capitol_buffers_near_parks),
)
