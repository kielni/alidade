"""Intersection of income and census hot spots at 99% confidence (Gi_Bin=3).

Source:
  output/hotspots_income.shp  → filter Gi_Bin == 3
  output/hotspots_census.shp  → filter Gi_Bin == 3

Output: output/hotspots_overlap.shp — polygon intersection of both hot spot sets.
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd

from alidade.models import (
    BoundLayer,
    Layer,
    PythonAction,
    SimpleFill,
    SingleSymbol,
    Symbol,
)
from projects.lab5.layers.hotspots_census_arcgis import (
    hotspots_census as hotspots_census_arcgis,
)
from projects.lab5.layers.hotspots_income_arcgis import (
    hotspots_income as hotspots_income_arcgis,
)


def compute_overlap(layer: BoundLayer) -> None:
    income_layer, census_layer = layer.inputs
    income_hot = gpd.read_file(income_layer.path)
    income_hot = income_hot[income_hot["Gi_Bin"] == 3]

    census_hot = gpd.read_file(census_layer.path)
    census_hot = census_hot[census_hot["Gi_Bin"] == 3]

    print(f"Income hot spots (Gi_Bin=3): {len(income_hot)}")
    print(f"Census hot spots (Gi_Bin=3): {len(census_hot)}")

    overlap = gpd.overlay(
        income_hot[["geometry"]],
        census_hot[["geometry"]],
        how="intersection",
        keep_geom_type=True,
    )

    print(f"Overlap polygons: {len(overlap)}")
    overlap.to_file(layer.path)


hotspots_overlap = Layer(
    id="hotspots_overlap",
    name="Hot Spot Overlap (Income & M22_39)",
    type="vector",
    inputs=[hotspots_income_arcgis, hotspots_census_arcgis],
    datasource="output/hotspots_overlap.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=True,
    geometry_type="Polygon",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            layers=[
                SimpleFill(
                    color="255,127,0,200",
                    outline_color="180,60,0,255",
                    outline_width=0.5,
                )
            ],
        )
    ),
    action=PythonAction(fn=compute_overlap),
)


def print_targets() -> pd.DataFrame:
    """Rank mall buffers by M22_39 population in the hot spot overlap zone.

    Loads output/hotspots_overlap.shp, output/mall_buffers.shp, and
    data/HotSpotsYoungMen.shp (ArcGIS Gi_Bin==3 hot spots with M22_39).
    Area-weights M22_39 through two overlay passes so each mall buffer
    receives credit proportional to the census tract area it covers inside
    the overlap zone.

    Returns a DataFrame with columns: mall_name, city, m22_39, overlap_sqmi.
    """
    project_dir = Path(__file__).parent.parent

    overlap = gpd.read_file(project_dir / "output" / "hotspots_overlap.shp")
    buffers = gpd.read_file(project_dir / "output" / "mall_buffers.shp")
    young_men = gpd.read_file(project_dir / "data" / "HotSpotsYoungMen.shp")

    young_men_hot = young_men[young_men["Gi_Bin"] == 3][["M22_39", "geometry"]].copy()
    young_men_hot["tract_area"] = young_men_hot.geometry.area

    attributed = gpd.overlay(
        overlap[["geometry"]],
        young_men_hot,
        how="intersection",
        keep_geom_type=True,
    )

    buffers_sub = buffers[["mall_name", "city", "geometry"]].copy()
    per_mall = gpd.overlay(
        attributed, buffers_sub, how="intersection", keep_geom_type=True
    )
    per_mall["sub_area"] = per_mall.geometry.area
    per_mall["m22_in_buf"] = per_mall["M22_39"] * (
        per_mall["sub_area"] / per_mall["tract_area"]
    )

    result = (
        per_mall.groupby(["mall_name", "city"])
        .agg(m22_39=("m22_in_buf", "sum"), overlap_sqft=("sub_area", "sum"))
        .reset_index()
        .sort_values("m22_39", ascending=False)
        .reset_index(drop=True)
    )
    result["m22_39"] = result["m22_39"].round().astype(int)
    result["overlap_sqmi"] = (result["overlap_sqft"] / 5280**2).round(2)
    result = result.drop(columns=["overlap_sqft"])

    print(result.to_string(index=False))
    return result


if __name__ == "__main__":
    print_targets()
