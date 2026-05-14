from pathlib import Path

import geopandas as gpd

from models import Layer, ProcessingStep, PythonAction, SimpleFill, SingleSymbol, Symbol


def filter_capitol_buffers_near_parks(
    buffers_path: Path, parks_path: Path, output: Path
) -> None:
    buffers = gpd.read_file(buffers_path)
    parks = gpd.read_file(parks_path)
    joined = gpd.sjoin(
        buffers, parks[["geometry"]], how="inner", predicate="intersects"
    )
    result = buffers.loc[joined.index.unique()]
    result.to_file(output)
    print(
        f"State capitols with 25-mile buffer intersecting a national park:"
        f" {len(result)}"
    )


capitol_parks_intersect = Layer(
    id="capitol_parks_intersect",
    name="Capitol Buffers Intersecting National Parks",
    type="vector",
    source="./output/capitol_parks_intersect.shp",
    provider="ogr",
    crs="EPSG:3857",
    visible=True,
    geometry_type="Polygon",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            layers=[
                SimpleFill(
                    color="255,160,50,110",
                    outline_color="200,90,0,255",
                    outline_width=1.0,
                )
            ],
        )
    ),
    processing_step=ProcessingStep(
        description=(
            "Filter 25-mile capitol buffers to those intersecting at least one"
            " national park polygon; print count to stdout."
        ),
        action=PythonAction(fn=filter_capitol_buffers_near_parks),
        depends_on=["capitol_buffer", "national_parks"],
        output=Path("output/capitol_parks_intersect.shp"),
    ),
)
