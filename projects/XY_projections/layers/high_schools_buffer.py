import geopandas as gpd

from alidade.models import (
    BoundLayer,
    Layer,
    PythonAction,
    SimpleFill,
    SingleSymbol,
    Symbol,
)
from projects.XY_projections.layers.high_schools_2227 import high_schools_2227


def _buffer(layer: BoundLayer) -> None:
    (src,) = layer.inputs
    gdf = gpd.read_file(src.path)
    gdf.geometry = gdf.geometry.buffer(5280)
    gdf.to_file(layer.path)


high_schools_buffer = Layer(
    id="high_schools_buffer",
    name="High Schools Buffer",
    type="vector",
    inputs=[high_schools_2227],
    datasource="data/high_schools_buffer.shp|layername=high_schools_buffer",
    provider="ogr",
    crs="EPSG:2227",
    geometry_type="Polygon",
    visible=True,
    style_xml=None,
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            alpha=0.5,
            layers=[SimpleFill(color="64,128,255,255")],
        )
    ),
    action=PythonAction(fn=_buffer),
)
