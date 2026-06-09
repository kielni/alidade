from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd

from alidade.models import Rule

CRS = "EPSG:26910"
CRS_WGS84 = "EPSG:4326"

BUFFER_100FT_M = 30.48  # 100 ft in metres (UTM units)
BUFFER_30FT_M = 9.144  # 30 ft in metres
BUFFER_HALF_MILE_M = 804.672  # 0.5 mile in metres


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


@dataclass
class VegetationZone:
    label: str
    values: list[str]
    color: str

    @property
    def filter(self) -> str:
        return " OR ".join(f"\"ENHANCED_LIFEFORM\" = '{v}'" for v in self.values)


VEGETATION_ZONES = [
    VegetationZone("Shrub", ["Shrub"], "#1a9850"),
    VegetationZone("Non-native herbaceous", ["Non-native Herbaceous"], "#a6d96a"),
    VegetationZone("Herbaceous", ["Herbaceous"], "#fee08b"),
    VegetationZone(
        "Non-native woodland",
        ["Eucalyptus", "Non-native Forest"],
        "#cccccc",
    ),
    VegetationZone(
        "Native woodland",
        ["Forest", "Deciduous Hardwood", "Evergreen Hardwood", "Pine/Cypress"],
        "#969696",
    ),
    VegetationZone("Riparian forest", ["Riparian Forest"], "#bdd7e7"),
    VegetationZone("Developed", ["Developed"], "#636363"),
]

vegetation_rules = [
    Rule(
        key=f"veg{i}",
        label=zone.label,
        filter=zone.filter,
        symbol_index=i,
    )
    for i, zone in enumerate(VEGETATION_ZONES)
]

# Lng / Lat
BBOX_GENERAL = [-121.841211, 37.381411, -121.777353, 37.410051]
