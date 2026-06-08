import geopandas as gpd

from alidade.models import (
    BoundLayer,
    Layer,
    PythonAction,
    SimpleMarker,
    SingleSymbol,
    Symbol,
)
from projects.goats.util import CRS

"""
Parking lots suitable for goat staging.
"""


def reproject_staging(layer: BoundLayer) -> None:
    """Reproject staging area points to project CRS."""
    gdf = gpd.read_file(layer.raw_path).to_crs(CRS)
    gdf.to_file(layer.path)


staging = Layer(
    id="staging_areas",
    name="Staging Areas",
    type="vector",
    raw_file="data/staging.geojson",
    source_description="Candidate goat staging area points",
    source_origin="Field-recorded",
    datasource="output/staging.shp",
    provider="ogr",
    crs=CRS,
    visible=True,
    geometry_type="Point",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="marker",
            layers=[
                SimpleMarker(
                    name="diamond",
                    color="180,0,255,255",
                    outline_color="110,0,160,255",
                    outline_width=0.4,
                    size=4.0,
                )
            ],
        )
    ),
    action=PythonAction(fn=reproject_staging),
)
