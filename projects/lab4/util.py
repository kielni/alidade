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
