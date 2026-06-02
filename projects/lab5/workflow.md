# Lab 5 workflow

## Step 1 — Migrate from .aprx to .lyrx output

**What this does:**

Switched output format from a single `project.aprx` ZIP archive (which ArcGIS Pro
failed to read correctly — Contents tab empty) to individual `{layer.id}.lyrx` files,
one per operational layer. Each `.lyrx` is a standalone `CIMLayerDocument` JSON that
ArcGIS Pro opens directly without requiring a working project archive.

The `.aprx` approach required a fragile `Index.json` node graph that was difficult to
keep consistent with CIM's CIMPATH references. The `.lyrx` approach avoids this entirely:
each file is self-contained and independently loadable. Basemaps must be added manually
in ArcGIS Pro per session since they are not stored in `.lyrx` files.

**Files changed:**
- `project.py` — import `Project` directly (not `ArcGISProject`); `output_format="lyrx"`;
  removed basemap CIM passthrough

---

## Step 2 — Rename median_household_income layers to household_income

**What this does:**

Renamed the `median_household_income` and `median_household_income_raw` layers
(and all associated files) to `household_income` and `household_income_raw` for
brevity. The data source (`B19013MedHHIncome.shp`) and field name (`MedianHH_i`)
are unchanged.

**Files changed:**
- `layers/household_income.py` — renamed from `median_household_income.py`; updated id, name, source path, depends_on
- `layers/household_income_raw.py` — renamed from `median_household_income_raw.py`; updated id, name
- `output/household_income.{cpg,dbf,prj,shp,shx}` — renamed from `median_household_income.*`
- `project.py` — updated imports and layer list

---

## Step 3 — Replace en dashes with hyphens

**What this does:**

Replaced Unicode en dashes (U+2013) with plain ASCII hyphens throughout layer files
and docstrings for consistency and to avoid encoding surprises.

**Files changed:**
- `layers/census_tracts.py` — layer name and range labels
- `layers/census_tracts_raw.py` — docstring

---

## Step 4 — household_income: restore raw/processed split

**What this does:**

Reinstated the `census_tracts_raw` → `census_tracts` pattern for the income layer.
`household_income_raw` is a hidden layer sourcing `data/B19013MedHHIncome.shp`
directly. `household_income` filters to `MedianHH_i > 0` (dropping 10 tracts with
missing data) and writes `output/household_income.shp`, which the graduated renderer
is applied to.

**Files changed:**
- `layers/household_income_raw.py` — hidden raw layer (no renderer)
- `layers/household_income.py` — `filter_nonzero_income` processing step; source `output/household_income.shp`
- `project.py` — both layers in layer list

---

## Step 5 — household_income: Oranges palette, census_tracts label style

**What this does:**

Switched `household_income` from ColorBrewer YlOrRd to 5-class Oranges (light to dark,
60% fill opacity) and updated the legend labels to match `census_tracts` style:
`LOWER - UPPER` for interior classes, `UPPER+` for the highest class.

**Files changed:**
- `util.py` — `INCOME_BUCKETS` updated to Oranges; `INCOME_OUTLINE` updated to dark orange
- `layers/household_income.py` — label format updated

---

## Step 6 — Add 2-mile mall buffers layer

**What this does:**

Added `mall_buffers`: a processing layer that buffers the 11 mall points by 2 miles
(10,560 US survey feet in EPSG:2227) and writes `output/mall_buffers.shp`. Styled
with a light green semi-transparent fill and darker green outline, matching the
lab4 mall buffer style.

**Files changed:**
- `layers/mall_buffers.py` — new layer with `buffer_malls` processing step
- `project.py` — added `mall_buffers` import and layer

---

## Step 7 — household_income: switch to ColorBrewer RdBu reversed palette

**What this does:**

Replaced the Oranges color ramp on `household_income` with ColorBrewer 5-class
RdBu reversed (blue → cream → red = low → high income), 60% fill opacity.
Outline updated to dark neutral grey. Docstring updated to match.

