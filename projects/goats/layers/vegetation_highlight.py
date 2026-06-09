"""
Display high-priority vegetation as partially transparent polygons.
"""

from alidade.models import Layer, Rule, RuleRenderer, SimpleFill, Symbol
from projects.goats.util import CRS, VEGETATION_ZONES, hex_to_rgba
from projects.goats.layers.vegetation import vegetation

HIGHLIGHT_ZONES = VEGETATION_ZONES[:3]

_rules = [
    Rule(
        key=f"veg_highlight{i}",
        label=zone.label,
        filter=zone.filter,
        symbol_index=i,
    )
    for i, zone in enumerate(HIGHLIGHT_ZONES)
]

_symbols = [
    Symbol(
        type="fill",
        layers=[
            SimpleFill(
                color=hex_to_rgba(zone.color, 32),
                style="solid",
                outline_color=hex_to_rgba(zone.color, 255),
                outline_width=0.5,
            )
        ],
    )
    for zone in HIGHLIGHT_ZONES
]

vegetation_highlight = Layer(
    id="vegetation_highlight",
    name="Fine-Scale Vegetation Highlight",
    type="vector",
    inputs=[vegetation],
    datasource="output/vegetation.gpkg|layername=vegetation",
    crs=CRS,
    geometry_type="MultiPolygon",
    renderer=RuleRenderer(
        rules_key="veg_highlight",
        rules=_rules,
        symbols=_symbols,
    ),
)
