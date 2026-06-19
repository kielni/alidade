from alidade.models import Extent, Map
from projects.goats.layers.basemap import basemap
from projects.goats.layers.basemap_satellite import basemap_satellite
from projects.goats.layers.border import border
from projects.goats.layers.developed_area import developed_area
from projects.goats.layers.elevation import elevation
from projects.goats.layers.park_boundary import park_boundary
from projects.goats.layers.slope import slope
from projects.goats.layers.roads_trails import roads_trails
from projects.goats.layers.staging import staging
from projects.goats.layers.vegetation import vegetation
from projects.goats.layers.park_fill import park_fill
from projects.goats.layers.vegetation_highlight import vegetation_highlight
from projects.goats.layers.water import water
from projects.goats.layers.priority_developed import priority_developed
from projects.goats.layers.priority_roads_trails import priority_roads_trails
from projects.goats.layers.exclude_water_vegetation import exclude_water_vegetation
from projects.goats.layers.target_zones import target_zones
from projects.goats.layers.staging_ranked import staging_ranked
from projects.goats.layers.suitability import suitability
from projects.goats.util import CRS

EXTENT = Extent(
    xmin=-121.82933556539967,
    ymin=37.389950939471255,
    xmax=-121.78110958256352,
    ymax=37.40782156055017,
    crs="EPSG:4326",
).to_crs(CRS)

# build all layers
map_all = Map(
    title="Alum Rock Goat Grazing",
    crs=CRS,
    extent=EXTENT,
    layers=[
        staging_ranked,
        staging,
        park_boundary,
        border,
        target_zones,
        exclude_water_vegetation,
        priority_roads_trails,
        priority_developed,
        developed_area,
        water,
        roads_trails,
        slope,
        elevation,
        vegetation,
        vegetation_highlight,
        suitability,
        park_fill,
        basemap,
    ],
)

"""
1: Park overview: staging areas, creek, roads/trails, developed zone
"""
map_park = Map(
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
2: Slope analysis derived from USGS DEM
"""
map_slope = Map(
    id="slope",
    title="Slopes",
    crs=CRS,
    extent=EXTENT,
    layers=[
        park_boundary,
        water,
        roads_trails,
        slope,
        basemap,
    ],
)

"""
3: Vegetation classification; lifeform classes grouped into 6 classes, plus developed
"""
map_veg = Map(
    title="Vegetation",
    id="vegetation",
    crs=CRS,
    extent=EXTENT,
    layers=[
        park_boundary,
        water,
        roads_trails,
        vegetation,
        basemap,
    ],
)

"""
4: Priority (road and trail edges, developed area) and exclusion (riparian buffer) zones
"""
map_zones = Map(
    title="Priority and Exclusion Zones",
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
5: Weighted overlay for suitability from priority/exclusion zones, slope, and vegetation
"""
map_suitability = Map(
    title="Goat Grazing Suitability",
    id="suitability",
    crs=CRS,
    extent=EXTENT,
    layers=[
        staging,
        suitability,
        park_boundary,
        water,
        roads_trails,
        park_fill,
        basemap,
    ],
)

"""
6: Group and smooth suitability outputs into target zones
"""
map_target_zones = Map(
    title="Goat Grazing Target Zones",
    id="patches",
    crs=CRS,
    extent=EXTENT,
    layers=[
        staging,
        target_zones,
        park_boundary,
        water,
        roads_trails,
        park_fill,
        basemap,
    ],
)

"""
7: Prioritized staging areas based on access to target zones
"""
map_ranked_staging = Map(
    title="Target Staging Areas",
    id="targets_cluster",
    crs=CRS,
    extent=EXTENT,
    layers=[
        park_boundary,
        staging_ranked,
        target_zones,
        water,
        roads_trails,
        park_fill,
        basemap,
    ],
)

"""
8: Detail map of top staging location, with satellite basemap, priority zones, and
vegetation zones.
"""
EXTENT_DETAIL = Extent(
    xmin=-121.81774937930001,
    ymin=37.39151926943471,
    xmax=-121.80662022350002,
    ymax=37.39690041368934,
    crs="EPSG:4326",
).to_crs(CRS)

map_detail = Map(
    title="Rustic Lands Staging area",
    id="detail",
    crs=CRS,
    extent=EXTENT_DETAIL,
    layers=[
        park_boundary,
        staging_ranked,
        priority_roads_trails,
        vegetation_highlight,
        water,
        roads_trails,
        basemap_satellite,
    ],
)

maps = [
    map_park,
    map_slope,
    map_veg,
    map_zones,
    map_suitability,
    map_target_zones,
    map_ranked_staging,
    map_detail,
]
spec = map_all
