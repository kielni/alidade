from pathlib import Path

from alidade.color import Color
from alidade.models import Layer, SimpleFill, SingleSymbol, Symbol

park_features_symbol_polygons = Layer(
    id="park_features_symbol_polygons",
    name="park_features_symbol",
    type="vector",
    datasource="data/park_features_symbol.geojson|geometrytype=Polygon",
    provider="ogr",
    crs="EPSG:4326",
    visible=True,
    style_xml=Path("styles/park_features_symbol_polygons.xml"),
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            layers=[
                SimpleFill(
                    color=Color.from_hex("#727676"),
                    outline_color=Color.from_hex("#232323"),
                    outline_width=0.26,
                )
            ],
        )
    ),
)
