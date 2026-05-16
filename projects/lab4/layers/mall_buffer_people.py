from pathlib import Path

import geopandas as gpd
import numpy as np

from alidade.models import (
    Layer,
    ProcessingStep,
    PythonAction,
    Rule,
    RuleRenderer,
    SimpleFill,
    Symbol,
)

# output/mall_buffer_people.shp: one row per mall buffer, with M22_39 summed
# across all target census tracts (pct_m22_39 > 20%) that spatially intersect
# that buffer. Fields: mall_id, mall_name, m22_39_total, bucket, geometry.
# bucket is 0/1/2 (good/better/best) computed at runtime via equal-count breaks.

# ColorBrewer YlGnBu 3-class (light → dark = good → best).
# Fill at 80% transparent (alpha 51); outline at full opacity, same hue.
_YLGNBU = [
    "161,218,180",  # #a1dab4 — good
    "65,182,196",  # #41b6c4 — better
    "34,94,168",  # #225ea8 — best
]


def _symbol(rgb: str, outline_width: float) -> Symbol:
    return Symbol(
        type="fill",
        layers=[
            SimpleFill(
                color=f"{rgb},40",
                outline_color=f"{rgb},255",
                outline_width=outline_width,
            )
        ],
    )


_SYMBOLS = [
    _symbol(_YLGNBU[0], 0.5),  # Good   — yellow-green, thin
    _symbol(_YLGNBU[1], 0.75),  # Better — teal, medium
    _symbol(_YLGNBU[2], 1.0),  # Best   — blue, thick
]


def aggregate_mall_m22_39(tracts: Path, buffers: Path, output: Path) -> None:
    tr = gpd.read_file(tracts)[["M22_39", "geometry"]]
    buf = gpd.read_file(buffers)[["id", "mall_name", "geometry"]].rename(
        columns={"id": "mall_id"}
    )
    print(f"  tracts: {len(tr)} rows, CRS={tr.crs}")
    print(f"  buffers: {len(buf)} rows, CRS={buf.crs}")

    joined = gpd.sjoin(tr, buf, how="inner", predicate="intersects")
    print(
        f"  sjoin result: {len(joined)} rows,"
        f" {joined['mall_id'].nunique()} unique malls"
    )
    totals = (
        joined.groupby(["mall_id"])["M22_39"]
        .sum()
        .reset_index()
        .rename(columns={"M22_39": "m22_39_total"})
    )

    vals = totals["m22_39_total"]
    p33 = float(np.percentile(vals, 100 / 3))
    p67 = float(np.percentile(vals, 200 / 3))
    totals["bucket"] = 2
    totals.loc[totals["m22_39_total"] <= p67, "bucket"] = 1
    totals.loc[totals["m22_39_total"] <= p33, "bucket"] = 0
    print(f"  mall_buffer_people breaks: good ≤ {p33:,.0f}, better ≤ {p67:,.0f}")

    result = buf.merge(totals, on="mall_id", how="inner")
    result[["mall_id", "mall_name", "m22_39_total", "bucket", "geometry"]].to_file(
        output
    )


mall_buffer_people = Layer(
    id="mall_buffer_people",
    name="Mall Buffer People",
    type="vector",
    source="./output/mall_buffer_people.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=True,
    geometry_type="Polygon",
    renderer=RuleRenderer(
        rules_key="r",
        rules=[
            Rule(key="r0", label="Good", filter='"bucket" = 0', symbol_index=0),
            Rule(key="r1", label="Better", filter='"bucket" = 1', symbol_index=1),
            Rule(key="r2", label="Best", filter='"bucket" = 2', symbol_index=2),
        ],
        symbols=_SYMBOLS,
    ),
    processing_step=ProcessingStep(
        description=(
            "Spatial join target tracts (pct_m22_39 > 20%) with mall 5-mile"
            " buffers; sum M22_39 per mall; assign equal-count bucket (0/1/2)."
        ),
        action=PythonAction(fn=aggregate_mall_m22_39),
        depends_on=["target_tracts", "mall_buffers"],
        output=Path("output/mall_buffer_people.shp"),
    ),
)

if __name__ == "__main__":
    _proj = Path(__file__).parent.parent / "output"
    aggregate_mall_m22_39(
        _proj / "target_tracts.shp",
        _proj / "mall_buffers.shp",
        _proj / "mall_buffer_people.shp",
    )
