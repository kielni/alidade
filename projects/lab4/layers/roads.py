from alidade.models import Layer, SimpleLine, SingleSymbol, Symbol

roads = Layer(
    id="roads",
    name="Roads",
    type="vector",
    source="./data/roads.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=True,
    geometry_type="LineString",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="line",
            layers=[
                SimpleLine(
                    line_color="80,80,80,255",
                    line_width=0.5,
                )
            ],
        )
    ),
)
