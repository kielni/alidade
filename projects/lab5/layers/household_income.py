"""Household income filtered to MedianHH_i > 0, graduated on MedianHH_i.

Source: output/household_income.shp
(generated from household_income_raw by filter step).
ColorBrewer RdBu reversed (blue → cream → red = low → high income).
Jenks natural breaks on MedianHH_i (n=1610):
  counts: 399, 520, 382, 231, 78
"""

import geopandas as gpd

from alidade.models import (
    BoundLayer,
    GraduatedRange,
    GraduatedRenderer,
    Layer,
    PythonAction,
)
from projects.lab5.layers.household_income_raw import household_income_raw
from projects.lab5.util import RDBU_R, RDBU_R_OUTLINE

_MIN = 0.0
_B1 = 57652.0
_B2 = 84875.0
_B3 = 113042.0
_B4 = 149750.0
_MAX = 233917.0


def filter_nonzero_income(layer: BoundLayer) -> None:
    (src,) = layer.inputs
    gdf = gpd.read_file(src.path)
    gdf[gdf["MedianHH_i"] > 0].to_file(layer.path)


household_income = Layer(
    id="household_income",
    name="Household Income",
    type="vector",
    inputs=[household_income_raw],
    datasource="output/household_income.shp",
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
                label=f"{_MIN:,.0f} - {_B1:,.0f}",
                color=RDBU_R[0],
            ),
            GraduatedRange(
                lower=_B1,
                upper=_B2,
                label=f"{_B1:,.0f} - {_B2:,.0f}",
                color=RDBU_R[1],
            ),
            GraduatedRange(
                lower=_B2,
                upper=_B3,
                label=f"{_B2:,.0f} - {_B3:,.0f}",
                color=RDBU_R[2],
            ),
            GraduatedRange(
                lower=_B3,
                upper=_B4,
                label=f"{_B3:,.0f} - {_B4:,.0f}",
                color=RDBU_R[3],
            ),
            GraduatedRange(
                lower=_B4,
                upper=_MAX,
                label=f"{_B4:,.0f}+",
                color=RDBU_R[4],
            ),
        ],
        outline_color=RDBU_R_OUTLINE,
        outline_width=0.1,
    ),
    action=PythonAction(fn=filter_nonzero_income),
)
