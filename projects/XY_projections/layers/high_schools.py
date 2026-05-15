from alidade.models import Layer

high_schools = Layer(
    id="high_schools",
    name="High Schools",
    type="vector",
    source=(
        "data/high_schools.csv"
        "?type=csv&xField=Longitude&yField=Latitude&crs=EPSG:4326"
    ),
    provider="delimitedtext",
    crs="EPSG:4326",
    geometry_type="Point",
    visible=True,
    style_xml=None,
)
