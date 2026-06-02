from alidade.models import Project
from projects.lab5.layers.census_tracts import census_tracts
from projects.lab5.layers.census_tracts_raw import census_tracts_raw
from projects.lab5.layers.hotspots_census import hotspots_census
from projects.lab5.layers.hotspots_income import hotspots_income
from projects.lab5.layers.hotspots_census_arcgis import (
    hotspots_census as hotspots_census_arcgis,
)
from projects.lab5.layers.hotspots_income_arcgis import (
    hotspots_income as hotspots_income_arcgis,
)
from projects.lab5.layers.hotspots_overlap import hotspots_overlap
from projects.lab5.layers.mall_buffers import mall_buffers
from projects.lab5.layers.malls import malls
from projects.lab5.layers.household_income import household_income
from projects.lab5.layers.household_income_raw import household_income_raw

EXTENT = (
    5460528.438,
    1733544.620,
    6590270.550,
    2544011.787,
)

spec = Project(
    output_format="lyrx",
    title="Lab 5",
    crs="EPSG:2227",
    extent=EXTENT,
    layers=[
        malls,
        mall_buffers,
        census_tracts,
        census_tracts_raw,
        household_income,
        household_income_raw,
        hotspots_income,
        hotspots_census,
        hotspots_income_arcgis,
        hotspots_census_arcgis,
        hotspots_overlap,
    ],
)
