from pathlib import Path

import geopandas as gpd

from alidade.models import (
    Layer,
    ProcessingStep,
    PythonAction,
    SimpleFill,
    SingleSymbol,
    Symbol,
)

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
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            layers=[
                SimpleFill(
                    color="255,200,50,180",
                    outline_color="180,120,0,255",
                    outline_width=0.5,
                )
            ],
        )
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
