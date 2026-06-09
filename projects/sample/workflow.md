# sample workflow

Reference project demonstrating alidade features: vector styling, raster
layers, rule-based renderers, and derived processing steps.

---

## Step 1 — Install alidade as a proper package

**What this does:**

Refactored the repo so `alidade` is an installed Python package. All layer
files updated: `from models import` → `from alidade.models import`.

**Files changed:**
- All `layers/*.py` — import line only
- `project.py` — import line only

---

## Step 2 — Color system refactor

Updated all layer files to use the new `alidade.color.Color` type. Inline QGIS
extended-format strings (e.g. `"125,17,196,0,hsv:..."`) replaced with
`Color.from_hex(...)` calls; the HSV/RGB float suffixes in the QGIS extended
format are dropped since only the R,G,B,A values are needed. Repeated colors
extracted to a module-level constant (`_DARK_GRAY` in
`park_features_symbol_points.py`).

**Files changed:**
- `layers/park_polygon.py`
- `layers/park_features_symbol_polygons.py`
- `layers/park_features_symbol_lines.py`
- `layers/park_features_symbol_points.py`
- `layers/arp_areas.py`
