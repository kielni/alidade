from alidade.models import Project
from projects.sample.layers.arp_areas import arp_areas
from projects.sample.layers.arp_slope import arp_slope
from projects.sample.layers.cartodb_positron import cartodb_positron
from projects.sample.layers.elevation import elevation
from projects.sample.layers.elevation_10n import elevation_10n
from projects.sample.layers.esri_satellite import esri_satellite
from projects.sample.layers.park_features_symbol_lines import park_features_symbol_lines
from projects.sample.layers.park_features_symbol_points import (
    park_features_symbol_points,
)
from projects.sample.layers.park_features_symbol_polygons import (
    park_features_symbol_polygons,
)
from projects.sample.layers.park_polygon import park_polygon
from projects.sample.layers.slope import slope
from projects.sample.layers.unique_values_table import unique_values_table

spec = Project(
    title="",
    crs="EPSG:26910",
    extent=(
        605148.0975601125,
        4139304.783319104,
        605845.1453876096,
        4140093.2879730943,
    ),
    layers=[
        park_polygon,
        unique_values_table,
        slope,
        elevation_10n,
        arp_areas,
        park_features_symbol_points,
        park_features_symbol_lines,
        park_features_symbol_polygons,
        arp_slope,
        cartodb_positron,
        esri_satellite,
        elevation,
    ],
)
