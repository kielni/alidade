from alidade.models import Layer, SimpleLine, SingleSymbol, Symbol

# California major road network, EPSG:2227 (NAD83 / CA zone 3, US survey feet).
# 11,201 segments (11,171 LineString + 30 MultiLineString), STATEFIPS=06 only.
#
# Key fields:
#   HWYNAME    — primary name (e.g. "I 205", "STATE HWY 1", "CROSSTOWN FRWY")
#   ALT1_NAME  — alternate name (e.g. "I 580", "CABRILLO HWY")
#   LENGTH     — segment length in miles
#   FCC        — Census TIGER road class code:
#                  A11 (315)  Interstate highway
#                  A20 (210)  US highway without limited access
#                  A21 (174)  State route without limited access
#                  A30 (5096) Secondary/county road
#                  A31 (1260) Connecting road
#                  A60 (379)  Local service road
#                  A63 (3633) Rural route
#                  A1x/A15    Other limited-access / primary highways
roads = Layer(
    id="roads",
    name="Roads",
    type="vector",
    source="./data/roads.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=False,
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
