# Lab 4 workflow

Three-layer project covering the M22 fire history polygon data, a roads
network, and an OpenStreetMap basemap. Data layers are in NAD83 / California
zone 3 (EPSG:2227, US survey feet); basemap is EPSG:3857 (reprojected on the
fly by QGIS).

---

## Step 1 — Bootstrap project from source shapefiles

**Prompt:** create a new QGIS project from the data files in projects/lab4/data:
M22_39yrs.shp and roads.shp; set up a new project.py and .qgs

**What this does:**

Created layer files and project spec from scratch, inspecting the shapefiles
with `ogrinfo` to confirm CRS and geometry types.

| Layer | File | Geometry | Features |
|-------|------|----------|---------|
| `m22_39yrs` | `data/M22_39yrs.shp` | Polygon | 1,620 |
| `roads` | `data/roads.shp` | LineString | 11,201 |

Both layers share CRS **EPSG:2227** (NAD83 / California zone 3, US survey feet).
Project extent set to the M22_39yrs bounding box.

Styling:
- `m22_39yrs`: warm orange fill (semi-transparent) with dark-brown outline
- `roads`: medium-gray 0.5 mm line

**Files created:**
- `layers/m22_39yrs.py`
- `layers/roads.py`
- `project.py`
- `output/project.qgs` (via `make build`)

---

## Step 2 — Add OpenStreetMap basemap

**Prompt:** add an OpenStreetMap basemap

**What this does:**

Added `openstreetmap` as the bottom layer using the GDAL WMS TMS source
(tile.openstreetmap.org, EPSG:3857). Copied the layer file and style XML
directly from the BufferAndQuery project; QGIS reprojects the tiles to
match the EPSG:2227 project CRS at render time.

Layer order (top → bottom):

| Layer | Note |
|-------|------|
| `m22_39yrs` | Fire history polygons |
| `roads` | Road network |
| `openstreetmap` | Basemap |

**Files created/changed:**
- `layers/openstreetmap.py` — GDAL WMS TMS layer (OSM tiles)
- `styles/openstreetmap.xml` — copied from BufferAndQuery
- `project.py` — added `openstreetmap` import and layer reference

---

## Step 3 — Rename layer to human-readable name

**Prompt:** update layer name and filename from M22 39 Years to human readable;
inspect metadata

**What this does:**

Inspected `data/M22_39yrs.shp` schema and sample records. The file is ACS
Sex by Age (table B01001) joined to California census tracts (EPSG:2227).
1,620 tracts covering the Bay Area / Central Valley.

Key fields identified:

| Field | Meaning |
|-------|---------|
| `NAMELSAD` | Census tract name (e.g. "Census Tract 4001") |
| `GEOID` | 11-digit census tract FIPS code |
| `Total` | Total population per tract |
| `M22_39` | Derived count: males aged 22–39 (ACS B01001 VD10–VD13) |
| `HD01_VD*` | Raw ACS B01001 Sex by Age columns |
| `White`, `Black`, `Asian`, … | Racial breakdown totals |
| `ALandSqMi` | Land area in sq mi (ALAND / 2,589,988) |

Renamed layer file and updated id/name. Added field-level comments to the
layer file documenting the ACS table structure.

**Files changed:**
- `layers/m22_39yrs.py` → `layers/census_tracts_males_22_39.py`
- `project.py` — updated import and layer reference

---

## Step 4 — Derived layer: males 22–39 as % of population, filtered > 20%

**Prompt:** for each census tract, calculate percentage of total population
that are males 22–39; filter to > 20%; style with ColorBrewer natural breaks,
darker = higher

**What this does:**

Added `males_22_39_pct_over20` as a derived layer with a `PythonAction` that
computes `pct_m22_39 = M22_39 / Total * 100` and keeps only tracts where that
value exceeds 20%. The output shapefile retains only four columns:
`GEOID`, `NAMELSAD`, `pct_m22_39`, and geometry.

Result: **176 of 1,617 tracts** (those with Total > 0) exceed 20%.
Percentage range: **20.0 % – 44.5 %**.

Jenks natural breaks (5 classes, computed with mapclassify):

| Class | Range | Count | Color |
|-------|-------|------:|-------|
| 1 | 20.0 – 21.2 % | 47 | `#eff3ff` (lightest) |
| 2 | 21.2 – 22.9 % | 34 | `#bdd7e7` |
| 3 | 22.9 – 25.7 % | 44 | `#6baed6` |
| 4 | 25.7 – 30.0 % | 28 | `#3182bd` |
| 5 | 30.0 – 44.5 % | 23 | `#08519c` (darkest) |

ColorBrewer sequential Blues, encoded as a `RuleRenderer` with QGIS filter
expressions on `pct_m22_39`. Break edges are hardcoded from the initial
mapclassify run (in `claude.py::compute_male_22_39_breaks`).

**Files created/changed:**
- `layers/males_22_39_pct_over20.py` — processing function + RuleRenderer
- `project.py` — added `males_22_39_pct_over20` as top layer

---

## Step 4b — Suppress datum transformation dialog on project open

**Prompt:** every time I reload the QGIS project I have to click through a
dialog to select transformation for OpenStreetMap and roads; project CRS
must remain EPSG:2227 (NAD83 / California zone 3 ftUS, State Plane CA III)

**What this does:**

