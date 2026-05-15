from alidade.models import Project

from .layers.males_22_39_pct_over20 import males_22_39_pct_over20
from .layers.openstreetmap import openstreetmap
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
        males_22_39_pct_over20,
        roads,
        openstreetmap,
    ],
)
