"""
Staging area rankings by distance-decay scoring against target zones.

For each staging point, score = sum(patch_score / distance) over High and Very
high patches (class >= 3 only). Low and Moderate patches are excluded so that
marginal terrain fragments do not inflate scores for staging areas that lack
access to genuinely high-priority grazing zones. Rank 1 = highest score (best).
Style: ColorBrewer YlGn 3-class — dark green = best, mid green = second,
pale yellow = other.
"""

import geopandas as gpd

from alidade.models import (
    BoundLayer,
    Layer,
    PythonAction,
    Rule,
    RuleRenderer,
    SimpleMarker,
    Symbol,
)
from projects.goats.layers.target_zones import target_zones as patches
from projects.goats.layers.staging import staging
from projects.goats.palette import STAGING_RANK_TIERS
from projects.goats.util import CRS

# YlGn 3-class, saturated — darker green = better
RANK_TIERS = [
    ("rank1", "Best", '"rank" = 1', STAGING_RANK_TIERS[0]),
    ("rank2", "Better", '"rank" = 2', STAGING_RANK_TIERS[1]),
    ("rank3", "Good", '"rank" >= 3', STAGING_RANK_TIERS[2]),
]

# Clamp patch distance so patches inside a staging lot don't contribute
# disproportionately to the score
MIN_PATCH_DISTANCE_M = 50.0


def build_staging_ranked(layer: BoundLayer) -> None:
    """Score each staging point by distance-decay sum over grazeable patches."""
    patches_layer, staging_layer = layer.inputs

    pts = gpd.read_file(staging_layer.path).to_crs(CRS)
    patch_gdf = gpd.read_file(patches_layer.path).to_crs(CRS)

    # Only High and Very high patches drive ranking; class 1-2 fragments are
    # too marginal to meaningfully differentiate staging area access
    patch_gdf = patch_gdf[patch_gdf["patch_class"] >= 3].copy()

    patch_scores = patch_gdf["patch_score"].to_numpy(dtype=float)

    scores = []
    for _, row in pts.iterrows():
        distances = (
            patch_gdf.geometry.distance(row.geometry)
            .clip(lower=MIN_PATCH_DISTANCE_M)
            .to_numpy(dtype=float)
        )
        scores.append(float((patch_scores / distances).sum()))

    pts["score"] = scores
    max_score = float(pts["score"].max())
    pts["score_norm"] = (pts["score"] / max_score).round(3) if max_score > 0 else 0.0
    pts["rank"] = pts["score"].rank(ascending=False, method="min").astype(int)

    for _, row in pts.sort_values("rank").iterrows():
        name = row.get("name", "—")
        print(
            f"  #{int(row['rank'])} {name}  "
            f"score={row['score_norm']:.3f}  "
            f"raw={row['score']:.4f}"
        )

    pts.to_file(layer.path, driver="GPKG")


_rules = [
    Rule(key=key, label=label, filter=filt, symbol_index=i)
    for i, (key, label, filt, _) in enumerate(RANK_TIERS)
]

_symbols = [
    Symbol(
        type="marker",
        layers=[
            SimpleMarker(name="diamond", color=color, outline_color=color, size=4.0)
        ],
    )
    for _, _, _, color in RANK_TIERS
]

staging_ranked = Layer(
    id="staging_ranked",
    name="Staging Area Ranking",
    type="vector",
    inputs=[patches, staging],
    datasource="output/staging_ranked.gpkg",
    crs=CRS,
    geometry_type="Point",
    renderer=RuleRenderer(
        rules_key="rank",
        rules=_rules,
        symbols=_symbols,
    ),
    action=PythonAction(fn=build_staging_ranked),
)