QGIS shows a "Select transformation" dialog when it finds multiple PROJ
paths between NAD83 (basis of EPSG:2227) and WGS84 (basis of EPSG:3857 /
OSM tiles). The fix is to embed the preferred transformation in the project
file so QGIS never has to ask.

Created `styles/base.qgs` as a per-project override of the alidade default
template (render.py checks `styles/base.qgs` before falling back to
`alidade/util/base.qgs`). Populated its empty `<transformContext />` with
the `<srcDest>` entry from the XY_projections project, which had already
saved the same CRS pair. The chosen operation uses the California/Nevada
horizontal grid shift (`us_noaa_cnhpgn.tif`, NADCON) with `allowFallback="1"`
so the project still opens if the grid file is absent.

**Files created:**
- `styles/base.qgs` — project base template with EPSG:3857 ↔ EPSG:2227
  transform context pre-filled

---

## Step 5 — Extract break values into constants

**Prompt:** pull out numbers in the renderer into constants so they can be
changed in one spot

**What this does:**

Extracted all six break-edge values (`_MIN`, `_B1`–`_B4`, `_MAX`) into
module-level constants in `males_22_39_pct_over20.py`. The filter expressions
and labels in the `RuleRenderer` rules now use f-strings referencing those
constants, and the `filter_males_22_39_pct` function uses `_MIN` for the
threshold filter. Changing any break value updates the filter, label, and
processing threshold together.

**Files changed:**
- `layers/males_22_39_pct_over20.py` — constants + f-string rules

---

## Step 6 — Fix OpenStreetMap basemap showing Saudi Arabia

**Prompt:** there's a mismatch in projections; OSM shows Saudi Arabia with
Bay Area census tracts on top

**What this does:**

The GDAL WMS provider passed canvas coordinates directly to the tile server
as EPSG:3857 meters without reprojecting. With the project CRS set to
EPSG:2227 (US survey feet, false easting ~6.5M ft), the canvas coordinates
(~5.7M–6.4M, ~1.8M–2.5M) were interpreted as EPSG:3857 meters, landing in
the Arabian Peninsula.

Fix: switched to the QGIS native WMS/XYZ tile provider (`provider="wms"`,
`type=xyz` source URL), which transforms the viewport extent from the project
CRS into EPSG:3857 before requesting tiles. Also dropped `style_xml` so the
maplayer XML is generated fresh from the model (the old XML encoded the GDAL
datasource and would have overridden the source change).

**Files changed:**
- `layers/openstreetmap.py` — WMS/XYZ provider, no style_xml
- `styles/openstreetmap.xml` — no longer used (can be deleted)

---

## Step 7 — Zoom initial extent to males_22_39_pct_over20 bounding box

**Prompt:** update initial extent to bounding box from males_22_39_pct_over20 features

**What this does:**

Read `output/males_22_39_pct_over20.shp` total bounds and replaced the
project extent in `project.py` (previously the full M22_39yrs extent).

Old extent (all 1,620 source tracts): 5,695,774 – 6,355,025 x 1,770,384 – 2,507,172
New extent (176 filtered tracts):     5,923,036 – 6,174,297 x 1,808,925 – 2,377,049

**Files changed:**
- `project.py` — updated `extent` tuple

---

## Step 8 — Pad extent to avoid clipping edge polygons

**Prompt:** north and south polygons are cut off; update bounding box to include all polygons

**What this does:**

`total_bounds` is tight to outermost vertices, so polygons on the edges
render half-clipped. Added 5% padding on each side (pad_x ≈ 12,563 ft,
pad_y ≈ 28,406 ft).

**Files changed:**
- `project.py` — updated `extent` tuple with 5% buffer

---

## Step 9 — Document roads.shp contents

**Prompt:** read ./data/roads.shp and add a comment to the layer file describing contents

**What this does:**

Inspected roads.shp schema, geometry types, and FCC code distribution.
11,201 California major road segments (STATEFIPS=06); no local streets.
Dominant classes: A30 secondary/county (5,096), A63 rural route (3,633),
A31 connecting road (1,260), A11 Interstate (315). LENGTH field is in miles.

**Files changed:**
- `layers/roads.py` — added header comment with field descriptions and FCC counts

---

## Step 10 — Derived layer: major roads (FCC A10–A21)

**Prompt:** create a new layer from roads filtered to FCC A10–A21

**What this does:**

Created `major_roads` as a derived layer filtering the full roads dataset to
primary and major highway FCC codes. A14, A17, A18 are included per spec but
have no matching features in this dataset.

Matched codes and counts from source data:

| FCC | Count | Description |
|-----|------:|-------------|
| A10 | 4 | Primary limited-access highway (connector/ramp) |
| A11 | 315 | Interstate highway |
| A12 | 7 | Other limited-access highway (divided) |
| A13 | 11 | Other limited-access highway |
| A15 | 53 | Primary highway without limited access |
| A16 | 2 | Primary highway, toll |
| A20 | 210 | US highway without limited access |
| A21 | 174 | State route without limited access |

Total: **776 segments**. Styled as a 1.0 mm near-black line, sitting above
the base roads layer.

**Files created/changed:**
- `layers/major_roads.py` — filter function + SingleSymbol renderer
- `project.py` — added `major_roads` between `males_22_39_pct_over20` and `roads`
