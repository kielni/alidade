"""Census tracts with median household income ≤ $75,000 that intersect the
5-mile UC/CSU campus buffer zone.

Derived from med_hh_income (753 tracts) filtered to those whose geometry
intersects any polygon in uc_and_csu_buffer. Duplicates are dropped so each
tract appears at most once even if it overlaps multiple campus buffers.

ColorBrewer Purples (7-class shades 2–6) so the lowest bucket is clearly
distinguishable from white, 50% opacity.
"""

import geopandas as gpd

from alidade.models import (
    BoundLayer,
    GraduatedRange,
    GraduatedRenderer,
    Layer,
    PythonAction,
)
from projects.midterm.layers.med_hh_income import med_hh_income
from projects.midterm.layers.uc_and_csu_buffer import uc_and_csu_buffer

_MIN = 0.0
_B1 = 27255.0
_B2 = 44309.0
_B3 = 55505.0
_B4 = 65507.0
_MAX = 75000.0

# ColorBrewer Purples 7-class shades 2–6, 50% opacity (alpha=128).
# Skips the near-white class 1 so the lowest bucket is clearly visible.
_PURPLES = [
    "218,218,235,128",
    "188,189,220,128",
    "158,154,200,128",
    "117,107,177,128",
    "84,39,143,128",
]


def _filter_in_buffer(layer: BoundLayer) -> None:
    income_layer, buffer_layer = layer.inputs
    income = gpd.read_file(income_layer.path)
    buffer = gpd.read_file(buffer_layer.path)
    joined = gpd.sjoin(income, buffer, how="inner", predicate="intersects")
    joined = joined[~joined.index.duplicated(keep="first")]
    joined[income.columns].to_file(layer.path)


med_hh_income_in_buffer = Layer(
    id="med_hh_income_in_buffer",
    name="Low-Income Tracts in Campus Buffer",
    type="vector",
    inputs=[med_hh_income, uc_and_csu_buffer],
    datasource="output/med_hh_income_in_buffer.shp",
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
    action=PythonAction(fn=_filter_in_buffer),
)
