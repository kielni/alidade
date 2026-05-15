from alidade.models import Layer, SimpleFill, SingleSymbol, Symbol

# ACS Sex by Age (table B01001) joined to California census tracts,
# projected to EPSG:2227 (NAD83 / California zone 3, US survey feet).
# 1,620 tracts covering the Bay Area / Central Valley region.
#
# Key fields:
#   NAMELSAD   — e.g. "Census Tract 4001" (legal/statistical area name)
#   GEOID      — 11-digit census tract FIPS code
#   Total      — total population per tract
#   M22_39     — derived count: males aged 22–39 (sum of ACS B01001 VD10–VD13)
#   HD01_VD*   — raw ACS B01001 Sex by Age columns (VD01=total … VD49)
#   White/Black/Asian/… — racial breakdown totals
#   ALandSqMi  — land area in square miles (ALAND / 2,589,988)
census_tracts_males_22_39 = Layer(
    id="census_tracts_males_22_39",
    name="Males Ages 22-39 (Census Tracts)",
    type="vector",
    source="./data/M22_39yrs.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=False,
    geometry_type="Polygon",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            layers=[
                SimpleFill(
                    color="200,120,50,180",
                    outline_color="120,60,0,255",
                )
            ],
        )
    ),
)
