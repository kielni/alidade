from pathlib import Path

import geopandas as gpd

from alidade.models import (
    GraduatedRange,
    GraduatedRenderer,
    Layer,
    ProcessingStep,
    PythonAction,
)
from projects.lab4.util import CENSUS_BUCKETS, CENSUS_OUTLINE

# Same Jenks breaks as census_tracts (M22_39 across all 1,617 tracts).
_MIN = 0.0
_B1 = 424.0
_B2 = 740.0
_B3 = 1162.0
_B4 = 2003.0
_MAX = 2973.0

# output/mall_target_intersect.shp: census tracts (pct_m22_39 > 20%) that
# spatially intersect a mall 5-mile buffer. One row per (tract × mall) pair.
# Fields: GEOID, NAMELSAD, Total, M22_39, pct_m22_39, mall_id, mall_name.
_PCT_THRESHOLD = 20.0


def intersect_mall_buffer_tracts(buffers: Path, tracts: Path, output: Path) -> None:
    buf = gpd.read_file(buffers)[["id", "mall_name", "geometry"]].rename(
        columns={"id": "mall_id"}
    )

    tr = gpd.read_file(tracts)
    tr = tr[tr["Total"] > 0].copy()
    tr["pct_m22_39"] = tr["M22_39"] / tr["Total"] * 100
    tr = tr[tr["pct_m22_39"] > _PCT_THRESHOLD][
        ["GEOID", "NAMELSAD", "Total", "M22_39", "pct_m22_39", "geometry"]
    ]

    joined = gpd.sjoin(tr, buf, how="inner", predicate="intersects")
    joined = joined.drop(columns=["index_right"])
    joined[
        [
            "GEOID",
            "NAMELSAD",
            "Total",
            "M22_39",
            "pct_m22_39",
            "mall_id",
            "mall_name",
            "geometry",
        ]
    ].to_file(output)


mall_target_intersect = Layer(
    id="mall_target_intersect",
    name="Mall Target Intersect",
    type="vector",
    source="./output/mall_target_intersect.shp",
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
                label=f"{_MIN:.0f} – {_B1:.0f}",
                color=CENSUS_BUCKETS[0],
            ),
            GraduatedRange(
                lower=_B1,
                upper=_B2,
                label=f"{_B1:.0f} – {_B2:.0f}",
                color=CENSUS_BUCKETS[1],
            ),
            GraduatedRange(
                lower=_B2,
                upper=_B3,
                label=f"{_B2:.0f} – {_B3:.0f}",
                color=CENSUS_BUCKETS[2],
            ),
            GraduatedRange(
                lower=_B3,
                upper=_B4,
                label=f"{_B3:.0f} – {_B4:.0f}",
                color=CENSUS_BUCKETS[3],
            ),
            GraduatedRange(
                lower=_B4, upper=_MAX, label=f"{_B4:.0f}+", color=CENSUS_BUCKETS[4]
            ),
        ],
        outline_color=CENSUS_OUTLINE,
        outline_width=0.1,
    ),
    processing_step=ProcessingStep(
        description=(
            "Spatial inner join (intersects) of mall 5-mile buffers with"
            " census tracts where pct_m22_39 > 20%; retains Total and M22_39."
        ),
        action=PythonAction(fn=intersect_mall_buffer_tracts),
        depends_on=["mall_buffers", "census_tracts"],
        output=Path("output/mall_target_intersect.shp"),
    ),
)
