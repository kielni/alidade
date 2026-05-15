from pathlib import Path

from alidade.models import Layer

libraries = Layer(
    id="Libraries_53815974_27c8_4c61_ac6e_25a82f907635",
    name="Libraries",
    type="vector",
    source="../projects/XY_projections/project_data/Libraries.shp|layername=Libraries",
    provider="ogr",
    crs="EPSG:2227",
    visible=True,
    style_xml=Path("styles/libraries.xml"),
)
