from pathlib import Path

from models import Layer

usaparks = Layer(
    id="usaparks",
    name="Parks",
    type="vector",
    source="../BufferAndQuery/data/USAParks.shp",
    provider="ogr",
    crs="EPSG:3857",
    visible=True,
    style_xml=Path("styles/usaparks.xml"),
)
