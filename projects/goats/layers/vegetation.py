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
from projects.goats.util import CRS

_GDB_LAYER = "CRUZ_CLARA_FINESCALE_VEG_6_15_2023"

# Grazing zone reclassification of the 11 ENHANCED_LIFEFORM classes into
# 5 decision zones (plus Developed) for goat management.  Colors chosen to
# read naturally against the CartoDB Positron basemap; alpha=200 lets
# slope/elevation show through.
#
# Group 1 – Primary targets: Shrub/chaparral (Artemisia californica,
#   Ceanothus, Baccharis) — main fire-fuel-reduction use case.
# Group 2 – Invasive/non-native: secondary browsing targets.  Pine/Cypress
#   is native (Pinus sabiniana, P. attenuata) so it goes in Group 3, not here.
# Group 3 – Native woodland: avoid; unsupervised goats damage native oaks.
# Group 4 – Riparian Forest: exclude via 100-ft stream buffer; sensitive habitat.
# Group 5 – Low-priority / neutral: native grassland.
# Developed – irrelevant to management; rendered neutral gray.
_ZONES = [
    (
        "Primary targets (shrub/chaparral)",
        "\"ENHANCED_LIFEFORM\" = 'Shrub'",
        "#d4851e",
    ),
    (
        "Invasive / non-native",
        (
            "\"ENHANCED_LIFEFORM\" = 'Eucalyptus'"
            " OR \"ENHANCED_LIFEFORM\" = 'Non-native Forest'"
            " OR \"ENHANCED_LIFEFORM\" = 'Non-native Herbaceous'"
        ),
        "#9b6fa0",
    ),
    (
        "Native woodland (avoid or buffer)",
        (
            "\"ENHANCED_LIFEFORM\" = 'Evergreen Hardwood'"
            " OR \"ENHANCED_LIFEFORM\" = 'Deciduous Hardwood'"
            " OR \"ENHANCED_LIFEFORM\" = 'Forest'"
            " OR \"ENHANCED_LIFEFORM\" = 'Pine/Cypress'"
        ),
        "#3a6a24",
    ),
    (
        "Riparian Forest (exclude)",
        "\"ENHANCED_LIFEFORM\" = 'Riparian Forest'",
        "#2a7a6a",
    ),
    (
        "Herbaceous (low priority)",
        "\"ENHANCED_LIFEFORM\" = 'Herbaceous'",
        "#d4e882",
    ),
    (
        "Developed",
        "\"ENHANCED_LIFEFORM\" = 'Developed'",
        "#c0c0c0",
    ),
]


def _hex_to_rgba(hex_color: str, alpha: int = 200) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"{r},{g},{b},{alpha}"


def clip_vegetation(boundary: Path, output: Path) -> None:
    project_dir = boundary.parent.parent
    gdb = project_dir / "data" / "fine_scale_vegetation.gdb"
    gdf = gpd.read_file(gdb, layer=_GDB_LAYER).to_crs(CRS)
    mask = gpd.read_file(boundary).to_crs(CRS)
    gpd.clip(gdf, mask).to_file(output, driver="GPKG")


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
                color=_hex_to_rgba(color),
                style="solid",
                outline_color="80,80,80,120",
                outline_width=0.1,
            )
        ],
    )
    for _, _, color in _ZONES
]

vegetation = Layer(
    id="vegetation",
    name="Fine-Scale Vegetation (2020)",
    type="vector",
    source="./output/vegetation.gpkg|layername=vegetation",
    provider="ogr",
    crs=CRS,
    visible=True,
    geometry_type="MultiPolygon",
    renderer=RuleRenderer(
        rules_key="veg",
        rules=_rules,
        symbols=_symbols,
    ),
    processing_step=ProcessingStep(
        description=(
            "Reproject and clip Santa Cruz/Santa Clara fine-scale vegetation"
            " to park boundary"
        ),
        action=PythonAction(fn=clip_vegetation),
        depends_on=["park_boundary"],
        output=Path("output/vegetation.gpkg"),
    ),
)
