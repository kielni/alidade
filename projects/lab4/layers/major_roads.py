import geopandas as gpd

from alidade.models import (
    BoundLayer,
    Layer,
    PythonAction,
    SimpleLine,
    SingleSymbol,
    Symbol,
)
from projects.lab4.layers.roads import roads

# Census TIGER FCC codes for primary/major highways (limited and unlimited access).
# A14, A17, A18 are included per spec but absent from this dataset.
_FCC_MAJOR = {
    "A10",
    "A11",
    "A12",
    "A13",
    "A14",
    "A15",
    "A16",
    "A17",
    "A18",
    "A20",
    "A21",
}


def filter_major_roads(layer: BoundLayer) -> None:
    (src,) = layer.inputs
    gdf = gpd.read_file(src.path)
    gdf[gdf["FCC"].isin(_FCC_MAJOR)].to_file(layer.path)


major_roads = Layer(
    id="major_roads",
    name="Major Roads",
    type="vector",
    inputs=[roads],
    datasource="output/major_roads.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=True,
    geometry_type="LineString",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="line",
            layers=[
                SimpleLine(
                    line_color="220,210,180,255",
                    line_width=0.6,
                )
            ],
        )
    ),
    action=PythonAction(fn=filter_major_roads),
)
