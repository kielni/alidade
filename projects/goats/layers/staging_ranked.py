"""
Staging area rankings by distance-decay scoring against grazeable patches.

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
from projects.goats.layers.patches import patches
from projects.goats.layers.staging import staging
from projects.goats.util import CRS

# ColorBrewer YlGn 3-class — darker green = better
_RANK_TIERS = [
    ("rank1", "Best", '"rank" = 1', "49,163,84,255"),
    ("rank2", "Better", '"rank" = 2', "173,221,142,255"),
    ("rank3", "Good", '"rank" >= 3', "247,252,185,255"),
]


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
        # Clamp at 50 m so patches closer than that contribute equally —
        # exact proximity to a patch edge should not dominate the score
        distances = (
            patch_gdf.geometry.distance(row.geometry)
            .clip(lower=50.0)
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
    for i, (key, label, filt, _) in enumerate(_RANK_TIERS)
]

_symbols = [
    Symbol(
        type="marker",
        layers=[SimpleMarker(color=color, outline_color=color, size=3.0)],
    )
    for _, _, _, color in _RANK_TIERS
]

staging_ranked = Layer(
    id="staging_ranked",
    name="Staging Area Ranking",
    type="vector",
    inputs=[patches, staging],
    datasource="output/staging_ranked.gpkg",
    provider="ogr",
    crs=CRS,
    visible=True,
    geometry_type="Point",
    renderer=RuleRenderer(
        rules_key="rank",
        rules=_rules,
        symbols=_symbols,
    ),
    action=PythonAction(fn=build_staging_ranked),
)
