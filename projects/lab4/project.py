from alidade.models import Project

from .layers.census_tracts_males_22_39 import census_tracts_males_22_39
from .layers.openstreetmap import openstreetmap
from .layers.roads import roads

spec = Project(
    title="Lab 4",
    crs="EPSG:2227",
    extent=(
        5695774.397680,
        1770384.036803,
        6355024.590892,
        2507172.370473,
    ),
    layers=[
        census_tracts_males_22_39,
        roads,
        openstreetmap,
    ],
)
