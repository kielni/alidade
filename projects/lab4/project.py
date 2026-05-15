from alidade.models import Project

from .layers.cartodb_positron import cartodb_positron
from .layers.census_tracts_males_22_39 import census_tracts_males_22_39
from .layers.major_roads import major_roads
from .layers.mall_buffer_tracts import mall_buffer_tracts
from .layers.mall_buffers import mall_buffers
from .layers.malls import malls
from .layers.roads import roads

spec = Project(
    title="Lab 4",
    crs="EPSG:2227",
    extent=(
        5910472.946202975,
        1780518.6560298572,
        6186860.062643979,
        2405454.983961653,
    ),
    layers=[
        malls,
        mall_buffers,
        mall_buffer_tracts,
        major_roads,
        census_tracts_males_22_39,  # not visible
        roads,  # not visible
        cartodb_positron,
    ],
)
