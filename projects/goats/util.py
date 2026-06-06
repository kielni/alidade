from pathlib import Path

import geopandas as gpd

from alidade.models import Rule

CRS = "EPSG:26910"


def hex_to_rgba(hex_color: str, alpha: int = 255) -> str:
    """Convert a CSS hex color to a QGIS-format 'R,G,B,A' string."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"{r},{g},{b},{alpha}"


def clip_border(gdf: gpd.GeoDataFrame, output: Path) -> gpd.GeoDataFrame:
    """Clip gdf to the buffered park border.

    gdf must already be in project CRS (EPSG:26910).
    """
    mask = gpd.read_file(output.parent / "border.gpkg")
    return gpd.clip(gdf, mask)


def clip_park(gdf: gpd.GeoDataFrame, boundary_path: Path) -> gpd.GeoDataFrame:
    """Clip gdf to the exact park boundary (no buffer).

    gdf must already be in project CRS (EPSG:26910).
    """
    mask = gpd.read_file(boundary_path).to_crs(CRS).dissolve()
    return gpd.clip(gdf, mask)


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
VEGETATION_ZONES = [
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

vegetation_rules = [
    Rule(
        key=f"veg{i}",
        label=label,
        filter=filter_expr,
        symbol_index=i,
    )
    for i, (label, filter_expr, _) in enumerate(VEGETATION_ZONES)
]
