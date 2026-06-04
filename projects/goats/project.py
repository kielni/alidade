from alidade.models import ProjectSpec
from projects.goats.layers.basemap import basemap
from projects.goats.layers.border import border
from projects.goats.layers.developed_area import developed_area
from projects.goats.layers.elevation import elevation
from projects.goats.layers.park_boundary import park_boundary
from projects.goats.layers.slope import slope
from projects.goats.layers.roads_trails import roads_trails
from projects.goats.layers.staging import staging
from projects.goats.layers.vegetation import vegetation
from projects.goats.layers.water import water
from projects.goats.util import CRS

EXTENT = (
    603628.0288069494,
    4138828.9799421867,
    607872.9612583271,
    4140758.2218029452,
)

map_all = ProjectSpec(
    title="Alum Rock Goat Grazing",
    crs=CRS,
    extent=EXTENT,
    layers=[
        staging,
        park_boundary,
        border,
        developed_area,
        water,
        roads_trails,
        slope,
        elevation,
        vegetation,
        basemap,
    ],
)

"""
Park boundary with data layers (staging areas, creek, roads/trails, developed zone)
"""
map_park = ProjectSpec(
    id="park",
    title="Alum Rock Park",
    crs=CRS,
    extent=EXTENT,
    layers=[
        staging,
        park_boundary,
        border,
        developed_area,
        water,
        roads_trails,
        basemap,
    ],
)

"""
Slope analysis derived from DEM, clipped to park + 100ft buffer
"""
map_slope = ProjectSpec(
    id="slope",
    title="Alum Rock Park: Slopes",
    crs=CRS,
    extent=EXTENT,
    layers=[
        park_boundary,
        border,
        developed_area,
        water,
        roads_trails,
        slope,
        elevation,
        basemap,
    ],
)

"""
Vegetation classification map, clipped to park; classes combined to 4-6 zones
"""
map_veg = ProjectSpec(
    title="Alum Rock: Vegetation",
    id="vegetation",
    crs=CRS,
    extent=EXTENT,
    layers=[
        park_boundary,
        border,
        developed_area,
        water,
        roads_trails,
        vegetation,
        basemap,
    ],
)

"""
Exclusion and priority zones (riparian buffer, road/trail buffer, staging range)
"""
map_zones = ProjectSpec(
    title="Alum Rock Goat Grazing Zones",
    id="zones",
    crs=CRS,
    extent=EXTENT,
    layers=[
        staging,
        park_boundary,
        border,
        developed_area,
        water,
        roads_trails,
        basemap,
    ],
)

"""
Weighted overlay suitability raster
"""
map_suitability = ProjectSpec(
    title="Alum Rock Goat Grazing Suitability",
    id="suitability",
    crs=CRS,
    extent=EXTENT,
    layers=[
        staging,
        park_boundary,
        border,
        developed_area,
        water,
        roads_trails,
        basemap,
    ],
)

"""
Recommended goat grazing zones (park-wide overview)
"""
map_targets = ProjectSpec(
    title="Alum Rock Goat Grazing Targets",
    id="targets",
    crs=CRS,
    extent=EXTENT,
    layers=[
        staging,
        park_boundary,
        border,
        developed_area,
        water,
        roads_trails,
        basemap,
    ],
)

"""
Detail map(s) of highest-priority zones at large scale
"""
map_detail = ProjectSpec(
    title="Alum Rock Goat Grazing Detail",
    id="detail",
    crs=CRS,
    extent=EXTENT,
    layers=[
        staging,
        park_boundary,
        border,
        developed_area,
        water,
        roads_trails,
        basemap,
    ],
)

maps = [
    map_park,
    map_slope,
    map_veg,
    map_zones,
    map_suitability,
    map_targets,
    map_detail,
]
spec = map_veg
