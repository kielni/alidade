import geopandas as gpd

from alidade.models import (
    BoundLayer,
    Layer,
    PythonAction,
    SimpleFill,
    SingleSymbol,
    Symbol,
)
from projects.BufferAndQuery.layers.usaparks import usaparks


def filter_national_park_service(layer: BoundLayer) -> None:
    (src,) = layer.inputs
    gdf = gpd.read_file(src.path)
    gdf[gdf["FCC"] == "D83"].to_file(layer.path)


national_parks = Layer(
    id="national_parks",
    name="National Parks",
    type="vector",
    inputs=[usaparks],
    datasource="output/national_parks.shp",
    provider="ogr",
    crs="EPSG:3857",
    visible=True,
    geometry_type="Polygon",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            layers=[
                SimpleFill(
                    color="120,200,100,128",
                    outline_color="0,100,0,255",
                )
            ],
        )
    ),
    action=PythonAction(fn=filter_national_park_service),
)
