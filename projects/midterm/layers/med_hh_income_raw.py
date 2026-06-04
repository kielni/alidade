"""Unfiltered Bay Area census tracts with median household income (ACS B19019).

Used only as the dependency source for med_hh_income so the build system
can pass the shapefile path to the filter function. Not displayed directly.

Key fields (DBF names truncated to 10 characters):
    GEOID      — 11-digit census tract FIPS code (e.g. "06001400100")
    NAMELSAD   — full name, e.g. "Census Tract 4001"
    MedianHH_i — median household income in dollars (truncated from
                 MedianHHIncome); the primary thematic field
    ALAND      — land area in square meters
    AWATER     — water area in square meters
    INTPTLAT   — internal point latitude (WGS 84)
    INTPTLON   — internal point longitude (WGS 84)
    Shape_Leng — perimeter length in geographic degrees (pre-projection)
    Shape_Area — area in geographic degrees² (pre-projection)
    OBJECTID_1, OBJECTID, OBJECTID_2 — duplicate ESRI object IDs
    Id         — duplicate of GEOID
"""

from alidade.models import Layer, SimpleFill, SingleSymbol, Symbol

med_hh_income_raw = Layer(
    id="med_hh_income_raw",
    name="Median Household Income (raw)",
    type="vector",
    datasource="data/B19019MedHHIncome.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=True,
    geometry_type="Polygon",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            layers=[
                SimpleFill(
                    color="0,0,0,0",
                    outline_color="0,0,0,255",
                    outline_width=0.1,
                )
            ],
        )
    ),
)