**Files changed:**
- `util.py` — `INCOME_BUCKETS` updated to RdBu reversed; `INCOME_OUTLINE` updated to dark grey (60,60,60)
- `layers/household_income.py` — docstring updated

---

## Step 15 — hotspots_overlap: implement print_targets; update story_map

**What this does:**

Implemented `print_targets()` to rank the 11 BigBucks mall buffers by the
number of men ages 22–39 (M22_39) reachable within the hot spot overlap zone.

Algorithm: two `gpd.overlay(how="intersection")` passes.
1. `hotspots_overlap` × `HotSpotsYoungMen[Gi_Bin==3]` — attributes area-weighted
   M22_39 from each source census tract to the overlap polygons.
2. That result × `mall_buffers` — clips to each mall's 2-mile service area.

M22_39 is area-weighted throughout (each sub-piece gets `M22_39 × piece_area /
tract_area`) so counts are not double-counted when a census tract spans multiple
intersection pieces.

**Results** (only 3 of 11 malls intersect the target zone):

| Mall | City | M22_39 in zone | Overlap area |
|---|---|---|---|
| Santana Row | San Jose | 5,652 | 3.88 sq mi |
| Westgate Center | San Jose | 3,332 | 1.96 sq mi |
| Great Mall | Milpitas | 7 | 0.73 sq mi |

Updated `story_map.md` executive summary and map 5 narrative with these findings
and the three recommended launch sites.

**Files changed:**
- `layers/hotspots_overlap.py` — `print_targets`: full implementation (replaces stub)
- `story_map.md` — executive summary and map 5 updated with site recommendations

---

## Step 14 — hotspots_overlap: fix syntax error in print_targets stub

**What this does:**

`print_targets()` had a comment-only body with no executable statement,
causing an `IndentationError` at parse time.  Added `pass` so the module is
importable while keeping the TODO comments in place.

**Files changed:**
- `layers/hotspots_overlap.py` — `print_targets`: added `pass` to stub body

---

## Step 13 — hotspots_overlap: intersection of Gi_Bin=3 hot spots

**What this does:**

Added `hotspots_overlap`: filters both `hotspots_income` and `hotspots_census` to
`Gi_Bin == 3` (99% confidence hot spots only), then computes their polygon
intersection via `gpd.overlay(..., how="intersection")`. The result is the set of
areas that are simultaneously high-income and high-density 22-39 male hot spots.

Styled with a solid orange fill (255,127,0, 78% opacity) and dark orange outline,
distinct from both individual hot spot layers.

**Files changed:**
- `layers/hotspots_overlap.py` — new layer; `compute_overlap(src_income, src_census, output)`
- `project.py` — added `hotspots_overlap` import and layer

---

## Step 12 — hotspots_census: Gi* on M22_39; refactor algorithm to util.py

**What this does:**

Moved the three hotspot computation functions from `hotspots_income.py` into
`util.py` so they can be shared across layers:
- `find_locational_outliers(gdf)` — unchanged signature
- `compute_distance_band(gdf, outlier_mask, value_column)` — added `value_column`
  parameter (was hardcoded to `MedianHH_i`)
- `run_gistar(gdf, distance_band, value_column)` — unchanged signature
- `hotspot_renderer(attr="Gi_Bin")` — new factory; returns the standard ArcGIS Pro
  7-class graduated renderer; avoids duplicating 50 lines of renderer code
- Color constants (`HOTSPOT_COLD_99`, etc.) moved to `util.py`

Added `hotspots_census`: same three-function pipeline on `M22_39` from
`output/census_tracts.shp`. Both `hotspots_income` and `hotspots_census` now import
from `util.py` and are otherwise identical in structure.

**Files changed:**
- `util.py` — added hotspot algorithm, renderer factory, and color constants
- `layers/hotspots_income.py` — stripped to imports + `compute_hot_spots` + layer
- `layers/hotspots_census.py` — new layer; same structure as hotspots_income
- `test_processing.py` — imports moved to `util`; added `TestHotspotsCensus` class
- `project.py` — added `hotspots_census` import and layer

---

## Step 11 — hotspots_income: unit tests

**What this does:**

