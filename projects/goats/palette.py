"""Project color palette for goats / Alum Rock Park.

All layer files import named constants from here. No layer file should
construct a Color directly or use an inline string.
"""

from alidade.color import BLACK as _BLACK  # noqa: F401 — re-export for layers
from alidade.color import TRANSPARENT as _TRANSPARENT  # noqa: F401
from alidade.color import WHITE as _WHITE  # noqa: F401
from alidade.color import Color, brewer

# Re-export generic constants so layers import from one place.
BLACK = _BLACK
TRANSPARENT = _TRANSPARENT
WHITE = _WHITE

# ── Park boundary ──────────────────────────────────────────────────────────────

PARK_FILL = Color.from_hex("#ffffff")
PARK_BORDER = Color.from_hex("#6464c8", alpha=180)
PARK_BOUNDARY_EDGE = Color.from_hex("#404040")

# ── Water ──────────────────────────────────────────────────────────────────────

WATER_FILL = Color.from_hex("#4477aa")
WATER_FILL_SEMI = Color.from_hex("#4477aa", alpha=128)
WATER_EDGE = Color.from_hex("#285078", alpha=200)

# ── Developed / built environment ──────────────────────────────────────────────

DEVELOPED_FILL = Color.from_hex("#e34a33", alpha=160)
DEVELOPED_EDGE = Color.from_hex("#9e3322")

# ── Roads and trails ───────────────────────────────────────────────────────────

ROADS_LINE = Color.from_hex("#784828")

# ── Vegetation ─────────────────────────────────────────────────────────────────
# Matches VEGETATION_ZONES order in util.py.

VEG_SHRUB = Color.from_hex("#1a9850")
VEG_NON_NATIVE_HERB = Color.from_hex("#a6d96a")
VEG_HERBACEOUS = Color.from_hex("#fee08b")
VEG_NON_NATIVE_WOOD = Color.from_hex("#6b4f3a")
VEG_NATIVE_WOOD = Color.from_hex("#a8927a")
VEG_DEVELOPED = Color.from_hex("#595959")
VEG_RIPARIAN = Color.from_hex("#bdd7e7")
VEG_EDGE = Color(80, 80, 80, 120)

# ── Slope ──────────────────────────────────────────────────────────────────────
# RdYlGn-derived, matches slope classification thresholds.

SLOPE_GENTLE = Color.from_hex("#1a9641")
SLOPE_MODERATE = Color.from_hex("#ffffbf")
SLOPE_STEEP = Color.from_hex("#fdae61")
SLOPE_TOO_STEEP = Color.from_hex("#ddd0c0")

# ── Suitability, basins, and grazeable patches ─────────────────────────────────
# ColorBrewer Purples 4-class; index 0 = lowest suitability.

SUITABILITY = brewer("sequential.Purples", 4, alpha=200)

FEATURE_EDGE = Color(80, 80, 80)

# ── Staging areas ──────────────────────────────────────────────────────────────

STAGING_FILL = Color.from_hex("#b400ff")
STAGING_EDGE = Color.from_hex("#6e00a0")

# ── Priority areas ─────────────────────────────────────────────────────────────

PRIORITY_DEVELOPED_FILL = Color.from_hex("#f2a900", alpha=128)
PRIORITY_ROADS_FILL = Color.from_hex("#ffc800", alpha=128)

# ── Rank tiers ─────────────────────────────────────────────────────────────────

# YlGn 3-class — used in staging_ranked.py; index 0 = best.
STAGING_RANK_TIERS = [
    Color.from_hex("#00c83c"),
    Color.from_hex("#78e65a"),
    Color.from_hex("#e1ff50"),
]

# RdYlBu diverging — used in targets.py; index 0 = best.
TARGET_RANK_TIERS = [
    Color.from_hex("#d7191c"),
    Color.from_hex("#fdae61"),
    Color.from_hex("#2c7bb6"),
]
