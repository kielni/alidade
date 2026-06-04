"""Bay Area zoo point locations, reprojected from EPSG:4326 to EPSG:2227.

Source: zoo.txt — three Bay Area zoo locations geocoded via Bing Maps.

zoo.txt columns:
    latitude, longitude — WGS 84 coordinates
    name    — street address used for geocoding
    desc    — display address
    color   — zoo name (e.g. "Oakland Zoo", "San Francisco Zoo", "Happy Hollow Zoo")
    source  — geocoder used ("Bing Maps")
    precision — geocode match type ("address" or "intersection")
"""

import geopandas as gpd
import pandas as pd

from alidade.models import (
    BoundLayer,
    Layer,
    PythonAction,
    SingleSymbol,
    SvgMarker,
    Symbol,
)
from projects.midterm_practice.layers.bay_area_zoos_raw import bay_area_zoos_raw


def _reproject(layer: BoundLayer) -> None:
    (src,) = layer.inputs
    df = pd.read_csv(src.path)
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326",
    )
    gdf.to_crs("EPSG:2227").to_file(layer.path)


bay_area_zoos = Layer(
    id="bay_area_zoos",
    name="Bay Area Zoos",
    type="vector",
    inputs=[bay_area_zoos_raw],
    datasource="output/bay_area_zoos.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=True,
    geometry_type="Point",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="marker",
            layers=[
                SvgMarker(
                    name="tourist/tourist_zoo.svg",
                    color="0,0,0,255",
                    outline_color="0,0,0,255",
                    outline_width=0.2,
                    size=10.0,
                )
            ],
        )
    ),
    action=PythonAction(fn=_reproject),
)
