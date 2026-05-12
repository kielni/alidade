from pathlib import Path

from helpers import filter_national_parks
from models import Layer, ProcessingStep, PythonAction

national_parks = Layer(
    id="national_parks",
    name="National Parks",
    type="vector",
    source="./output/national_parks.shp",
    provider="ogr",
    crs="EPSG:3857",
    visible=True,
    geometry_type="Polygon",
    processing_step=ProcessingStep(
        description=(
            "Filter USAParks to FCC='D83' (National Park Service units:"
            " national parks, monuments, historic parks, seashores, etc.)."
        ),
        action=PythonAction(fn=filter_national_parks),
        depends_on=["usaparks"],
        output=Path("output/national_parks.shp"),
    ),
)
