"""Bay Area census tracts with median household income ≤ $75,000.

Filtered from med_hh_income_raw (1,618 total tracts) to tracts where
MedianHH_i <= 75000 (753 tracts).

Jenks natural breaks on MedianHH_i (n=753):
    counts: 47, 140, 179, 181, 206
"""

import geopandas as gpd

from alidade.models import (
    BoundLayer,
    GraduatedRange,
    GraduatedRenderer,
    Layer,
    PythonAction,
)
from projects.midterm.layers.med_hh_income_raw import med_hh_income_raw

_MIN = 0.0
_B1 = 27255.0
_B2 = 44309.0
_B3 = 55505.0
_B4 = 65507.0
_MAX = 75000.0

# ColorBrewer Purples 7-class shades 2–6, 65% opacity (alpha=166).
# Skips the near-white class 1 so the lowest bucket is clearly visible.
_PURPLES = [
    "218,218,235,166",
    "188,189,220,166",
    "158,154,200,166",
    "117,107,177,166",
    "84,39,143,166",
]


def _filter_income(layer: BoundLayer) -> None:
    (src,) = layer.inputs
    gdf = gpd.read_file(src.path)
    gdf[gdf["MedianHH_i"] <= 75000].to_file(layer.path)


med_hh_income = Layer(
    id="med_hh_income",
    name="Median Household Income ≤ $75,000",
    type="vector",
    inputs=[med_hh_income_raw],
    datasource="output/med_hh_income.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=True,
    geometry_type="Polygon",
    renderer=GraduatedRenderer(
        attr="MedianHH_i",
        ranges=[
            GraduatedRange(
                lower=_MIN,
                upper=_B1,
                label=f"$0 – ${_B1:,.0f}",
                color=_PURPLES[0],
            ),
            GraduatedRange(
                lower=_B1,
                upper=_B2,
                label=f"${_B1:,.0f} – ${_B2:,.0f}",
                color=_PURPLES[1],
            ),
            GraduatedRange(
                lower=_B2,
                upper=_B3,
                label=f"${_B2:,.0f} – ${_B3:,.0f}",
                color=_PURPLES[2],
            ),
            GraduatedRange(
                lower=_B3,
                upper=_B4,
                label=f"${_B3:,.0f} – ${_B4:,.0f}",
                color=_PURPLES[3],
            ),
            GraduatedRange(
                lower=_B4,
                upper=_MAX,
                label=f"${_B4:,.0f} – ${_MAX:,.0f}",
                color=_PURPLES[4],
            ),
        ],
        outline_color="128,128,128,255",
        outline_width=0.1,
    ),
    action=PythonAction(fn=_filter_income),
)
