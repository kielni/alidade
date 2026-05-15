from alidade.models import Project

from .layers.cartodb_positron import cartodb_positron
from .layers.census_tracts_males_22_39 import census_tracts_males_22_39
from .layers.major_roads import major_roads
from .layers.males_22_39_pct_over20 import males_22_39_pct_over20
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
        males_22_39_pct_over20,
        major_roads,
        census_tracts_males_22_39.model_copy(update={"visible": False}),
        roads.model_copy(update={"visible": False}),
        cartodb_positron,
    ],
)
