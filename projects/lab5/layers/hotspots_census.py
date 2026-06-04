"""Getis-Ord Gi* hot spot analysis on M22_39 (males 22-39 count).

Source: output/hotspots_census.shp (generated from output/census_tracts.shp).

Method replicates ArcGIS Pro Optimized Hot Spot Analysis:
  - Locational outliers excluded from distance band calculation
  - Optimal fixed distance band via Incremental Spatial Autocorrelation
  - Gi* formula: esda.G_Local, binary weights, star=True
  - FDR correction: Benjamini-Hochberg via statsmodels

Output fields: GiZScore, GiPValue, Gi_Bin, NNeighbors
"""

import geopandas as gpd

from alidade.models import BoundLayer, Layer, PythonAction
from projects.lab5.layers.census_tracts import census_tracts
from projects.lab5.util import (
    compute_distance_band,
    find_locational_outliers,
    hotspot_renderer,
    run_gistar,
)

_VALUE_COL = "M22_39"


def compute_hot_spots(layer: BoundLayer) -> None:
    (src,) = layer.inputs
    gdf = gpd.read_file(src.path)

    print(f"Input features: {len(gdf)}")
    outlier_mask = find_locational_outliers(gdf)
    print(f"Locational outliers: {int(outlier_mask.sum())}")

    distance_band = compute_distance_band(gdf, outlier_mask, _VALUE_COL)
    units = gdf.crs.axis_info[0].unit_name if gdf.crs else "units"
    print(f"Distance band: {distance_band:.4f} {units}")

    result = run_gistar(gdf, distance_band, _VALUE_COL)
    print(f"Significant features after FDR: {int((result['Gi_Bin'] != 0).sum())}")

    result.to_file(layer.path)


hotspots_census = Layer(
    id="hotspots_census",
    name="Hot Spot Analysis (M22_39)",
    type="vector",
    inputs=[census_tracts],
    datasource="output/hotspots_census.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=True,
    geometry_type="Polygon",
    renderer=hotspot_renderer(),
    action=PythonAction(fn=compute_hot_spots),
)
