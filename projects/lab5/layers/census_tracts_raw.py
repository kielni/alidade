"""M22_39yrs: 1620 Census tract polygons, EPSG:2227.

Source: FileGDB dataset in lab5_win.gdb (data/M22_39yrs.shp on disk).
Key fields: NAMELSAD (tract name, e.g. "Census Tract 4001"), GEOID,
Total (total population), M22_39 (males 22-39 count), ALandSqMi,
race breakdown fields (White, Black, AmIndian_A, Asian, etc.).

Includes tracts with Total = 0; use census_tracts for analysis.
"""

from alidade.models import Layer

census_tracts_raw = Layer(
    id="census_tracts_raw",
    name="Census Tracts (raw)",
    type="vector",
    datasource="data/M22_39yrs.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=False,
    geometry_type="Polygon",
)
