from alidade.models import Layer, SimpleFill, SingleSymbol, Symbol
from projects.goats.palette import PARK_BOUNDARY_EDGE, TRANSPARENT
from projects.goats.util import CRS_WGS84

"""
Alum Rock Park boundary layer, from OpenStreetMap data
downloaded via Overpass Turbo: https://overpass-turbo.eu

[out:json][timeout:25];
(
  relation["name"="Alum Rock Park"]["leisure"="park"]({{bbox}});
  way["name"="Alum Rock Park"]["leisure"="park"]({{bbox}});
);
out geom;
"""
park_boundary = Layer(
    id="park_boundary",
    name="Park Boundary",
    type="vector",
    datasource="data/park_boundary.geojson",
    source_description="Park boundary polygon",
    source_origin="OpenStreetMap via Overpass Turbo",
    crs=CRS_WGS84,
    visible=True,
    geometry_type="Polygon",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            layers=[
                SimpleFill(
                    color=TRANSPARENT,
                    style="no",
                    outline_color=PARK_BOUNDARY_EDGE,
                    outline_width=1,
                )
            ],
        )
    ),
)
