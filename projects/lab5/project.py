from alidade.models import Project

from .layers.census_tracts import census_tracts
from .layers.census_tracts_raw import census_tracts_raw
from .layers.mall_buffers import mall_buffers
from .layers.malls import malls
from .layers.household_income import household_income
from .layers.household_income_raw import household_income_raw

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
    ],
)
