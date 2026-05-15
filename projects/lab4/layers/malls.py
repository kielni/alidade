import csv
import time
from pathlib import Path

import geopandas as gpd
from geopy.geocoders import Nominatim  # type: ignore[import-untyped]
from shapely.geometry import Point

from alidade import project_data_dir
from alidade.models import (
    Layer,
    ProcessingStep,
    PythonAction,
    SimpleMarker,
    SingleSymbol,
    Symbol,
)

# output/malls.shp: 11 Bay Area shopping mall points, EPSG:2227.
# Fields: id (str), name (street address), city (str).
# Extent: x=5,990,284–6,175,052 ft  y=1,932,559–2,189,415 ft.
_CSV = project_data_dir(__file__) / "malls.csv"


def geocode_malls(output: Path) -> None:
    geocoder = Nominatim(user_agent="alidade-lab4-geocode")
    rows = []
    with open(_CSV, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            address = (
                f"{row['Street'].strip()}, {row['City'].strip()}, "
                f"{row['State'].strip()} {row['Zip'].strip()}"
            )
            result = geocoder.geocode(address, country_codes="us")
            rows.append(
                {
                    "id": row["ID"].strip(),
                    "name": row["Street"].strip(),
                    "city": row["City"].strip(),
                    "geometry": (
                        Point(result.longitude, result.latitude) if result else None
                    ),
                }
            )
            time.sleep(1.1)  # Nominatim rate limit: 1 request/second

    gdf = gpd.GeoDataFrame(rows, crs="EPSG:4326")
    gdf = gdf[gdf.geometry.notna()].to_crs("EPSG:2227")
    gdf.to_file(output)


malls = Layer(
    id="malls",
    name="Shopping Malls",
    type="vector",
    source="./output/malls.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=True,
    geometry_type="Point",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="marker",
            layers=[
                SimpleMarker(
                    color="220,50,50,255",
                    size=4.0,
                    outline_color="140,20,20,255",
                    outline_width=0.5,
                )
            ],
        )
    ),
    processing_step=ProcessingStep(
        description=(
            "Geocode malls.csv addresses with Nominatim; reproject to EPSG:2227."
        ),
        action=PythonAction(fn=geocode_malls),
        depends_on=[],
        output=Path("output/malls.shp"),
    ),
)
