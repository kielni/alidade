from alidade.models import PrintLayout, PrintMapFrame, PrintScaleBar, Project

from .layers.basemap import basemap
from .layers.census_tracts import census_tracts
from .layers.census_tracts_raw import census_tracts_raw
from .layers.major_roads import major_roads
from .layers.mall_buffers import mall_buffers
from .layers.mall_buffer_people import mall_buffer_people
from .layers.mall_target_intersect import mall_target_intersect
from .layers.mall_people_deduped import mall_people_deduped
from .layers.malls import malls
from .layers.roads import roads
from .layers.target_tracts import target_tracts

CREDITS = (
    "US Census Bureau, 2010 data · Big Bucks INC"
    " · CartoDB Dark Matter · CC BY-SA 4.0 via Wikimedia Commons"
)

_FRAME_350k = PrintMapFrame(scale=350000)
_SCALE_BAR_350k = PrintScaleBar(
    unit_type="mi", num_units_per_segment=5.0, num_segments=2
)

EXTENT_600k = (
    5925815.516200287,
    1815209.5977735333,
    6171517.492646666,
    2370764.042217977,
)

EXTENT_350k = (
    5981864.529348838,
    1900163.1315698293,
    6125190.682275892,
    2224236.5574957547,
)

spec_all = Project(
    title="Lab 4",
    crs="EPSG:2227",
    extent=EXTENT_600k,
    layers=[
        malls,
        mall_people_deduped,
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
distribution of 22-39 year old males (census_tracts)
mall locations (malls)
major roads (major_roads)
"""
map1 = Project(
    title="Map 1: Overview",
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
        name="print_1",
        orientation="portrait",
        title_text="Big Bucks Malls and Age 22-39 Men",
        credits_text=CREDITS,
        map_frame=PrintMapFrame(scale=600000),
        # At 1:600,000 one 50-mile segment is ~134 mm; 1 segment fits centered
        # on a 215.9 mm-wide portrait page.  Two segments would overflow.
        scale_bar=PrintScaleBar(
            unit_type="mi",
            num_units_per_segment=50.0,
            num_segments=1,
            x_mm=40.9,
        ),
    ),
)

"""
1:350,000 scale map
Census tracts with greater than 20% 22-39 year old males (target_tracts)
mall locations (malls)
"""
map2 = Project(
    title="Map 2: Target Census Tracts and Malls",
    crs="EPSG:2227",
    extent=EXTENT_350k,
    layers=[
        malls,
        target_tracts,
        basemap,
    ],
    print_layout=PrintLayout(
        name="print_2",
        orientation="portrait",
        title_text="Target Areas: 20+% Age 22-39 Men",
        credits_text=CREDITS,
        map_frame=_FRAME_350k,
        scale_bar=_SCALE_BAR_350k,
    ),
)

"""
1:350,000 scale map
Census tracts with >20% 22-39 year old males near malls (mall_target_intersect)
mall locations (malls)
5 mile buffers of malls (mall_buffers) ; unfilled or transparent polygons
"""
map3 = Project(
    title="Map 3: Malls and Target Tracts Near Malls",
    crs="EPSG:2227",
    extent=EXTENT_350k,
    layers=[
        malls,
        mall_buffer_people,
        mall_target_intersect,
        basemap,
    ],
    print_layout=PrintLayout(
        name="print_3",
        orientation="portrait",
        title_text="Target Population Near Malls",
        credits_text=CREDITS,
        map_frame=_FRAME_350k,
        scale_bar=_SCALE_BAR_350k,
    ),
)


map4 = Project(
    title="Map 4: Deduplicated Target Population by Mall Draw Zone",
    crs="EPSG:2227",
    extent=EXTENT_350k,
    layers=[
        malls,
        # needed as depdendency for mall_people_deduped but not actually visible
        mall_buffers.model_copy(update={"visible": False}),
        target_tracts.model_copy(update={"visible": False}),
        mall_people_deduped,
        basemap,
    ],
    print_layout=PrintLayout(
        name="print_4",
        orientation="portrait",
        title_text="Mall Draw Zone and Target Population",
        credits_text=CREDITS,
        map_frame=_FRAME_350k,
        scale_bar=_SCALE_BAR_350k,
    ),
)

spec = map4
