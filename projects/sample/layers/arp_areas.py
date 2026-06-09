from pathlib import Path

from alidade.color import Color
from alidade.models import Layer, SimpleFill, SingleSymbol, Symbol

arp_areas = Layer(
    id="arp_areas",
    name="ARP_areas",
    type="vector",
    datasource="data/ARP_areas.geojson",
    provider="ogr",
    crs="EPSG:4326",
    visible=True,
    style_xml=Path("styles/arp_areas.xml"),
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            alpha=0.506,
            layers=[
                SimpleFill(
                    color=Color.from_hex("#987db7", alpha=0),
                    outline_color=Color.from_hex("#27202f"),
                )
            ],
        )
    ),
)
