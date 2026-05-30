"""malls: 11 Bay Area shopping mall points, EPSG:2227.

Source: data/malls.shp, copied from projects/lab4/output/malls.shp
(geocoded from mall_names.csv via Nominatim).
Bounds: x=[5990285, 6175052] ft, y=[1932560, 2189415] ft.
Fields: id (str), Street, mall_name (str), city (str).
"""

from alidade.models import Label, Layer, SingleSymbol, SvgMarker, Symbol

malls = Layer(
    id="mall_points",
    name="Big Bucks Malls",
    type="vector",
    source="./data/malls.shp",
    provider="ogr",
    crs="EPSG:2227",
    geometry_type="Point",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="marker",
            layers=[
                SvgMarker(
                    name="data/mall.svg",
                    color="230,120,0,255",
                    outline_color="160,84,0,255",
                    outline_width=0.0,
                    size=5.0,
                )
            ],
        )
    ),
    label=Label(field="mall_name"),
)
