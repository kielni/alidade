from pathlib import Path

import geopandas as gpd

from alidade.models import (
    Layer,
    ProcessingStep,
    PythonAction,
    SimpleFill,
    SingleSymbol,
    Symbol,
)


def _buffer(shp_path: Path, output: Path) -> None:
    gdf = gpd.read_file(shp_path)
    gdf.geometry = gdf.geometry.buffer(5280)
    gdf.to_file(output)


high_schools_buffer = Layer(
    id="high_schools_buffer",
    name="High Schools Buffer",
    type="vector",
    source="data/high_schools_buffer.shp|layername=high_schools_buffer",
    provider="ogr",
    crs="EPSG:2227",
    geometry_type="Polygon",
    visible=True,
    style_xml=None,
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            alpha=0.5,
            layers=[SimpleFill(color="64,128,255,255")],
        )
    ),
    processing_step=ProcessingStep(
        description="1-mile buffer around each high school point (EPSG:2227 ft)",
        action=PythonAction(fn=_buffer),
        depends_on=["high_schools_2227"],
        output=Path("data/high_schools_buffer.shp"),
    ),
)
