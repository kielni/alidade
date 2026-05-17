from pathlib import Path

import geopandas as gpd
import numpy as np
from shapely.geometry import MultiPoint
from shapely.ops import voronoi_diagram

from projects.lab4.util import MALL_BUCKET_COLORS
from alidade.models import (
    Layer,
    ProcessingStep,
    PythonAction,
    Rule,
    RuleRenderer,
    SimpleFill,
    Symbol,
)

"""
Create output/mall_buffer_people.shp with one row per mall. Geometry is
the Voronoi cell (draw zone) clipped to each mall's 5-mile buffer.
Population is area-weighted from target census tracts (pct_m22_39 > 20%),
so each person is counted toward exactly one mall, the nearest one within 5 miles.

Fields: mall_id, mall_name, m22_39, bucket, geometry.
bucket is 0/1/2 (good/better/best) via equal-count breaks.

A Voronoi diagram partitions space based on proximity to a set of points. Given mall
locations, draw boundaries so that every spot on the map gets assigned to its nearest
store.
For any two stores, draw the perpendicular bisector of the line connecting them: the
line where every point is exactly equidistant from both stores. On one side, you're
closer to store A; on the other, closer to store B.
Do this for every pair of stores, and the bisectors intersect to form polygons.
Each polygon (a "Voronoi cell") contains exactly one store, and every point inside that
cell is closer to that store than to any other.
"""


def _symbol(rgb: str, outline_width: float) -> Symbol:
    return Symbol(
        type="fill",
        layers=[
            SimpleFill(
                color=f"{rgb},40",
                outline_color=f"{rgb},255",
                outline_width=outline_width,
            )
        ],
    )


_SYMBOLS = [
    _symbol(MALL_BUCKET_COLORS[0], 0.5),
    _symbol(MALL_BUCKET_COLORS[1], 0.75),
    _symbol(MALL_BUCKET_COLORS[2], 1.0),
]


def _build_draw_zones(buffers_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Return one polygon per mall: Voronoi cell intersected with that mall's buffer.

    Mall points are derived from buffer centroids (exact for circular buffers
    in a projected CRS), so only mall_buffers is needed as an input.
    """
    centroids = buffers_gdf[["mall_id", "mall_name"]].copy()
    centroids["geometry"] = buffers_gdf.geometry.centroid
    centroids_gdf = gpd.GeoDataFrame(centroids, crs=buffers_gdf.crs)

    points = MultiPoint(list(centroids_gdf.geometry))  # type: ignore[arg-type]
    envelope = buffers_gdf.geometry.union_all()
    regions = voronoi_diagram(points, envelope=envelope)

    voronoi_gdf = gpd.GeoDataFrame(geometry=list(regions.geoms), crs=buffers_gdf.crs)
    # Assign each Voronoi polygon to its nearest mall centroid.
    assigned = gpd.sjoin_nearest(
        voronoi_gdf,
        centroids_gdf,
        how="left",
    ).drop(columns=["index_right"])

    # Clip each Voronoi cell to its own 5-mile buffer.
    buf_geom = buffers_gdf.set_index("mall_id")["geometry"]
    clipped_geoms = [
        row.geometry.intersection(buf_geom[row.mall_id])
        for _, row in assigned.iterrows()
    ]
    result = assigned.copy()
    result["geometry"] = clipped_geoms
    result = result[~result.geometry.is_empty].reset_index(drop=True)
    return result[["mall_id", "mall_name", "geometry"]]


def aggregate_deduped(buffers: Path, tracts: Path, output: Path) -> None:
    # load buffer zones for malls
    buffers_gdf = gpd.read_file(buffers)[["id", "mall_name", "geometry"]].rename(
        columns={"id": "mall_id"}
    )
    # load target tracts with M22_39 population
    tracts_gdf = gpd.read_file(tracts)[["GEOID", "M22_39", "geometry"]]
    print(f"  buffers: {len(buffers_gdf)} rows, CRS={buffers_gdf.crs}")
    print(f"  tracts: {len(tracts_gdf)} rows")

    draw_zones = _build_draw_zones(buffers_gdf)
    print(f"  draw zones: {len(draw_zones)} rows")

    # Area-weighted overlay: split tracts by draw zone, prorate M22_39 by area.
    tracts_gdf["tract_area"] = tracts_gdf.geometry.area
    fragments = gpd.overlay(draw_zones, tracts_gdf, how="intersection")
    fragments["target_population"] = (
        fragments["M22_39"] * fragments.geometry.area / fragments["tract_area"]
    )

    totals = (
        fragments.groupby("mall_id")["target_population"]
        .sum()
        .reset_index()
        .rename(columns={"target_population": "m22_39"})
    )

    vals = totals["m22_39"]
    p33 = float(np.percentile(vals, 100 / 3))
    p67 = float(np.percentile(vals, 200 / 3))
    totals["bucket"] = 2
    totals.loc[totals["m22_39"] <= p67, "bucket"] = 1
    totals.loc[totals["m22_39"] <= p33, "bucket"] = 0
    print(f"  deduped_people breaks: good ≤ {p33:,.0f}, better ≤ {p67:,.0f}")

    result = draw_zones.merge(totals, on="mall_id", how="inner")
    result[["mall_id", "mall_name", "m22_39", "bucket", "geometry"]].to_file(output)


mall_people_deduped = Layer(
    id="mall_people_deduped",
    name="Mall Draw Zones",
    type="vector",
    source="./output/mall_people_deduped.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=True,
    geometry_type="Polygon",
    renderer=RuleRenderer(
        rules_key="r",
        rules=[
            Rule(key="r0", label="Good", filter='"bucket" = 0', symbol_index=0),
            Rule(key="r1", label="Better", filter='"bucket" = 1', symbol_index=1),
            Rule(key="r2", label="Best", filter='"bucket" = 2', symbol_index=2),
        ],
        symbols=_SYMBOLS,
    ),
    processing_step=ProcessingStep(
        description=(
            "Build Voronoi draw zones (Voronoi cell ∩ 5-mile buffer) for each"
            " mall; area-weight M22_39 from target tracts across zone boundaries;"
            " assign equal-count bucket (0/1/2)."
        ),
        action=PythonAction(fn=aggregate_deduped),
        depends_on=["mall_buffers", "target_tracts"],
        output=Path("output/mall_people_deduped.shp"),
    ),
)

if __name__ == "__main__":
    _proj = Path(__file__).parent.parent / "output"
    aggregate_deduped(
        _proj / "mall_buffers.shp",
        _proj / "target_tracts.shp",
        _proj / "mall_people_deduped.shp",
    )
