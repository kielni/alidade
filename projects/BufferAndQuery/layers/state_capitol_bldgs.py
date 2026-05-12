from pathlib import Path

from models import Layer

state_capitol_bldgs = Layer(
    id="state_capitol_bldgs",
    name="State Capitol Buildings",
    type="vector",
    source="../projects/BufferAndQuery/data/state_Capitol_bldgs.shp",
    provider="ogr",
    crs="EPSG:3857",
    visible=True,
    style_xml=Path("styles/state_capitol_bldgs.xml"),
)
