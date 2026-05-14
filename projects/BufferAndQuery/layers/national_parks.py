from pathlib import Path

import geopandas as gpd

from models import Layer, ProcessingStep, PythonAction, SimpleFill, SingleSymbol, Symbol


def filter_national_park_service(src: Path, output: Path) -> None:
    gdf = gpd.read_file(src)
    gdf[gdf["FCC"] == "D83"].to_file(output)


national_parks = Layer(
    id="national_parks",
    name="National Parks",
    type="vector",
    source="./output/national_parks.shp",
    provider="ogr",
    crs="EPSG:3857",
    visible=True,
    geometry_type="Polygon",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            layers=[
                SimpleFill(
                    color="120,200,100,128",
                    outline_color="0,100,0,255",
                )
            ],
        )
    ),
    processing_step=ProcessingStep(
        description=(
            "Filter USAParks to FCC='D83' (National Park Service units:"
            " national parks, monuments, historic parks, seashores, etc.)."
        ),
        action=PythonAction(fn=filter_national_park_service),
        depends_on=["usaparks"],
        output=Path("output/national_parks.shp"),
    ),
)
