"""Unfiltered Bay Area census tracts (BayPopulationByAge.shp).

Used only as the dependency source for population_by_age so the build system
can pass the shapefile path to the filter function. Not displayed directly.
"""

from alidade.models import Layer

population_by_age_raw = Layer(
    id="population_by_age_raw",
    name="Population by Age (raw)",
    type="vector",
    datasource="data/BayPopulationByAge.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=False,
    geometry_type="Polygon",
)
