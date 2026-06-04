"""UC and CSU campus point locations, reprojected from EPSG:4326 to EPSG:2227.

Source: UCandCSU_XY.txt — 6 UC and CSU campuses with WGS 84 coordinates.

Icon: data/cap.svg — graduation cap (FreeSVG.org, CC0).
The SVG uses hardcoded fill colors rather than param(fill)/param(outline),
so SvgMarker color fields do not recolor it; the icon renders black on
transparent as-is.
"""

import geopandas as gpd
import pandas as pd

from alidade.models import (
    BoundLayer,
    Label,
    Layer,
    PythonAction,
    SingleSymbol,
    SvgMarker,
    Symbol,
)
from projects.midterm.layers.uc_and_csu_raw import uc_and_csu_raw


def _reproject(layer: BoundLayer) -> None:
    (src,) = layer.inputs
    # Comma+tab delimiter; sep regex handles the mixed whitespace.
    df = pd.read_csv(src.path, sep=r",\s*", engine="python")
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326",
    )
    gdf.to_crs("EPSG:2227").to_file(layer.path)


uc_and_csu = Layer(
    id="uc_and_csu_points",
    name="UC and CSU Campuses",
    type="vector",
    inputs=[uc_and_csu_raw],
    datasource="output/uc_and_csu.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=True,
    geometry_type="Point",
    label=Label(field="school", color="0,0,0,255"),
    renderer=SingleSymbol(
        symbol=Symbol(
            type="marker",
            layers=[
                SvgMarker(
                    name="data/cap.svg",
                    size=5.0,
                    color="0,0,0,255",
                    outline_color="0,0,0,0",
                )
            ],
        )
    ),
    action=PythonAction(fn=_reproject),
)
