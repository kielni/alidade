"""
Staging area quality score: total suitability within 1-mile deployment zone.

## Approach

The full park (3859 m × 2.4 mi wide; 1754 m × 1.1 mi tall) is entirely
reachable over a 1-week engagement — no staging area is too far from any part
of the park. Within that constraint, the **1-mile buffer (1609 m)** around each
staging point captures the zone of highest grazing intensity: the area goats
will cover first and most thoroughly before ranging further.

For each staging point, compute:

    suit_sum   = Σ suitability pixel values within 1-mile buffer (nodata=0 excluded)
    suit_mean  = mean suitability of non-excluded pixels within buffer
    score      = suit_sum / max(suit_sum across all staging points)  [0–1]
    rank       = 1 = best

`suit_sum` is the primary ranking metric: it rewards staging areas that have
both many high-suitability pixels AND high class values nearby.

## Implementation

Uses rasterstats.zonal_stats — handles raster/vector intersection and pixel
accumulation without manual rasterio iteration.

## Output

output/staging_scored.gpkg — staging points with suit_sum, suit_mean,
suit_count, score (0–1), rank columns; symbolised by rank tier.
"""

import geopandas as gpd
from rasterstats import zonal_stats

from alidade.models import (
    BoundLayer,
    Layer,
    PythonAction,
    Rule,
    RuleRenderer,
    SimpleMarker,
    Symbol,
)
from projects.goats.layers.staging import staging
from projects.goats.layers.suitability import suitability
from projects.goats.palette import TARGET_RANK_TIERS
from projects.goats.util import CRS

BUFFER_M = 804.672  # 0.5 mile

# (key, label, filter, color) — RdYlBu diverging: red = best, blue = least good
_RANK_TIERS = [
    ("travel1", "Best", '"rank" = 1', TARGET_RANK_TIERS[0]),
    ("travel2", "Second", '"rank" = 2', TARGET_RANK_TIERS[1]),
    ("travel3", "Other", '"rank" >= 3', TARGET_RANK_TIERS[2]),
]


def build_targets(layer: BoundLayer) -> None:
    """Score each staging point by mean suitability within a 0.5-mile buffer."""
    staging_layer, suitability_layer = layer.inputs

    pts = gpd.read_file(staging_layer.path).to_crs(CRS)

    buffers = pts.copy()
    buffers.geometry = pts.geometry.buffer(BUFFER_M)

    stats = zonal_stats(
        buffers,
        str(suitability_layer.path),
        stats=["sum", "mean", "count"],
        nodata=0,
    )

    pts["suit_sum"] = [float(s.get("sum") or 0.0) for s in stats]
    pts["suit_mean"] = [float(s.get("mean") or 0.0) for s in stats]
    pts["suit_count"] = [int(s.get("count") or 0) for s in stats]

    max_mean = float(pts["suit_mean"].max())
    pts["score"] = (pts["suit_mean"] / max_mean).round(3) if max_mean > 0 else 0.0
    pts["rank"] = pts["score"].rank(ascending=False, method="min").astype(int)

    for _, row in pts.sort_values("rank").iterrows():
        name = row.get("name", "—")
        print(
            f"  #{int(row['rank'])} {name}  "
            f"score={row['score']:.3f}  "
            f"sum={row['suit_sum']:.0f}  "
            f"mean={row['suit_mean']:.2f}  "
            f"count={int(row['suit_count'])}"
        )

    pts.to_file(layer.path, driver="GPKG")


_rules = [
    Rule(key=key, label=label, filter=filt, symbol_index=i)
    for i, (key, label, filt, _) in enumerate(_RANK_TIERS)
]

_symbols = [
    Symbol(
        type="marker",
        layers=[SimpleMarker(outline_color=color, color=color, size=3.0)],
    )
    for _, _, _, color in _RANK_TIERS
]

targets = Layer(
    id="staging_targets",
    name="Staging Area Scores",
    type="vector",
    inputs=[staging, suitability],
    datasource="output/staging_scored.gpkg",
    provider="ogr",
    crs=CRS,
    visible=True,
    geometry_type="Point",
    renderer=RuleRenderer(
        rules_key="travel",
        rules=_rules,
        symbols=_symbols,
    ),
    action=PythonAction(fn=build_targets),
)