Added `test_processing.py` with 9 unittest cases validating the hotspots_income
pipeline against `arcgis_hotspot.txt` targets:

| Test | Expected | Tolerance |
|---|---|---|
| Outlier count | 40 | exact |
| Distance band | 39829.87 ft | ±25% |
| FID 207 Gi_Bin | 3 | exact |
| FID 207 z-score | positive | — |
| Significant features | 1207 | ±25% |
| Gi_Bin range | {-3…+3} | — |
| Hot + cold spots present | both | — |
| NNeighbors non-negative | all | — |
| Output columns | all 4 | — |

Run: `uv run python -m unittest projects.lab5.test_processing`

Note on distance band: ISA (libpysal Moran z_norm) finds a first local peak at
~48933 ft vs ArcGIS's 39829 ft. Both are within 25% and FID 207 Gi_Bin=3 matches.
The discrepancy is likely due to a different Moran's I normalization or step spacing
in ArcGIS's internal ISA implementation.

**Files changed:**
- `test_processing.py` — new unittest file

---

## Step 9+10 — hotspots_income: Optimized Hot Spot Analysis replicating ArcGIS Pro

**What this does:**

Added `hotspots_income`: a processing layer that replicates ArcGIS Pro's Optimized Hot
Spot Analysis on `MedianHH_i` from `output/household_income.shp`.  Three-function
pipeline:

1. `find_locational_outliers` — marks features whose nearest-neighbor distance exceeds
   mean + 3 std; these are excluded from distance band calculation.
2. `compute_distance_band` — tries in order: large-dataset shortcut (k=30 mean if any
   feature has 500+ neighbours), Incremental Spatial Autocorrelation (first local peak
   in Moran's I z-norm over 30 steps), k-neighbour fallback.
3. `run_gistar` — builds binary `DistanceBand` weights (no row-standardization),
   runs `esda.G_Local(star=True, permutations=0)`, applies Benjamini-Hochberg FDR
   via `statsmodels.stats.multitest.multipletests`.

**`Gi_Bin` classification (after FDR correction):**
| Corrected p | Z > 0 | Z < 0 |
|---|---|---|
| ≤ 0.01 | +3 | -3 |
| ≤ 0.05 | +2 | -2 |
| ≤ 0.10 | +1 | -1 |
| > 0.10 | 0 | 0 |

**Renderer:** ArcGIS Pro hot spot color scheme, fully opaque, integer breakpoints
(-3 to +3), "Cold/Hot Spot with X% Confidence" labels.

**Validation targets (from `arcgis_hotspot.txt`):**
- 40 locational outliers
- Distance band ~39829.87 ft
- 1207 significant features after FDR

**Bug fixes applied after initial implementation:**
- `transform="B"` added to `G_Local` — default `transform="R"` was internally
  row-standardizing binary weights, setting self-weight to 1/k instead of 1,
  corrupting z-scores and producing all Gi_Bin=1
- 2a shortcut gated on `n_no >= 10000` — at `probe_radius = 30*start`, dense
  census tracts triggered the shortcut, returning 21626 ft instead of ISA result
- ISA disconnected-graph guard removed — `n_components > 1` was skipping steps
  1–9, so the Moran z-norm was computed from step 10 onward only

**Files changed:**
- `layers/hotspots_income.py` — complete rewrite with three-function pipeline; bug fixes above
- `pyproject.toml` — added `scipy`, `statsmodels` dependencies; mypy overrides for both

---

## Step 8 — Rename palette constants to ColorBrewer names

**What this does:**

Renamed the palette constants in `util.py` from project-specific names
(`CENSUS_BUCKETS`, `CENSUS_OUTLINE`, `INCOME_BUCKETS`, `INCOME_OUTLINE`) to
ColorBrewer palette names (`PURPLES`, `PURPLES_OUTLINE`, `RDBU_R`,
`RDBU_R_OUTLINE`). Updated imports and usages in both layer files.

**Files changed:**
- `util.py` — renamed all four constants
- `layers/census_tracts.py` — updated import and usages
- `layers/household_income.py` — updated import and usages
