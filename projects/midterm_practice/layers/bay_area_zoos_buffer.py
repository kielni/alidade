"""10-mile buffer polygons around each Bay Area zoo point.

EPSG:2227 uses US survey feet; 10 miles = 52,800 feet.
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
from projects.midterm_practice.layers.bay_area_zoos import bay_area_zoos

_BUFFER_FT = 52800  # 10 miles in US survey feet


def _buffer(layer: BoundLayer) -> None:
    (src,) = layer.inputs
    gdf = gpd.read_file(src.path)
    gdf.geometry = gdf.geometry.buffer(_BUFFER_FT)
    gdf.to_file(layer.path)


bay_area_zoos_buffer = Layer(
    id="bay_area_zoos_buffer",
    name="Bay Area Zoos Buffer",
    type="vector",
    inputs=[bay_area_zoos],
    datasource="output/bay_area_zoos_buffer.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=True,
    geometry_type="Polygon",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            alpha=0.1,
            layers=[SimpleFill(color="0,0,0,255")],
        )
    ),
    action=PythonAction(fn=_buffer),
)
