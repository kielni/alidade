from pathlib import Path

import geopandas as gpd

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
