from pathlib import Path

import geopandas as gpd
import pandas as pd

from alidade.models import Layer, ProcessingStep, PythonAction


def _reproject(csv_path: Path, output: Path) -> None:
    df = pd.read_csv(csv_path)
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["Longitude"], df["Latitude"]),
        crs="EPSG:4326",
    )
    gdf.to_crs("EPSG:2227").to_file(output)


high_schools_2227 = Layer(
    id="high_schools_2227",
    name="High Schools 2227",
    type="vector",
    source="data/high_schools_2227.shp|layername=high_schools_2227",
    provider="ogr",
    crs="EPSG:2227",
    geometry_type="Point",
    visible=True,
    style_xml=None,
    processing_step=ProcessingStep(
        description="Reproject high schools CSV from EPSG:4326 to EPSG:2227",
        action=PythonAction(fn=_reproject),
        depends_on=["high_schools"],
        output=Path("data/high_schools_2227.shp"),
    ),
)
