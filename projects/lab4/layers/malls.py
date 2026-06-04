import csv
import time

import geopandas as gpd
from geopy.geocoders import Nominatim  # type: ignore[import-untyped]
from shapely.geometry import Point

from alidade.models import (
    BoundLayer,
    Label,
    Layer,
    PythonAction,
    SingleSymbol,
    SvgMarker,
    Symbol,
)

# output/malls.shp: 11 Bay Area shopping mall points, EPSG:2227.
# Fields: id (str), Street (street address), mall_name (str), city (str).
# Extent: x=5,990,284–6,175,052 ft  y=1,932,559–2,189,415 ft.


def geocode_malls(layer: BoundLayer) -> None:
    geocoder = Nominatim(user_agent="alidade-lab4-geocode")
    rows = []
    with open(layer.raw_path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            address = (
                f"{row['Street'].strip()}, {row['City'].strip()}, "
                f"{row['State'].strip()} {row['Zip'].strip()}"
            )
            result = geocoder.geocode(address, country_codes="us")
            rows.append(
                {
                    "id": row["ID"].strip(),
                    "Street": row["Street"].strip(),
                    "mall_name": row["MallName"].strip(),
                    "city": row["City"].strip(),
                    "geometry": (
                        Point(result.longitude, result.latitude) if result else None
                    ),
                }
            )
            time.sleep(1.1)  # Nominatim rate limit: 1 request/second

    gdf = gpd.GeoDataFrame(rows, crs="EPSG:4326")
    gdf = gdf[gdf.geometry.notna()].to_crs("EPSG:2227")
    gdf.to_file(layer.path)


malls = Layer(
    id="mall_points",
    name="Big Bucks Malls",
    type="vector",
    raw_file="data/mall_names.csv",
    datasource="output/malls.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=True,
    geometry_type="Point",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="marker",
            layers=[
                SvgMarker(
                    name="data/mall.svg",
                    color="230,120,0,255",
                    outline_color="160,84,0,255",
                    outline_width=0.0,
                    size=5.0,
                )
            ],
        )
    ),
    label=Label(field="mall_name"),
    action=PythonAction(fn=geocode_malls),
)
