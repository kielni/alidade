from pathlib import Path

from alidade.models import Layer

usaparks = Layer(
    id="usaparks",
    name="Parks",
    type="vector",
    source="../projects/BufferAndQuery/data/USAParks.shp",
    provider="ogr",
    crs="EPSG:3857",
    visible=True,
    style_xml=Path("styles/usaparks.xml"),
)
