from alidade.models import Layer, RuleRenderer, SimpleFill, Symbol
from projects.goats.util import CRS, VEGETATION_ZONES, hex_to_rgba, vegetation_rules
from projects.goats.layers.vegetation import vegetation

_symbols = [
    Symbol(
        type="fill",
        layers=[
            SimpleFill(
                color=hex_to_rgba(color, 0),
                style="solid",
                outline_color=hex_to_rgba(color, 255),
                outline_width=1.0,
            )
        ],
    )
    for _, _, color in VEGETATION_ZONES
]

vegetation_outline = Layer(
    id="vegetation_outline",
    name="Fine-Scale Vegetation outline",
    type="vector",
    inputs=[vegetation],
    datasource="output/vegetation.gpkg|layername=vegetation",
    crs=CRS,
    geometry_type="MultiPolygon",
    renderer=RuleRenderer(
        rules_key="veg",
        rules=vegetation_rules,
        symbols=_symbols,
    ),
)
