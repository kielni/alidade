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
