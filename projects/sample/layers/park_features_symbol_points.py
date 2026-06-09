from pathlib import Path

from alidade.color import Color
from alidade.models import Layer, Rule, RuleRenderer, SimpleMarker, SvgMarker, Symbol

_DARK_GRAY = Color.from_hex("#232323")

_renderer = RuleRenderer(
    rules_key="{bb04642b-f9da-4f52-8c90-270a8056b0ff}",
    rules=[
        Rule(
            key="{7fc325ed-e2de-4cff-a2f1-262229909fff}",
            label="parking",
            filter="\"symbol\" = 'parking'",
            symbol_index=0,
        ),
        Rule(
            key="{f6a95713-252a-45da-b62d-7a9430575dfb}",
            label="picnic",
            filter="\"symbol\" = 'picnic'",
            symbol_index=1,
        ),
        Rule(
            key="{b2d4f8a3-b727-4969-b0bd-cfd2ae17e769}",
            label="ranger station",
            filter="\"symbol\" = 'ranger station'",
            symbol_index=2,
        ),
        Rule(
            key="{ee7e2257-8cba-446a-a49a-1ad2b3413e81}",
            label="shelter",
            filter="\"symbol\" = 'shelter'",
            symbol_index=3,
        ),
        Rule(
            key="{e198d526-e4ab-404b-bcbe-dbad9eba2e2d}",
            label="stream",
            filter="\"symbol\" = 'stream'",
            symbol_index=4,
            active=False,
        ),
        Rule(
            key="{7feccf46-df16-454b-88bf-832515a6b9be}",
            label="toilets",
            filter="\"symbol\" = 'toilets'",
            symbol_index=5,
        ),
        Rule(
            key="{b1d42b8d-7d64-4335-99b9-a696ae0ac3fa}",
            filter="ELSE",
            symbol_index=6,
            active=False,
        ),
    ],
    symbols=[
        Symbol(
            type="marker",
            layers=[
                SvgMarker(
                    name="transportation (NRGS NPS Respository)/svg/parking_light.svg",
                    color=Color.from_hex("#4b4b4b"),
                    outline_color=Color.from_hex("#000000"),
                    outline_width=0.4,
                )
            ],
        ),
        Symbol(
            type="marker",
            layers=[
                SvgMarker(
                    name="camping (NRGS NPS Respository)/svg/picnic_area_light.svg",
                    color=Color.from_hex("#19c994"),
                    outline_color=_DARK_GRAY,
                )
            ],
        ),
        Symbol(
            type="marker",
            layers=[
                SvgMarker(
                    name="park_buildings (NRGS NPS Respository)/svg/ranger_light.svg",
                    color=Color.from_hex("#e664c1"),
                    outline_color=_DARK_GRAY,
                )
            ],
        ),
        Symbol(
            type="marker",
            layers=[
                SvgMarker(
                    name=(
                        "camping (NRGS NPS Respository)/svg/picnic_shelter_light.svg"
                    ),
                    color=Color.from_hex("#83afe5"),
                    outline_color=_DARK_GRAY,
                )
            ],
        ),
        Symbol(
            type="marker",
            layers=[
                SimpleMarker(
                    color=Color.from_hex("#6422c8"),
                    outline_color=_DARK_GRAY,
                )
            ],
        ),
        Symbol(
            type="marker",
            layers=[
                SvgMarker(
                    name="services (NRGS NPS Respository)/svg/restrooms_light.svg",
                    color=Color.from_hex("#6bdd57"),
                    outline_color=_DARK_GRAY,
                )
            ],
        ),
        Symbol(
            type="marker",
            layers=[
                SimpleMarker(
                    color=Color.from_hex("#e6e33c"),
                    outline_color=_DARK_GRAY,
                )
            ],
        ),
    ],
)

park_features_symbol_points = Layer(
    id="park_features_symbol_points",
    name="park_features_symbol",
    type="vector",
    datasource="data/park_features_symbol.geojson|geometrytype=Point",
    provider="ogr",
    crs="EPSG:4326",
    visible=True,
    style_xml=Path("styles/park_features_symbol_points.xml"),
    renderer=_renderer,
)
