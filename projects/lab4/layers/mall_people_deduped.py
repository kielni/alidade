"""Voronoi draw zones clipped to each mall's 5-mile buffer.

One row per mall. Population is area-weighted from target census tracts
(pct_m22_39 > 20%), so each person is counted toward exactly one mall —
the nearest one within 5 miles.

Voronoi cells: for each pair of mall points, the perpendicular bisector of
the segment between them divides space into two half-planes; every location
on one side is closer to one mall, the other side to the other. The full set
of bisectors intersects to form one convex polygon (cell) per mall point.
Each cell is clipped to its own 5-mile buffer so remote areas don't inflate
the count.
"""

import geopandas as gpd
import numpy as np
from shapely.geometry import MultiPoint
from shapely.ops import voronoi_diagram

from alidade.models import (
    BoundLayer,
    Layer,
    PythonAction,
    Rule,
    RuleRenderer,
    SimpleFill,
    Symbol,
)
from projects.lab4.layers.mall_buffers import mall_buffers
from projects.lab4.layers.target_tracts import target_tracts
from projects.lab4.util import MALL_BUCKET_COLORS


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
    assigned = gpd.sjoin_nearest(
        voronoi_gdf,
        centroids_gdf,
        how="left",
    ).drop(columns=["index_right"])

    buf_geom = buffers_gdf.set_index("mall_id")["geometry"]
    clipped_geoms = [
        row.geometry.intersection(buf_geom[row.mall_id])
        for _, row in assigned.iterrows()
    ]
    result = assigned.copy()
    result["geometry"] = clipped_geoms
    result = result[~result.geometry.is_empty].reset_index(drop=True)
    return result[["mall_id", "mall_name", "geometry"]]


def aggregate_deduped(layer: BoundLayer) -> None:
    buffers_layer, tracts_layer = layer.inputs
    buffers_gdf = gpd.read_file(buffers_layer.path)[
        ["id", "mall_name", "geometry"]
    ].rename(columns={"id": "mall_id"})
    tracts_gdf = gpd.read_file(tracts_layer.path)[["GEOID", "M22_39", "geometry"]]
    print(f"  buffers: {len(buffers_gdf)} rows, CRS={buffers_gdf.crs}")
    print(f"  tracts: {len(tracts_gdf)} rows")

    draw_zones = _build_draw_zones(buffers_gdf)
    print(f"  draw zones: {len(draw_zones)} rows")

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
    result[["mall_id", "mall_name", "m22_39", "bucket", "geometry"]].to_file(layer.path)


mall_people_deduped = Layer(
    id="mall_people_deduped",
    name="Mall Draw Zones",
    type="vector",
    inputs=[mall_buffers, target_tracts],
    datasource="output/mall_people_deduped.shp",
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
    action=PythonAction(fn=aggregate_deduped),
)
