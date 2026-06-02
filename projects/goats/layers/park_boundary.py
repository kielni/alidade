from alidade.models import Layer, SimpleFill, SingleSymbol, Symbol

park_boundary = Layer(
    id="park_boundary",
    name="Park Boundary",
    type="vector",
    source="./data/park_boundary.geojson",
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
                    outline_color="128,0,128,255",
                    outline_width=1.5,
                )
            ],
        )
    ),
)
