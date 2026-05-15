from alidade.models import Layer

openstreetmap = Layer(
    id="openstreetmap",
    name="OpenStreetMap",
    type="raster",
    source=(
        "http-header:referer=&type=xyz"
        "&url=https://tile.openstreetmap.org/%7Bz%7D/%7Bx%7D/%7By%7D.png"
        "&zmax=19&zmin=0"
    ),
    provider="wms",
    crs="EPSG:3857",
    visible=True,
)
