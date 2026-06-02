from math import sqrt

import warnings

import geopandas as gpd
import libpysal
import numpy as np
import pandas as pd
from esda.getisord import G_Local
from esda.moran import Moran
from scipy.spatial import KDTree
from statsmodels.stats.multitest import multipletests

from alidade.models import GraduatedRange, GraduatedRenderer

# Shared ColorBrewer palettes for Lab 5 map layers, 60% fill opacity.

# 5-class Purples (light → dark = low → high).
PURPLES = [
    "242,240,247,153",  # #f2f0f7 — class 1 (lowest)
    "203,201,226,153",  # #cbc9e2 — class 2
    "158,154,200,153",  # #9e9ac8 — class 3
    "117,107,177,153",  # #756bb1 — class 4
    "84,39,143,153",  # #54278f  — class 5 (highest)
]

# Dark purple outline to complement Purples.
PURPLES_OUTLINE = "63,0,125,255"

# 5-class RdBu reversed (blue → cream → red = low → high).
RDBU_R = [
    "5,113,176,153",  # #0571b0 — class 1 (lowest)
    "146,197,222,153",  # #92c5de — class 2
    "247,247,247,153",  # #f7f7f7 — class 3 (cream midpoint)
    "244,165,130,153",  # #f4a582 — class 4
    "202,0,32,153",  # #ca0020  — class 5 (highest)
]

# Dark neutral outline to complement RdBu.
RDBU_R_OUTLINE = "60,60,60,255"

# ArcGIS Pro hot spot analysis color scheme, fully opaque.
HOTSPOT_COLD_99 = "0,92,230,255"
HOTSPOT_COLD_95 = "115,178,255,255"
HOTSPOT_COLD_90 = "215,230,252,255"
HOTSPOT_NS = "255,255,190,255"
HOTSPOT_HOT_90 = "255,210,162,255"
HOTSPOT_HOT_95 = "252,141,89,255"
HOTSPOT_HOT_99 = "215,48,31,255"
HOTSPOT_OUTLINE = "100,100,100,255"


def hotspot_renderer(attr: str = "Gi_Bin") -> GraduatedRenderer:
    """Return the standard ArcGIS Pro hot spot graduated renderer.

    Integer breakpoints -3…+3 on `attr` (default "Gi_Bin").
    """
    return GraduatedRenderer(
        attr=attr,
        ranges=[
            GraduatedRange(
                lower=-3,
                upper=-3,
                label="Cold Spot with 99% Confidence",
                color=HOTSPOT_COLD_99,
            ),
            GraduatedRange(
                lower=-3,
                upper=-2,
                label="Cold Spot with 95% Confidence",
                color=HOTSPOT_COLD_95,
            ),
            GraduatedRange(
                lower=-2,
                upper=-1,
                label="Cold Spot with 90% Confidence",
                color=HOTSPOT_COLD_90,
            ),
            GraduatedRange(
                lower=-1,
                upper=0,
                label="Not Significant",
                color=HOTSPOT_NS,
            ),
            GraduatedRange(
                lower=0,
                upper=1,
                label="Hot Spot with 90% Confidence",
                color=HOTSPOT_HOT_90,
            ),
            GraduatedRange(
                lower=1,
                upper=2,
                label="Hot Spot with 95% Confidence",
                color=HOTSPOT_HOT_95,
            ),
            GraduatedRange(
                lower=2,
                upper=3,
                label="Hot Spot with 99% Confidence",
                color=HOTSPOT_HOT_99,
            ),
        ],
        outline_color=HOTSPOT_OUTLINE,
        outline_width=0.1,
    )


def find_locational_outliers(gdf: gpd.GeoDataFrame) -> pd.Series:
    """Return boolean Series — True where a feature is a locational outlier.

    A feature is an outlier if its nearest-neighbor distance exceeds
    mean + 3 * std of all nearest-neighbor distances.
    """
    coords = np.column_stack([gdf.geometry.centroid.x, gdf.geometry.centroid.y])
    kd = KDTree(coords)
    # k=2: first result is the point itself (distance 0), second is nn.
    nn_dists = kd.query(coords, k=2)[0][:, 1]
    threshold = nn_dists.mean() + 3.0 * nn_dists.std()
    return pd.Series(nn_dists > threshold, index=gdf.index)


