from pathlib import Path

import geopandas as gpd

from alidade.models import (
    Layer,
    ProcessingStep,
    PythonAction,
    SimpleLine,
    SingleSymbol,
    Symbol,
)

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


def filter_major_roads(src: Path, output: Path) -> None:
    gdf = gpd.read_file(src)
    gdf[gdf["FCC"].isin(_FCC_MAJOR)].to_file(output)


major_roads = Layer(
    id="major_roads",
    name="Major Roads",
    type="vector",
    source="./output/major_roads.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=True,
    geometry_type="LineString",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="line",
            layers=[
                SimpleLine(
                    line_color="30,30,30,255",
                    line_width=1.0,
                )
            ],
        )
    ),
    processing_step=ProcessingStep(
        description="Filter roads to primary/major highway FCC codes A10–A21.",
        action=PythonAction(fn=filter_major_roads),
        depends_on=["roads"],
        output=Path("output/major_roads.shp"),
    ),
)
