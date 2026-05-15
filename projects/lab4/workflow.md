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
