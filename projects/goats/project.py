from alidade.models import Project
from projects.goats.layers.basemap import basemap
from projects.goats.layers.park_boundary import park_boundary

spec = Project(
    title="Alum Rock Goat Grazing",
    crs="EPSG:26910",
    extent=(
        603628.0288069494,
        4138828.9799421867,
        607872.9612583271,
        4140758.2218029452,
    ),
    layers=[
        park_boundary,
        basemap,
    ],
)
