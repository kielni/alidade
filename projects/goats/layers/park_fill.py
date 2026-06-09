from alidade.models import Layer, SimpleFill, SingleSymbol, Symbol
from projects.goats.util import CRS_WGS84

"""
Solid white polygon clipped to park. Use between basemap and layers that only cover
part of the area, to hide distracting basemap decorations.
"""
park_fill = Layer(
    id="park_solid_fill",
    name="Park Fill",
    type="vector",
    datasource="data/park_boundary.geojson",
    crs=CRS_WGS84,
    geometry_type="Polygon",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            layers=[
                SimpleFill(
                    color="255,255,255,255",
                    style="solid",
                    outline_color="0,0,0,0",
                    outline_width=0,
                )
            ],
        )
    ),
)
