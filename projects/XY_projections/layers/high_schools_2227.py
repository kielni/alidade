import geopandas as gpd
import pandas as pd

from alidade.models import BoundLayer, Layer, PythonAction
from projects.XY_projections.layers.high_schools import high_schools


def _reproject(layer: BoundLayer) -> None:
    (src,) = layer.inputs
    df = pd.read_csv(src.path)
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["Longitude"], df["Latitude"]),
        crs="EPSG:4326",
    )
    gdf.to_crs("EPSG:2227").to_file(layer.path)


high_schools_2227 = Layer(
    id="high_schools_2227",
    name="High Schools 2227",
    type="vector",
    inputs=[high_schools],
    datasource="data/high_schools_2227.shp|layername=high_schools_2227",
    provider="ogr",
    crs="EPSG:2227",
    geometry_type="Point",
    visible=True,
    style_xml=None,
    action=PythonAction(fn=_reproject),
)
