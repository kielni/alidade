import geopandas as gpd

from alidade.models import (
    BoundLayer,
    GraduatedRange,
    GraduatedRenderer,
    Layer,
    PythonAction,
)
from projects.lab4.layers.census_tracts_raw import census_tracts_raw
from projects.lab4.util import CENSUS_BUCKETS, CENSUS_OUTLINE

# Jenks natural breaks on M22_39 (tracts with Total > 0, n=1,617):
#   counts: 561, 594, 367, 91, 7
_MIN = 0.0
_B1 = 424.0
_B2 = 740.0
_B3 = 1162.0
_B4 = 2003.0
_MAX = 2973.0


def filter_nonzero_population(layer: BoundLayer) -> None:
    (src,) = layer.inputs
    gdf = gpd.read_file(src.path)
    gdf[gdf["Total"] > 0].to_file(layer.path)


census_tracts = Layer(
    id="census_tracts",
    name="Census Tracts",
    type="vector",
    inputs=[census_tracts_raw],
    datasource="output/census_tracts.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=True,
    geometry_type="Polygon",
    renderer=GraduatedRenderer(
        attr="M22_39",
        ranges=[
            GraduatedRange(
                lower=_MIN,
                upper=_B1,
                label=f"{_MIN:.0f} – {_B1:.0f}",
                color=CENSUS_BUCKETS[0],
            ),
            GraduatedRange(
                lower=_B1,
                upper=_B2,
                label=f"{_B1:.0f} – {_B2:.0f}",
                color=CENSUS_BUCKETS[1],
            ),
            GraduatedRange(
                lower=_B2,
                upper=_B3,
                label=f"{_B2:.0f} – {_B3:.0f}",
                color=CENSUS_BUCKETS[2],
            ),
            GraduatedRange(
                lower=_B3,
                upper=_B4,
                label=f"{_B3:.0f} – {_B4:.0f}",
                color=CENSUS_BUCKETS[3],
            ),
            GraduatedRange(
                lower=_B4,
                upper=_MAX,
                label=f"{_B4:.0f}+",
                color=CENSUS_BUCKETS[4],
            ),
        ],
        outline_color=CENSUS_OUTLINE,
        outline_width=0.1,
    ),
    action=PythonAction(fn=filter_nonzero_population),
)
