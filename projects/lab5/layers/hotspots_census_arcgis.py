"""Getis-Ord Gi* hot spot analysis on M22_39 (males 22-39 count).

Source: Optimized Hot Spot Analysis from ArcGIS Pro on census_tracts
"""

from alidade.models import Layer

hotspots_census = Layer(
    id="hotspots_census_arcgis",
    name="Hot Spot Analysis Young Men (ArcGIS Pro)",
    type="vector",
    datasource="data/HotSpotsYoungMen.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=True,
    geometry_type="Polygon",
)
