from pathlib import Path

from alidade.models import Layer

carto_test_3 = Layer(
    id="Carto_test_3_9e1d3db0_0fb6_449e_bbd7_427885fc5755",
    name="Carto test 3",
    type="raster",
    source=(
        "type=xyz&url=https://basemaps.cartocdn.com/light_all/%7Bz%7D/%7Bx%7D/%7By%7D.p"
        "ng&zmax=18&zmin=0"
    ),
    provider="wms",
    crs="EPSG:3857",
    visible=True,
    style_xml=Path("styles/carto_test_3.xml"),
)
