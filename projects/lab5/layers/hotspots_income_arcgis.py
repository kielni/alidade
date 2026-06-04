"""Getis-Ord Gi* hot spot analysis on MedianHH_i.

Source: Optimized Hot Spot Analysis from ArcGIS Pro on household_income
"""

from alidade.models import Layer

hotspots_income = Layer(
    id="hotspots_income_arcgis",
    name="Hot Spot Analysis Household Income (ArcGIS Pro)",
    type="vector",
    datasource="data/HotSpotsIncome.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=True,
    geometry_type="Polygon",
)
