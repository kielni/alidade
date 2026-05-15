from pathlib import Path

from alidade.models import Layer

osm_gray_scale = Layer(
    id="OSM_gray_scale_ab6c302d_fee9_4a8e_8d7b_119b3b3cd5ef",
    name="OSM gray scale",
    type="raster",
    source=(
        "crs=EPSG:3857&format&type=xyz&url=https://tiles.wmflabs.org/bw-mapnik/%7Bz%7D/"
        "%7Bx%7D/%7By%7D.png&zmax=18&zmin=0"
    ),
    provider="wms",
    crs="EPSG:3857",
    visible=True,
    style_xml=Path("styles/osm_gray_scale.xml"),
)
