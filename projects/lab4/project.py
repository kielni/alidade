from alidade.models import PrintLayout, PrintMapFrame, PrintScaleBar, Project

from .layers.basemap import basemap
from .layers.census_tracts import census_tracts
from .layers.census_tracts_raw import census_tracts_raw
from .layers.major_roads import major_roads
from .layers.mall_buffers import mall_buffers
from .layers.mall_buffer_people import mall_buffer_people
from .layers.mall_target_intersect import mall_target_intersect
from .layers.malls import malls
from .layers.roads import roads
from .layers.target_tracts import target_tracts

CREDITS = (
    "US Census Bureau, 2010 data · Big Bucks INC"
    " · CartoDB Positron · CC BY-SA 4.0 via Wikimedia Commons"
)

_FRAME_600k = PrintMapFrame(scale=600000)
_FRAME_350k = PrintMapFrame(scale=350000)
_SCALE_BAR_MI = PrintScaleBar(unit_type="mi", num_units_per_segment=50.0)

EXTENT_600k = (
    5925815.516200287,
    1815209.5977735333,
    6171517.492646666,
    2370764.042217977,
)

EXTENT_350k = (
    5981459.437566431,
    1911100.6096948292,
    6124785.590493485,
    2235174.0356207546,
)

spec_all = Project(
    title="Lab 4",
    crs="EPSG:2227",
    extent=EXTENT_600k,
    layers=[
        malls,
        mall_buffer_people,
        mall_buffers,
        mall_target_intersect,
        major_roads,
        census_tracts,
        census_tracts_raw,
        target_tracts,
        roads,
        basemap,
    ],
)


"""
1:600,000 scale map
distribution of 22-39 year old males (census_tracts), M22_39 graduated color scheme
mall locations (malls)
major roads (major_roads)
"""
spec_overview = Project(
    title="Lab 4 Overview",
    crs="EPSG:2227",
    extent=(
        5925815.516200287,
        1815209.5977735333,
        6171517.492646666,
        2370764.042217977,
    ),
    layers=[
        malls,
        major_roads,
        census_tracts,
        basemap,
    ],
    print_layout=PrintLayout(
        name="print_overview",
        title_text="Distribution of Males Aged 22–39",
        credits_text=CREDITS,
        map_frame=_FRAME_600k,
        scale_bar=_SCALE_BAR_MI,
    ),
)
map1 = spec_overview

"""
1:350,000 scale map
Census tracts with greater than 20% 22-39 year old males (target_tracts)
mall locations (malls)
"""
spec_young_men = Project(
    title="Lab 4 Young Men",
    crs="EPSG:2227",
    extent=EXTENT_350k,
    layers=[
        malls,
        target_tracts,
        basemap,
    ],
    print_layout=PrintLayout(
        name="print_young_men",
        title_text="Census Tracts: Males Aged 22–39 Over 20%",
        credits_text=CREDITS,
        map_frame=_FRAME_350k,
        scale_bar=_SCALE_BAR_MI,
    ),
)
map2 = spec_young_men

"""
1:350,000 scale map
Census tracts with >20% 22-39 year old males near malls (mall_target_intersect)
mall locations (malls)
5 mile buffers of malls (mall_buffers) ; unfilled or transparent polygons
"""
spec_near_malls = Project(
    title="Lab 4",
    crs="EPSG:2227",
    extent=EXTENT_350k,
    layers=[
        malls,
        mall_buffer_people,
        mall_target_intersect,
        basemap,
    ],
    print_layout=PrintLayout(
        name="print_young_men_near_malls",
        title_text="Target Tracts Near Shopping Malls",
        credits_text=CREDITS,
        map_frame=_FRAME_350k,
        scale_bar=_SCALE_BAR_MI,
    ),
)
map3 = spec_near_malls

spec = map1
