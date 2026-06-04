"""CartoDB Positron XYZ tile basemap (EPSG:3857)."""

from alidade.models import Layer

basemap = Layer(
    id="cartodb_positron",
    name="Basemap",
    type="raster",
    datasource=(
        "type=xyz&url=https://basemaps.cartocdn.com/light_all/"
        "%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=19&zmin=0"
    ),
    provider="wms",
    crs="EPSG:3857",
    visible=True,
    style_xml=None,
)
