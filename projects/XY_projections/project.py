from alidade.models import ProjectSpec
from projects.XY_projections.layers.libraries import libraries
from projects.XY_projections.layers.paloalto_cityboundary import paloalto_cityboundary
from projects.XY_projections.layers.carto_test_3 import carto_test_3
from projects.XY_projections.layers.osm_gray_scale import osm_gray_scale
from projects.XY_projections.layers.high_schools import high_schools
from projects.XY_projections.layers.high_schools_2227 import high_schools_2227
from projects.XY_projections.layers.high_schools_buffer import high_schools_buffer

spec = ProjectSpec(
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
