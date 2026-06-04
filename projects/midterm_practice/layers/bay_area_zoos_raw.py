"""Raw zoo locations from zoo.txt.

Used only as a dependency source for bay_area_zoos so the build system can
pass the CSV path to _reproject. Not displayed directly.
"""

from alidade.models import Layer

bay_area_zoos_raw = Layer(
    id="bay_area_zoos_raw",
    name="Bay Area Zoos (raw)",
    type="vector",
    datasource=(
        "data/zoo.txt" "?type=csv&xField=longitude&yField=latitude&crs=EPSG:4326"
    ),
    provider="delimitedtext",
    crs="EPSG:4326",
    geometry_type="Point",
    visible=False,
    style_xml=None,
)
