from pathlib import Path

import geopandas as gpd
import pandas as pd

from alidade import project_data_dir
from alidade.models import (
    Layer,
    ProcessingStep,
    PythonAction,
    SimpleFill,
    SingleSymbol,
    Symbol,
)

# output/mall_buffers.shp: 5-mile buffer polygons around each of the 11 mall
# points, joined with mall_names.csv on id. EPSG:2227 (US survey feet);
# 5 miles = 26,400 survey feet. Fields: id, name, city, mall_name.
_BUFFER_FT = 5 * 5280
_CSV = project_data_dir(__file__) / "mall_names.csv"


def buffer_malls(src: Path, output: Path) -> None:
    gdf = gpd.read_file(src)
    gdf = gdf.copy()
    gdf["geometry"] = gdf.geometry.buffer(_BUFFER_FT)

    names = pd.read_csv(_CSV, encoding="utf-8-sig")
    names["ID"] = names["ID"].astype(str)
    names = names[["ID", "MallName"]].rename(
        columns={"ID": "id", "MallName": "mall_name"}
    )
    gdf = gdf.merge(names, on="id", how="left")
    gdf.to_file(output)


mall_buffers = Layer(
    id="mall_buffers",
    name="Mall 5-Mile Buffers",
    type="vector",
    source="./output/mall_buffers.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=True,
    geometry_type="Polygon",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            layers=[
                SimpleFill(
                    color="144,238,144,128",
                    outline_color="80,160,80,255",
                    outline_width=0.5,
                )
            ],
        )
    ),
    processing_step=ProcessingStep(
        description=(
            "Buffer mall points by 5 miles (26,400 ft) in EPSG:2227;"
            " join mall_names.csv on id to add mall_name field."
        ),
        action=PythonAction(fn=buffer_malls),
        depends_on=["malls"],
        output=Path("output/mall_buffers.shp"),
    ),
)
