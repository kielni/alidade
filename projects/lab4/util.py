from pathlib import Path

import geopandas as gpd

# Shared palette for Lab 4 map layers.

# ColorBrewer 5-class Purples (light → dark = low → high), 60% fill opacity.
# Used by census_tracts (M22_39 count) and target_tracts (pct_m22_39).
CENSUS_BUCKETS = [
    "242,240,247,153",  # #f2f0f7 — class 1 (lowest)
    "203,201,226,153",  # #cbc9e2 — class 2
    "158,154,200,153",  # #9e9ac8 — class 3
    "117,107,177,153",  # #756bb1 — class 4
    "84,39,143,153",  # #54278f  — class 5 (highest)
]

# Dark purple outline for CENSUS_BUCKETS layers; matches palette hue.
CENSUS_OUTLINE = "63,0,125,255"  # darker than class 5, full opacity

# ColorBrewer YlGnBu 3-class (light → dark = good → best).
# Used by mall_buffer_people and mall_voronoi_people.
MALL_BUCKET_COLORS = [
    "161,218,180",  # #a1dab4 — good
    "65,182,196",  # #41b6c4 — better
    "34,94,168",  # #225ea8 — best
]

_PROJECT_DIR = Path(__file__).parent


def generate_summary() -> gpd.GeoDataFrame:
    """Return mall summary sorted by Voronoi young men descending.

    Columns: mall_id, mall_name, total_pop, m22_39_buf, m22_39_vor.
    """
    buffers = gpd.read_file(_PROJECT_DIR / "output/mall_buffers.shp")[
        ["id", "mall_name", "geometry"]
    ].rename(columns={"id": "mall_id"})
    buf_people = gpd.read_file(_PROJECT_DIR / "output/mall_buffer_people.shp")[
        ["mall_id", "m22_39_tot"]
    ].rename(columns={"m22_39_tot": "m22_39_buf"})
    deduped = gpd.read_file(_PROJECT_DIR / "output/mall_people_deduped.shp")[
        ["mall_id", "m22_39"]
    ].rename(columns={"m22_39": "m22_39_vor"})
    census = gpd.read_file(_PROJECT_DIR / "output/census_tracts.shp")[
        ["Total", "geometry"]
    ]

    joined = gpd.sjoin(
        census, buffers[["mall_id", "geometry"]], how="inner", predicate="intersects"
    )
    total_pop = (
        joined.groupby("mall_id")["Total"]
        .sum()
        .reset_index()
        .rename(columns={"Total": "total_pop"})
    )

    return (
        buffers[["mall_id", "mall_name"]]
        .merge(total_pop, on="mall_id", how="left")
        .merge(buf_people, on="mall_id", how="left")
        .merge(deduped, on="mall_id", how="left")
        .fillna(0)
        .sort_values("m22_39_vor", ascending=False)
    )
