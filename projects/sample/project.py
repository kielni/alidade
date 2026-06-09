from alidade.models import Extent, Project
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
    extent=Extent(
        xmin=-121.81209934186269,
        ymin=37.39447264780004,
        xmax=-121.80411315462595,
        ymax=37.40165792373717,
        crs="EPSG:4326",
    ).to_crs("EPSG:26910"),
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
