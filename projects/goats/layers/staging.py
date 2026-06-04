import geopandas as gpd

from alidade.models import (
    BoundLayer,
    Layer,
    PythonAction,
    SingleSymbol,
    SvgMarker,
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
    datasource="output/staging.shp",
    provider="ogr",
    crs=CRS,
    visible=True,
    geometry_type="Point",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="marker",
            layers=[
                SvgMarker(
                    name="data/goat.svg",
                    color="255,220,0,255",
                    size=6.0,
                )
            ],
        )
    ),
    action=PythonAction(fn=reproject_staging),
)
