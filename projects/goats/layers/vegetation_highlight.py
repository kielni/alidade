from alidade.models import Layer, Rule, RuleRenderer, SimpleFill, Symbol
from projects.goats.util import CRS, hex_to_rgba
from projects.goats.layers.vegetation import vegetation

_HIGHLIGHT_ZONES = [
    (
        "Shrub",
        "\"ENHANCED_LIFEFORM\" = 'Shrub'",
        "#1a9850",
    ),
    (
        "Non-native herbaceous",
        "\"ENHANCED_LIFEFORM\" = 'Non-native Herbaceous'",
        "#a6d96a",
    ),
    (
        "Herbaceous",
        "\"ENHANCED_LIFEFORM\" = 'Herbaceous'",
        "#fee08b",
    ),
]

_rules = [
    Rule(
        key=f"veg_highlight{i}",
        label=label,
        filter=filter_expr,
        symbol_index=i,
    )
    for i, (label, filter_expr, _) in enumerate(_HIGHLIGHT_ZONES)
]

_symbols = [
    Symbol(
        type="fill",
        layers=[
            SimpleFill(
                color=hex_to_rgba(color, 32),
                style="solid",
                outline_color=hex_to_rgba(color, 255),
                outline_width=0.5,
            )
        ],
    )
    for _, _, color in _HIGHLIGHT_ZONES
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
