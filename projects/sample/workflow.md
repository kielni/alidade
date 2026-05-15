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
