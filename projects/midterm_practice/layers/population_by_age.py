"""Bay Area census tracts with population-by-age attributes, projected to
EPSG:2227 (NAD83 / California zone 3, US survey feet).
Filtered to tracts with Under10 > 500 (out of 1,542 total).
Mix of Polygon and MultiPolygon geometries.

Key fields (DBF names truncated to 10 characters):
    GEOID      — 11-digit census tract FIPS code
    NAME       — e.g. "Census Tract 4402"
    County     — county name, e.g. "Alameda County"
    State      — "California" for all records
    Total Popu — total population of the tract
    RatioMakes — ratio of males to total population (truncated from "RatioMales")
    PopLessTha — population below an age threshold (truncated from "PopLessThan[Age]")
    Under10    — count of residents under 10 years old
    ALAND      — land area in square meters
    AWATER     — water area in square meters
    Shape__Are, Shape__Len, Shape_Leng, Shape_Area — ESRI geometry metadata
"""

import geopandas as gpd

from alidade.models import (
    BoundLayer,
    GraduatedRange,
    GraduatedRenderer,
    Layer,
    PythonAction,
)
from projects.midterm_practice.layers.population_by_age_raw import population_by_age_raw

# Jenks natural breaks on Under10 (n=833, tracts with Under10 > 500):
#   counts: 398, 271, 134, 28, 2
_MIN = 501.0
_B1 = 702.0
_B2 = 970.0
_B3 = 1389.0
_B4 = 2099.0
_MAX = 4891.0

# ColorBrewer Purples 5-class
_PURPLES = ["#f2f0f7", "#cbc9e2", "#9e9ac8", "#756bb1", "#54278f"]


def _filter_under10(layer: BoundLayer) -> None:
    (src,) = layer.inputs
    gdf = gpd.read_file(src.path)
    gdf[gdf["Under10"] > 500].to_file(layer.path)


population_by_age = Layer(
    id="population_by_age",
    name="Population by Age",
    type="vector",
    inputs=[population_by_age_raw],
    datasource="output/population_by_age.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=True,
    geometry_type="Polygon",
    renderer=GraduatedRenderer(
        attr="Under10",
        ranges=[
            GraduatedRange(
                lower=_MIN,
                upper=_B1,
                label=f"{_MIN:.0f} – {_B1:.0f}",
                color=_PURPLES[0],
            ),
            GraduatedRange(
                lower=_B1,
                upper=_B2,
                label=f"{_B1:.0f} – {_B2:.0f}",
                color=_PURPLES[1],
            ),
            GraduatedRange(
                lower=_B2,
                upper=_B3,
                label=f"{_B2:.0f} – {_B3:.0f}",
                color=_PURPLES[2],
            ),
            GraduatedRange(
                lower=_B3,
                upper=_B4,
                label=f"{_B3:.0f} – {_B4:.0f}",
                color=_PURPLES[3],
            ),
            GraduatedRange(
                lower=_B4,
                upper=_MAX,
                label=f"{_B4:.0f}+",
                color=_PURPLES[4],
            ),
        ],
        outline_color="#999999",
        outline_width=0.1,
    ),
    action=PythonAction(fn=_filter_under10),
)
