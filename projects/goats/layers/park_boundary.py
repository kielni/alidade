from alidade.models import Layer, SimpleFill, SingleSymbol, Symbol

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
    provider="ogr",
    crs="EPSG:4326",
    visible=True,
    geometry_type="Polygon",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            layers=[
                SimpleFill(
                    color="0,0,0,0",
                    style="no",
                    outline_color="128,128,128,255",
                    outline_width=1,
                )
            ],
        )
    ),
)
