from alidade.models import Project

from .layers.libraries import libraries
from .layers.paloalto_cityboundary import paloalto_cityboundary
from .layers.carto_test_3 import carto_test_3
from .layers.osm_gray_scale import osm_gray_scale
from .layers.high_schools import high_schools
from .layers.high_schools_2227 import high_schools_2227
from .layers.high_schools_buffer import high_schools_buffer

spec = Project(
    title="",
    crs="EPSG:2227",
    extent=(
        6056039.14008246,
        1946189.7836964093,
        6110664.6121568605,
        2010948.4156161044,
    ),
    layers=[
        high_schools_buffer,
        high_schools_2227,
        high_schools,
        libraries,
        paloalto_cityboundary,
        carto_test_3,
        osm_gray_scale,
    ],
)
