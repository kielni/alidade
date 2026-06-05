from alidade.models import Project
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
from projects.goats.layers.priority_developed import priority_developed
from projects.goats.layers.priority_roads_trails import priority_roads_trails
from projects.goats.layers.exclude_water_vegetation import exclude_water_vegetation
from projects.goats.layers.patches import patches
from projects.goats.layers.staging_ranked import staging_ranked
from projects.goats.layers.suitability import suitability
from projects.goats.layers.targets import targets
from projects.goats.util import CRS

EXTENT = (
    603628.0288069494,
    4138828.9799421867,
    607872.9612583271,
    4140758.2218029452,
)

map_all = Project(
    title="Alum Rock Goat Grazing",
    crs=CRS,
    extent=EXTENT,
    layers=[
        staging_ranked,
        staging,
        park_boundary,
        border,
        targets,
        patches,
        exclude_water_vegetation,
        priority_roads_trails,
        priority_developed,
        developed_area,
        water,
        roads_trails,
        slope,
        elevation,
        vegetation,
        suitability,
        basemap,
    ],
)

"""
Park boundary with data layers (staging areas, creek, roads/trails, developed zone)
"""
map_park = Project(
    id="park",
    title="Alum Rock Park",
    crs=CRS,
    extent=EXTENT,
    layers=[
        park_boundary,
        staging,
        developed_area,
        water,
        roads_trails,
        basemap,
    ],
)

"""
Slope analysis derived from DEM, clipped to park + 100ft buffer
"""
map_slope = Project(
    id="slope",
    title="Alum Rock Park: Slopes",
    crs=CRS,
    extent=EXTENT,
    layers=[
        park_boundary,
        developed_area,
        water,
        roads_trails,
        slope,
        basemap,
    ],
)

"""
Vegetation classification map, clipped to park; classes combined to 4-6 zones
"""
map_veg = Project(
    title="Alum Rock: Vegetation",
    id="vegetation",
    crs=CRS,
    extent=EXTENT,
    layers=[
        park_boundary,
        developed_area,
        water,
        roads_trails,
        vegetation,
        basemap,
    ],
)

"""
Exclusion and priority zones (riparian buffer, road/trail buffer)
"""
map_zones = Project(
    title="Alum Rock Goat Priority and Exclusion Zones",
    id="zones",
    crs=CRS,
    extent=EXTENT,
    layers=[
        park_boundary,
        exclude_water_vegetation,
        priority_roads_trails,
        priority_developed,
        developed_area,
        water,
        roads_trails,
        basemap,
    ],
)

"""
Weighted overlay suitability raster
"""
map_suitability = Project(
    title="Alum Rock Goat Grazing Suitability",
    id="suitability",
    crs=CRS,
    extent=EXTENT,
    layers=[
        staging,
        suitability,
        park_boundary,
        developed_area,
        water,
        roads_trails,
        basemap,
    ],
)

map_patches = Project(
    title="Alum Rock Goat Grazing Patches",
    id="patches",
    crs=CRS,
    extent=EXTENT,
    layers=[
        staging,
        patches,
        park_boundary,
        developed_area,
        water,
        roads_trails,
        basemap,
    ],
)
"""
Recommended goat grazing zones (park-wide overview)
"""
map_targets = Project(
    title="Alum Rock Goat Grazing Targets",
    id="targets",
    crs=CRS,
    extent=EXTENT,
    layers=[
        park_boundary,
        targets,
        suitability,
        developed_area,
        water,
        roads_trails,
        basemap,
    ],
)

# cluster-based
map_targets_cluster = Project(
    title="Alum Rock Goat Grazing Targets",
    id="targets_cluster",
    crs=CRS,
    extent=EXTENT,
    layers=[
        park_boundary,
        staging_ranked,
        patches,
        developed_area,
        water,
        roads_trails,
        basemap,
    ],
)
"""
Detail map(s) of highest-priority zones at large scale
"""
map_detail = Project(
    title="Alum Rock Goat Grazing Detail",
    id="detail",
    crs=CRS,
    extent=EXTENT,
    layers=[
        park_boundary,
        staging_ranked,
        suitability,
        staging,
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
    map_targets_cluster,
    map_patches,
    map_detail,
]
spec = map_all
