from pathlib import Path

from alidade.color import Color
from alidade.models import Layer, SimpleFill, SingleSymbol, Symbol

park_polygon = Layer(
    id="park_polygon",
    name="park_polygon",
    type="vector",
    datasource="data/park_polygon.geojson",
    provider="ogr",
    crs="EPSG:4326",
    visible=True,
    style_xml=Path("styles/park_polygon.xml"),
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            layers=[
                SimpleFill(
                    color=Color.from_hex("#7d11c4", alpha=0),
                    outline_color=Color.from_hex("#7009d1"),
                    outline_width=1.0,
                )
            ],
        )
    ),
)
