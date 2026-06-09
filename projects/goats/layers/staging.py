"""
Large flat areas suitable for goat staging.
"""

import geopandas as gpd

from alidade.models import (
    BoundLayer,
    Layer,
    PythonAction,
    SimpleMarker,
    SingleSymbol,
    Symbol,
)
from projects.goats.palette import STAGING_EDGE, STAGING_FILL
from projects.goats.util import CRS


def reproject_staging(layer: BoundLayer) -> None:
    """Reproject staging area points to project CRS."""
    gdf = gpd.read_file(layer.raw_path).to_crs(CRS)
    gdf.to_file(layer.path, driver="GPKG")


staging = Layer(
    id="staging_areas",
    name="Staging Areas",
    type="vector",
    raw_file="data/staging.geojson",
    source_description="Candidate goat staging area points",
    source_origin="Field-recorded",
    datasource="output/staging.gpkg",
    crs=CRS,
    geometry_type="Point",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="marker",
            layers=[
                SimpleMarker(
                    name="diamond",
                    color=STAGING_FILL,
                    outline_color=STAGING_EDGE,
                    outline_width=0.4,
                    size=4.0,
                )
            ],
        )
    ),
    action=PythonAction(fn=reproject_staging),
)
