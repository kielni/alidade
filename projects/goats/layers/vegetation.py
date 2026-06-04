import geopandas as gpd

from alidade.models import (
    BoundLayer,
    Layer,
    PythonAction,
    Rule,
    RuleRenderer,
    SimpleFill,
    Symbol,
)
from projects.goats.layers.border import border
from projects.goats.util import CRS, clip_border, hex_to_rgba

_GDB_LAYER = "CRUZ_CLARA_FINESCALE_VEG_6_15_2023"

# Vegetation suitability for goat grazing, based on Alum Rock VMP.
# Colors: green → yellow for suitable tiers; grays for poorly suited / excluded.
#
# Suitable:
#   Shrub — primary target
#   Non-native Herbaceous — invasive but not preferred by goats
#   Herbaceous — native grassland
#
# Poorly suited or excluded:
#   Eucalyptus + Non-native Forest — not suitable for goats
#   Forest + native hardwoods + Pine/Cypress — not suitable for goats
#   Riparian Forest — excluded by regulatory restrictions
#   Developed — not applicable
_ZONES = [
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
    # TODO: rewrite as list of lifeforms and build query later
    (
        "Non-native woodland",
        (
            "\"ENHANCED_LIFEFORM\" = 'Eucalyptus'"
            " OR \"ENHANCED_LIFEFORM\" = 'Non-native Forest'"
        ),
        "#cccccc",
    ),
    (
        "Native woodland",
        (
            "\"ENHANCED_LIFEFORM\" = 'Forest'"
            " OR \"ENHANCED_LIFEFORM\" = 'Deciduous Hardwood'"
            " OR \"ENHANCED_LIFEFORM\" = 'Evergreen Hardwood'"
            " OR \"ENHANCED_LIFEFORM\" = 'Pine/Cypress'"
        ),
        "#969696",
    ),
    (
        "Riparian forest",
        "\"ENHANCED_LIFEFORM\" = 'Riparian Forest'",
        "#bdd7e7",
    ),
    (
        "Developed",
        "\"ENHANCED_LIFEFORM\" = 'Developed'",
        "#636363",
    ),
]


def clip_vegetation(layer: BoundLayer) -> None:
    """Reproject and clip Santa Cruz/Santa Clara fine-scale vegetation to boundary."""
    (border,) = layer.inputs
    gdf = gpd.read_file(layer.raw_path, layer=_GDB_LAYER).to_crs(CRS)
    clip_border(gdf, border.path).to_file(layer.path, driver="GPKG")


_rules = [
    Rule(
        key=f"veg{i}",
        label=label,
        filter=filter_expr,
        symbol_index=i,
    )
    for i, (label, filter_expr, _) in enumerate(_ZONES)
]

_symbols = [
    Symbol(
        type="fill",
        layers=[
            SimpleFill(
                color=hex_to_rgba(color, 200),
                style="solid",
                outline_color="80,80,80,120",
                outline_width=0,
            )
        ],
    )
    for _, _, color in _ZONES
]

vegetation = Layer(
    id="fine_scale_vegetation",
    name="Fine-Scale Vegetation (2020)",
    type="vector",
    inputs=[border],
    raw_file="data/fine_scale_vegetation.gdb",
    datasource="output/vegetation.gpkg|layername=vegetation",
    provider="ogr",
    crs=CRS,
    visible=True,
    geometry_type="MultiPolygon",
    renderer=RuleRenderer(
        rules_key="veg",
        rules=_rules,
        symbols=_symbols,
    ),
    action=PythonAction(fn=clip_vegetation),
)
