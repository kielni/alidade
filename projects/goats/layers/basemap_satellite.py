from pathlib import Path

from alidade.models import Layer

basemap_satellite = Layer(
    id="esri_satellite",
    name="ESRI World Imagery",
    type="raster",
    datasource=(
        "http-header:referer=&type=xyz&url=https://server.arcgisonline.com/ArcGIS/rest/"
        "services/World_Imagery/MapServer/tile/%7Bz%7D/%7By%7D/%7Bx%7D&zmax=18&zmin=0"
    ),
    provider="wms",
    crs="EPSG:3857",
    visible=True,
    style_xml=Path("styles/esri_satellite.xml"),
)
