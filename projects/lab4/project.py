from alidade.models import Project

from .layers.cartodb_positron import cartodb_positron
from .layers.census_tracts import census_tracts
from .layers.census_tracts_raw import census_tracts_raw
from .layers.major_roads import major_roads
from .layers.mall_buffers import mall_buffers
from .layers.mall_target_intersect import mall_target_intersect
from .layers.malls import malls
from .layers.roads import roads
from .layers.target_tracts import target_tracts

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
        mall_target_intersect,
        major_roads,
        census_tracts,
        census_tracts_raw,
        target_tracts,
        roads,
        cartodb_positron,
    ],
)
