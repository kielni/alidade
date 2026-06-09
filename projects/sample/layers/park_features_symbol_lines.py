from pathlib import Path

from alidade.color import Color
from alidade.models import Layer, SimpleLine, SingleSymbol, Symbol

park_features_symbol_lines = Layer(
    id="park_features_symbol_lines",
    name="park_features_symbol",
    type="vector",
    datasource="data/park_features_symbol.geojson|geometrytype=LineString",
    provider="ogr",
    crs="EPSG:4326",
    visible=True,
    style_xml=Path("styles/park_features_symbol_lines.xml"),
    renderer=SingleSymbol(
        symbol=Symbol(
            type="line",
            layers=[
                SimpleLine(
                    line_color=Color.from_hex("#0d259b"),
                    line_width=0.75,
                )
            ],
        )
    ),
)
