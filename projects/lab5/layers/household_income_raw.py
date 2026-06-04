"""B19013MedHHIncome: 1620 Census tract polygons, EPSG:2227.

Source: data/B19013MedHHIncome.shp.
Bounds: x=[5695774, 6355025] ft, y=[1770384, 2507172] ft.
Key fields: MedianHH_i (float, median household income), GiZScore,
GiPValue, Gi_Bin (Getis-Ord hot spot classification).

Includes tracts with MedianHH_i = 0; use household_income for analysis.
"""

from alidade.models import Layer

household_income_raw = Layer(
    id="household_income_raw",
    name="Household Income (raw)",
    type="vector",
    datasource="data/B19013MedHHIncome.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=False,
    geometry_type="Polygon",
)
