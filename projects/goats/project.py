from alidade.models import Project
from projects.goats.layers.basemap import basemap
from projects.goats.layers.developed_area import developed_area
from projects.goats.layers.elevation import elevation
from projects.goats.layers.park_boundary import park_boundary
from projects.goats.layers.slope import slope
from projects.goats.layers.roads_trails import roads_trails
from projects.goats.layers.staging import staging
from projects.goats.layers.water import water
from projects.goats.util import CRS

map_all = Project(
    title="Alum Rock Goat Grazing",
    crs=CRS,
    extent=(
        603628.0288069494,
        4138828.9799421867,
        607872.9612583271,
        4140758.2218029452,
    ),
    layers=[
        staging,
        park_boundary,
        developed_area,
        water,
        roads_trails,
        slope,
        elevation,
        basemap,
    ],
)

map = Project(
    title="Alum Rock Goat Grazing",
    crs=CRS,
    extent=(
        603628.0288069494,
        4138828.9799421867,
        607872.9612583271,
        4140758.2218029452,
    ),
    layers=[
        staging,
        park_boundary,
        developed_area,
        water,
        roads_trails,
        slope,
        basemap,
    ],
)

spec = map_all
