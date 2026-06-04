"""5-mile buffer polygons around each UC and CSU campus point.

EPSG:2227 uses US survey feet; 5 miles = 26,400 feet.
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
from projects.midterm.layers.uc_and_csu import uc_and_csu

_BUFFER_FT = 26400  # 5 miles in US survey feet


def _buffer(layer: BoundLayer) -> None:
    (src,) = layer.inputs
    gdf = gpd.read_file(src.path)
    gdf.geometry = gdf.geometry.buffer(_BUFFER_FT)
    gdf.to_file(layer.path)


uc_and_csu_buffer = Layer(
    id="uc_and_csu_buffer",
    name="UC and CSU 5-Mile Buffer",
    type="vector",
    inputs=[uc_and_csu],
    datasource="output/uc_and_csu_buffer.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=True,
    geometry_type="Polygon",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            layers=[
                SimpleFill(
                    color="0,128,0,10",
                    outline_color="0,100,0,255",
                    outline_width=0.8,
                )
            ],
        )
    ),
    action=PythonAction(fn=_buffer),
)
