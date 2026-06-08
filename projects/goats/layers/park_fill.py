from alidade.models import Layer, SimpleFill, SingleSymbol, Symbol

park_fill = Layer(
    id="park_solid_fill",
    name="Park Fill",
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
                    color="255,255,255,255",
                    style="solid",
                    outline_color="0,0,0,0",
                    outline_width=0,
                )
            ],
        )
    ),
)
