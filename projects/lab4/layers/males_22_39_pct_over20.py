from pathlib import Path

import geopandas as gpd

from alidade.models import (
    Layer,
    ProcessingStep,
    PythonAction,
    Rule,
    RuleRenderer,
    SimpleFill,
    Symbol,
)

# Jenks natural breaks on pct_m22_39 (tracts > 20%, n=176):
#   counts: 47, 34, 44, 28, 23
_MIN = 20.0
_B1 = 21.24
_B2 = 22.91
_B3 = 25.66
_B4 = 29.97
_MAX = 44.51

# ColorBrewer 5-class Blues (light → dark = low → high %), 50% fill opacity
_BLUES = [
    "239,243,255,128",  # #eff3ff — 20.0–21.2 %
    "189,215,231,128",  # #bdd7e7 — 21.2–22.9 %
    "107,174,214,128",  # #6baed6 — 22.9–25.7 %
    "49,130,189,128",  # #3182bd — 25.7–30.0 %
    "8,81,156,128",  # #08519c — 30.0–44.5 %
]
_OUTLINE = "0,80,200,255"


def _symbol(color: str) -> Symbol:
    return Symbol(
        type="fill",
        layers=[SimpleFill(color=color, outline_color=_OUTLINE, outline_width=0.5)],
    )


def filter_males_22_39_pct(src: Path, output: Path) -> None:
    gdf = gpd.read_file(src)
    gdf = gdf[gdf["Total"] > 0].copy()
    gdf["pct_m22_39"] = gdf["M22_39"] / gdf["Total"] * 100
    gdf[gdf["pct_m22_39"] > _MIN][
        ["geometry", "GEOID", "NAMELSAD", "pct_m22_39"]
    ].to_file(output)


males_22_39_pct_over20 = Layer(
    id="males_22_39_pct_over20",
    name="Males 22-39 > 20% of Population",
    type="vector",
    source="./output/males_22_39_pct_over20.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=True,
    geometry_type="Polygon",
    renderer=RuleRenderer(
        rules_key="r",
        rules=[
            Rule(
                key="r0",
                label=f"{_MIN:.1f} – {_B1:.1f} %",
                filter=f'"pct_m22_39" <= {_B1}',
                symbol_index=0,
            ),
            Rule(
                key="r1",
                label=f"{_B1:.1f} – {_B2:.1f} %",
                filter=f'"pct_m22_39" > {_B1} AND "pct_m22_39" <= {_B2}',
                symbol_index=1,
            ),
            Rule(
                key="r2",
                label=f"{_B2:.1f} – {_B3:.1f} %",
                filter=f'"pct_m22_39" > {_B2} AND "pct_m22_39" <= {_B3}',
                symbol_index=2,
            ),
            Rule(
                key="r3",
                label=f"{_B3:.1f} – {_B4:.1f} %",
                filter=f'"pct_m22_39" > {_B3} AND "pct_m22_39" <= {_B4}',
                symbol_index=3,
            ),
            Rule(
                key="r4",
                label=f"{_B4:.1f} – {_MAX:.1f} %",
                filter=f'"pct_m22_39" > {_B4}',
                symbol_index=4,
            ),
        ],
        symbols=[_symbol(c) for c in _BLUES],
    ),
    processing_step=ProcessingStep(
        description=(
            "Calculate pct_m22_39 = M22_39 / Total * 100; "
            "keep tracts where pct_m22_39 > 20."
        ),
        action=PythonAction(fn=filter_males_22_39_pct),
        depends_on=["census_tracts_males_22_39"],
        output=Path("output/males_22_39_pct_over20.shp"),
    ),
)
