from pathlib import Path

import geopandas as gpd

CRS = "EPSG:26910"


def clip_border(gdf: gpd.GeoDataFrame, output: Path) -> gpd.GeoDataFrame:
    """Clip gdf to the buffered park border.

    gdf must already be in project CRS (EPSG:26910).
    """
    mask = gpd.read_file(output.parent / "border.gpkg")
    return gpd.clip(gdf, mask)