def compute_distance_band(
    gdf: gpd.GeoDataFrame,
    outlier_mask: pd.Series,
    value_column: str,
) -> float:
    """Return the optimal distance band in CRS units.

    Inputs must be projected (metres or feet).

    Tries in order:
      2a. Large dataset shortcut (n >= 10000 and any feature has 500+ neighbours)
      2b. Incremental Spatial Autocorrelation (first local Moran peak)
      2c. K-neighbour fallback
    """
    if gdf.crs is None or not gdf.crs.is_projected:
        raise ValueError(
            "GeoDataFrame must have a projected CRS (metres or feet). "
            f"Got: {gdf.crs}"
        )

    non_outliers = gdf[~outlier_mask].reset_index(drop=True)
    n_no = len(non_outliers)

    coords_no = np.column_stack(
        [non_outliers.geometry.centroid.x, non_outliers.geometry.centroid.y]
    )

    # Build KDTree once; mean nearest-neighbor distance drives 2a probe and 2b step.
    kd_no = KDTree(coords_no)
    nn_dists_no = kd_no.query(coords_no, k=2)[0][:, 1]
    start = float(nn_dists_no.mean())

    # -- 2a: large dataset shortcut -------------------------------------------
    # Only probe when n >= 10000 — for smaller datasets ArcGIS runs ISA directly.
    if n_no >= 10000:
        probe_radius = 30.0 * start
        sample_counts = kd_no.query_ball_point(
            coords_no[: min(200, n_no)], r=probe_radius, return_sorted=False
        )
        if any(len(nbrs) >= 500 for nbrs in sample_counts):
            print("Large dataset shortcut: using mean k=30 distance.")
            k30_dists = kd_no.query(coords_no, k=31)[0][:, 30]
            return float(k30_dists.mean())

    # -- 2b: Incremental Spatial Autocorrelation ------------------------------
    values_no = non_outliers[value_column].values.astype(float)

    distances: list[float] = []
    z_norms: list[float] = []

    for step in range(1, 31):
        d = start * step
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            w = libpysal.weights.DistanceBand.from_dataframe(
                non_outliers,
                threshold=d,
                binary=True,
                silence_warnings=True,
            )
        if len(w.islands) == n_no:
            z = float("nan")
        else:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                mi = Moran(values_no, w, two_tailed=False)
            z = float(mi.z_norm)
        distances.append(d)
        z_norms.append(z)
        print(f"  step {step:2d}: d={d:.2f}  Moran z={z:.4f}")

    # Find first local peak (higher than both neighbours).
    for i in range(1, len(z_norms) - 1):
        if (
            not np.isnan(z_norms[i])
            and not np.isnan(z_norms[i - 1])
            and not np.isnan(z_norms[i + 1])
            and z_norms[i] > z_norms[i - 1]
            and z_norms[i] > z_norms[i + 1]
        ):
            print(f"Peak found at step {i + 1}: d={distances[i]:.4f}")
            return distances[i]

    print("No peak found; using k-neighbour fallback.")

    # -- 2c: K-neighbour fallback ---------------------------------------------
    k = max(3, min(30, int(0.05 * len(gdf))))
    k_dists = kd_no.query(coords_no, k=k + 1)[0][:, k]
    mean_k = float(k_dists.mean())

    mean_x = coords_no[:, 0].mean()
    mean_y = coords_no[:, 1].mean()
    std_dist = sqrt(
        float(np.sum((coords_no[:, 0] - mean_x) ** 2 + (coords_no[:, 1] - mean_y) ** 2))
        / n_no
    )

    return min(mean_k, std_dist)


def run_gistar(
    gdf: gpd.GeoDataFrame,
    distance_band: float,
    value_column: str,
) -> gpd.GeoDataFrame:
    """Add GiZScore, GiPValue, Gi_Bin, NNeighbors columns and return gdf."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        w = libpysal.weights.DistanceBand.from_dataframe(
            gdf,
            threshold=distance_band,
            binary=True,
            silence_warnings=True,
        )
    # Binary weights, no row-standardization — ArcGIS uses binary weights.
    # transform="B" prevents G_Local from internally row-standardizing, which
    # would corrupt z-scores by making the self-weight 1/k instead of 1.
    g = G_Local(gdf[value_column], w, transform="B", star=True, permutations=0)

    _, p_corrected, _, _ = multipletests(g.p_norm, method="fdr_bh")

    def _classify(z: float, p: float) -> int:
        if p > 0.10:
            return 0
        sign = 1 if z > 0 else -1
        if p <= 0.01:
            return sign * 3
        if p <= 0.05:
            return sign * 2
        return sign * 1

    result = gdf.copy()
    result["GiZScore"] = g.Zs
    result["GiPValue"] = g.p_norm
    result["Gi_Bin"] = [
        _classify(float(z), float(p)) for z, p in zip(g.Zs, p_corrected)
    ]
    result["NNeighbors"] = [w.cardinalities[i] for i in range(len(gdf))]
    return result
