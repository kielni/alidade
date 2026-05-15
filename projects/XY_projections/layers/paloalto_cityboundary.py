from pathlib import Path

from alidade.models import Layer

paloalto_cityboundary = Layer(
    id="PaloAlto_cityboundary_95ec1801_58ca_483b_90a0_f170e1a6caa4",
    name="PaloAlto_cityboundary",
    type="vector",
    source=(
        "../projects/XY_projections/project_data/PaloAlto_cityboundary.shp|layername=Pa"
        "loAlto_cityboundary"
    ),
    provider="ogr",
    crs="EPSG:2227",
    visible=True,
    style_xml=Path("styles/paloalto_cityboundary.xml"),
)
