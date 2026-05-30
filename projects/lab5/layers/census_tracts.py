"""Census tracts filtered to Total > 0, graduated on M22_39 count.

Source: output/census_tracts.shp (generated from census_tracts_raw by filter step).
Jenks natural breaks on M22_39 (n=1617):
  counts: 560, 596, 364, 90, 7
"""

from pathlib import Path

import geopandas as gpd

from alidade.models import (
    GraduatedRange,
    GraduatedRenderer,
    Layer,
    ProcessingStep,
    PythonAction,
)
from projects.lab5.util import PURPLES, PURPLES_OUTLINE

_MIN = 0.0
_B1 = 425.0
_B2 = 742.0
_B3 = 1167.0
_B4 = 2003.0
_MAX = 2973.0


def filter_nonzero_population(src: Path, output: Path) -> None:
    gdf = gpd.read_file(src)
    gdf[gdf["Total"] > 0].to_file(output)


census_tracts = Layer(
    id="census_tracts",
    name="Males 22-39 Years",
    type="vector",
    source="./output/census_tracts.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=True,
    geometry_type="Polygon",
    renderer=GraduatedRenderer(
        attr="M22_39",
        ranges=[
            GraduatedRange(
                lower=_MIN,
                upper=_B1,
                label=f"{_MIN:.0f} - {_B1:.0f}",
                color=PURPLES[0],
            ),
            GraduatedRange(
                lower=_B1,
                upper=_B2,
                label=f"{_B1:.0f} - {_B2:.0f}",
                color=PURPLES[1],
            ),
            GraduatedRange(
                lower=_B2,
                upper=_B3,
                label=f"{_B2:.0f} - {_B3:.0f}",
                color=PURPLES[2],
            ),
            GraduatedRange(
                lower=_B3,
                upper=_B4,
                label=f"{_B3:.0f} - {_B4:.0f}",
                color=PURPLES[3],
            ),
            GraduatedRange(
                lower=_B4,
                upper=_MAX,
                label=f"{_B4:.0f}+",
                color=PURPLES[4],
            ),
        ],
        outline_color=PURPLES_OUTLINE,
        outline_width=0.1,
    ),
    processing_step=ProcessingStep(
        description="Filter census tracts to those with Total > 0.",
        action=PythonAction(fn=filter_nonzero_population),
        depends_on=["census_tracts_raw"],
        output=Path("output/census_tracts.shp"),
    ),
)
