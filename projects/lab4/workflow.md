# Lab 4 workflow

## Step 49 — Fix lint errors (unused import, trailing whitespace)

**Prompt:** fix all lint errors

**What this does:**

Three flake8 errors fixed:

- `projects/XY_projections/project.py` — removed unused `from pathlib import Path`
- `layers/mall_people_deduped.py` lines 29, 31 — removed trailing whitespace
  from the Voronoi explanation docstring

No logic or styling changes.

**Files changed:**
- `layers/mall_people_deduped.py` — trailing whitespace removed from docstring
- `projects/XY_projections/project.py` — unused `Path` import removed

---

## Step 48 — Rename mall_voronoi_people → mall_people_deduped; simplify to one input

**Prompt:** rename mall_voronoi_people to mall_people_deduped; simplify
depends_on to just mall_buffers + target_tracts (derive mall points from
buffer centroids).

**What this does:**

Created `layers/mall_people_deduped.py` replacing `mall_voronoi_people.py`.
Three changes bundled together:

1. **Rename** — layer file, Python variable, layer id, QGIS display name,
   source/output paths all updated to `mall_people_deduped`.

2. **Simplified inputs** — `aggregate_deduped_m22_39(buffers, tracts, output)`
   takes only two inputs. `_build_draw_zones` now derives mall points from
   `buffers_gdf.geometry.centroid` (exact for circular buffers in a projected
   CRS), eliminating the `mall_points` dependency.

3. **Build fix** — `depends_on` changed from
   `["mall_points", "mall_buffers", "target_tracts"]` to
   `["mall_buffers", "target_tracts"]`. The build system (`build.py`) resolves
   dependencies only from layers present in the active spec; `mall_buffers`
   is now explicitly included in `spec_dedup`, fixing the `KeyError: 'mall_buffers'`
   failure that occurred with `--force`.

**Files created/changed:**
- `layers/mall_people_deduped.py` — new; replaces `mall_voronoi_people.py`
- `project.py` — import updated; `spec_all` and `spec_dedup` reference
  `mall_people_deduped`; `mall_buffers` added to `spec_dedup` layer list

---

## Step 47 — Extract MALL_BUCKET_COLORS palette to util.py

**Prompt:** move YlGnBu 3-class palette from mall_voronoi_people and
mall_buffer_people to shared location in util.py.

**What this does:**

Added `MALL_BUCKET_COLORS` to `util.py` alongside `CENSUS_BUCKETS`. Both
`mall_buffer_people.py` and `mall_voronoi_people.py` now import it from
there and remove their local `_YLGNBU` definitions.

**Files changed:**
- `util.py` — `MALL_BUCKET_COLORS` list added (YlGnBu 3-class)
- `layers/mall_buffer_people.py` — removed `_YLGNBU`; imports and uses
  `MALL_BUCKET_COLORS`
- `layers/mall_voronoi_people.py` — removed `_YLGNBU`; imports and uses
  `MALL_BUCKET_COLORS`

---

## Step 46 — Voronoi draw zones: deduplicated target population per mall

**Prompt:** mall_buffer_people double-counts people in overlapping buffer zones;
build Voronoi/Thiessen polygons clipped to 5-mile buffers so each person is
assigned to their closest mall; area-weight M22_39 across zone boundaries;
use as map4 only (spec_dedup), keeping mall_buffer_people in map3.

**What this does:**

Created `mall_voronoi_people` as a new derived layer. For each mall:

1. **Voronoi cells** — `shapely.ops.voronoi_diagram` on the 11 mall points,
   using the union of all 5-mile buffers as the envelope. Each cell contains
   exactly the area closer to that mall than to any other.
2. **Clip to buffer** — each Voronoi cell is intersected with its mall's own
   5-mile buffer, producing the exclusive draw zone (arc-shaped where buffers
   overlap, full circle where they don't).
3. **Area-weighted overlay** — `gpd.overlay(draw_zones, target_tracts,
   how="intersection")` fragments target census tracts at draw zone boundaries.
   Each fragment contributes `M22_39 × (fragment_area / tract_area)` to its
   mall, assuming uniform density within a tract.
4. **Equal-count bucket** — same 0/1/2 good/better/best scheme as
   `mall_buffer_people`, computed from the deduplicated totals.

The geometry rendered is the draw zone polygon (not the full circle buffer),
so overlap areas are visually split between their respective malls.

`spec_dedup` / `map4` mirrors `spec_near_malls` / `map3` but substitutes
`mall_voronoi_people` for `mall_buffer_people`. `spec = map4` is now active.
`mall_voronoi_people` also added to `spec_all`.

**Files created/changed:**
- `layers/mall_voronoi_people.py` — `_build_draw_zones()` +
  `aggregate_voronoi_m22_39()`; depends on `mall_points`, `mall_buffers`,
  `target_tracts`; YlGnBu palette; same bucket renderer as `mall_buffer_people`
- `project.py` — `mall_voronoi_people` imported; added to `spec_all`;
  `spec_dedup` / `map4` added with `mall_voronoi_people`; `spec = map4`

---

## Step 45 — Create styles/cartodb_positron.xml for dark basemap

**Prompt:** style_xml=Path("styles/cartodb_positron.xml") has been removed;
generate a new one for use with a dark basemap

**What this does:**

Created `styles/cartodb_positron.xml` for the lab4 project. The file is
copied from `projects/sample/styles/cartodb_positron.xml` (the canonical
tile-layer template providing the `singlebandcolordata` pipe required for
color XYZ tiles). The `_inject_layers` render path overwrites `<id>`,
`<datasource>`, and `<layername>` from the `Layer` spec at build time, so
the embedded `dark_all` URL and "Basemap" name serve only as documentation.

**Files created:**
- `styles/cartodb_positron.xml` — raster maplayer template with
  `singlebandcolordata` pipe; `basemap.py` `style_xml` now resolves

---

## Step 44 — Rename malls `name` field to `Street`

**Prompt:** in malls, update `name` to `Street`; update labeling to use
mall_name instead of name

**What this does:**

Renamed the street-address field in `output/malls.shp` from `name` to
`Street` to match the source CSV column name and distinguish it from the
`mall_name` label field. The label was already wired to `mall_name` (Step 42),
so no change to the `Label` definition was needed.

Updated in `malls.py`: row dict key, header comment, and processing
description.

**Files changed:**
- `layers/malls.py` — `"name"` → `"Street"` in geocode row dict; comment and
  processing description updated

---

## Step 43 — Remove redundant mall_name join from mall_buffers

**Prompt:** move mall names join out of mall_buffers and into malls so that
it only has to be done once

**What this does:**

`mall_buffers` previously re-read `mall_names.csv` and joined `MallName` on
`id` (with zero-padding normalisation) to produce `mall_name` in the buffer
shapefile. Now that `malls.shp` carries `mall_name` directly (Step 42),
`buffer_malls` can simply buffer the geometry and write the file — `mall_name`
is already present in the source GeoDataFrame.

Removed from `mall_buffers.py`: `pandas` import, `project_data_dir` import,
`_CSV` constant, and the CSV read / rename / normalise / merge block.

**Files changed:**
- `layers/mall_buffers.py` — join removed; `pd`/`project_data_dir`/`_CSV`
  removed; header comment and processing description updated

---

## Step 42 — Add mall name labels to malls layer

**Prompt:** show mall names as labels on the malls layer; use mall_names.csv
MallName field; reference project_labels.qgs for label style

**What this does:**

Two changes:

1. **`mall_name` field added to malls shapefile**: The geocode function now
   reads `mall_names.csv` instead of `malls.csv` (same addresses, adds
   `MallName`). The field is stored as `mall_name` in `output/malls.shp`
   alongside the existing `id`, `name`, and `city` fields.

2. **Label support added to alidade**: New `Label` model in `alidade/models.py`
   and `label: Label | None` field on `Layer`. `_build_labeling()` in
   `alidade/render.py` emits `<labeling type="simple">` XML matching the style
   in `project_labels.qgs` (Open Sans Bold 10 pt, light gray
   `225,225,225,255`, placed above the point with 2 mm y-offset, overlap
   handling enabled). `_build_vector_maplayer` sets `labelsEnabled="1"` when
   a label is configured.

   `malls.py` wires it up with `label=Label(field="mall_name")`.

**Files changed:**
- `alidade/models.py` — new `Label` model; `label: Label | None` on `Layer`
- `alidade/render.py` — `_build_labeling()` helper; `labelsEnabled` conditional;
  `Label` added to imports
- `layers/malls.py` — source CSV → `mall_names.csv`; `mall_name` field added
  to geocode output; `Label` imported and applied; processing description updated

---

## Step 41 — Major roads color for dark basemap

**Prompt:** update color of major_roads to work with dark mode

**What this does:**

Changed `SimpleLine` color from `30,30,30,255` (near-black, invisible on
dark backgrounds) to `220,210,180,255` (warm off-white/pale yellow), which
reads clearly against CartoDB Dark Matter without being visually harsh.

**Files changed:**
- `layers/major_roads.py` — `line_color` updated

---

## Step 40 — Mall SVG icon color to medium orange

**Prompt:** update color of mall svg icon to medium orange

**What this does:**

Changed `SvgMarker` fill and outline colors in `malls.py`:

| Property | Old | New |
|----------|-----|-----|
| `color` | `25,27,28,255` (near black) | `230,120,0,255` (medium orange) |
| `outline_color` | `35,35,35,255` (near black) | `160,84,0,255` (darker orange) |

**Files changed:**
- `layers/malls.py` — `color` and `outline_color` updated

---

## Step 39 — Switch basemap to CartoDB Dark Matter; rename to basemap

**Prompt:** update baselayer to use dark version of carto basemap; rename layer to basemap

**What this does:**

Switched the CartoDB tile URL from `light_all` (Positron) to `dark_all`
(Dark Matter) and renamed the layer throughout:

| | Old | New |
|---|-----|-----|
| QGIS display name | `CartoDB Positron` | `Basemap` |
| Python variable | `cartodb_positron` | `basemap` |
| Python module | `layers/cartodb_positron.py` | `layers/basemap.py` |
| Tile endpoint | `.../light_all/...` | `.../dark_all/...` |

`layers/cartodb_positron.py` is retained (unused) since files cannot be
deleted; all imports now reference `layers/basemap.py`.

**Files changed:**
- `layers/basemap.py` — new file; dark_all URL, name "Basemap"
- `styles/cartodb_positron.xml` — datasource and layername updated to dark_all / "Basemap"
- `project.py` — import and all layer-list references updated to `basemap`

---

## Step 38 — Fix layer IDs too short for QGIS (malls, roads)

**Prompt:** malls layer does not load properly; QGIS drops layers whose `<id>`
is 10 characters or shorter

**What this does:**

QGIS's layer reader silently discards layers whose `<id>` text is ≤ 10
characters. `malls` (5) and `roads` (5) were below the threshold; both layers
were silently rejected, leaving them half-attached in the panel with no
renderer or context menu.

Fix applied at two levels:

1. **`alidade/models.py`** — added a `field_validator` on `Layer.id` that
   pads any ID of 10 characters or fewer with a deterministic UUID5 suffix
   (`{id}_{uuid5(NAMESPACE_DNS, id).hex[:8]}`). Deterministic so the same ID
   always produces the same padded form across renders.

2. **`layers/malls.py` / `layers/roads.py`** — updated the short IDs to their
   padded forms so the source files are explicit rather than relying on the
   runtime validator silently rewriting them:

   | Old ID | New ID |
   |--------|--------|
   | `malls` | `malls_c4ae8970` |
   | `roads` | `roads_52280a2b` |

**Files changed:**
- `alidade/models.py` — `_pad_short_id` field validator on `Layer.id`
- `layers/malls.py` — `id` updated to `"malls_c4ae8970"`
- `layers/roads.py` — `id` updated to `"roads_52280a2b"`

---



Three-layer project covering the M22 fire history polygon data, a roads
network, and an OpenStreetMap basemap. Data layers are in NAD83 / California
zone 3 (EPSG:2227, US survey feet); basemap is EPSG:3857 (reprojected on the
fly by QGIS).

---

## Step 37 — Update mall_buffer_people palette to YlGnBu class 2

**Prompt:** update colors in mall_buffer_people to #a1dab4 #41b6c4 #225ea8

**What this does:**

Replaced the three `_YLGNBU` RGB strings with the mid-range YlGnBu 3-class set:

| Bucket | Old | New |
|--------|-----|-----|
| Good | `#edf8b1` | `#a1dab4` |
| Better | `#7fcdbb` | `#41b6c4` |
| Best | `#2c7fb8` | `#225ea8` |

**Files changed:**
- `layers/mall_buffer_people.py` — `_YLGNBU` updated; TODO comment removed

---

## Step 36 — Fix SvgMarker rendering (missing parameters element; float formatting)

**Prompt:** markers not rendering; find and fix broken config; compare project_bad.qgs
vs project_svg.qgs (working built-in SVG icon written by QGIS)

**What this does:**

Diffed `project_svg.qgs` (QGIS-saved, working) against `project_bad.qgs` (generated,
broken). Two bugs in `alidade/render.py`'s SvgMarker branch:

1. **Missing `<Option name="parameters" />`**: QGIS 3.44 requires this bare element
   in the SvgMarker option map (used for SVG fill/outline parameter overrides). Without
   it, QGIS cannot parse the symbol layer and the malls layer has no context menu.
   Fixed by inserting it after `outline_width_unit` in alphabetical position.

2. **Float formatting**: `angle`, `outline_width`, `size` were serialized with `str()`
   producing `"0.0"`, `"5.0"`. QGIS expects `"0"`, `"5"`. Applied `:g` format (already
   used by SimpleMarker) to all three fields.

**Files changed:**
- `alidade/render.py` — SvgMarker: insert bare `parameters` Option element;
  `:g` format for `angle`, `outline_width`, `size`

---

## Step 35 — Shared census outline color; print layouts in project.py; local SVG path

**Prompt:** (1) update icon to use data/mall.svg; add CC BY-SA 4.0 via Wikimedia Commons
to credits; (2) move print layout content from main.py into project.py, shared print
renderer for each Project instance; (3) move _OUTLINE from census_tracts.py into
util.py, rename CENSUS_OUTLINE, update everywhere, color to dark purple

**What this does:**

**Mall SVG icon and credits:**

Changed `SvgMarker.name` from the QGIS built-in `shopping/shopping_gift.svg` to the
project-local `data/mall.svg`. `alidade/render.py` now resolves `data/`-prefixed SVG
paths relative to the project directory (the same logic as datasource paths), so the
QGS file receives `../data/mall.svg` relative to `output/`.

Attribution added to `CREDITS` in `project.py`:
`"US Census Bureau, 2010 data · Big Bucks INC · CartoDB Positron · CC BY-SA 4.0 via Wikimedia Commons"`

**Print layouts moved to project.py:**

Each print-spec (`spec_overview`, `spec_young_men`, `spec_near_malls`) now carries its
own `print_layout=PrintLayout(...)` directly on the `Project` instance. Shared
components (`_FRAME_600k`, `_FRAME_350k`, `_SCALE_BAR_MI`, `CREDITS`) are module-level
constants in `project.py`. `main.py` is reduced to thin wrappers that call
`render_print_layout(spec_*, PROJECT_DIR)`.

**Shared census outline color:**

Extracted `CENSUS_OUTLINE = "63,0,125,255"` (dark purple, darker than class-5 fill,
full opacity) into `util.py` alongside `CENSUS_BUCKETS`. Removed the local `_OUTLINE`
constant from `census_tracts.py`, `mall_target_intersect.py`, and `target_tracts.py`
(which previously had an unrelated blue outline); all three now import and use
`CENSUS_OUTLINE`.

**Files changed:**
- `alidade/render.py` — thread `project_dir` through `_render_symbol_layer`,
  `_render_symbol`, `_render_renderer`; resolve `data/`-prefixed SVG names via
  `_rel_source`
- `layers/malls.py` — `name` changed to `"data/mall.svg"`
- `util.py` — `CENSUS_OUTLINE = "63,0,125,255"` added
- `layers/census_tracts.py` — removed `_OUTLINE`; uses `CENSUS_OUTLINE`
- `layers/mall_target_intersect.py` — removed `_OUTLINE`; uses `CENSUS_OUTLINE`
- `layers/target_tracts.py` — removed `_OUTLINE`; uses `CENSUS_OUTLINE`
- `project.py` — `CREDITS`, `_FRAME_*`, `_SCALE_BAR_MI` constants; `print_layout`
  added to `spec_overview`, `spec_young_men`, `spec_near_malls`
- `main.py` — simplified to import specs and call `render_print_layout` directly

---

## Step 32 — Switch malls marker to SVG shopping icon

**Prompt:** read projects/lab4/output/project.qgs, extract SVG icon styling for
the malls layer, and apply to the Python malls layer

**What this does:**

Replaced the plain red `SimpleMarker` circle with the `SvgMarker` that was
already in `project.qgs` (a second maplayer entry for malls added manually in
QGIS). Extracted from the `SvgMarker` symbol layer in that file:

| Property | Value |
|----------|-------|
| SVG | `shopping/shopping_gift.svg` |
| color | `25,27,28,255` (near black) |
| outline_color | `35,35,35,255` |
| outline_width | `0` mm |
| size | `5` mm |

**Files changed:**
- `layers/malls.py` — `SimpleMarker` → `SvgMarker`; import updated accordingly

---

## Step 31 — Per-mall M22–39 summary layer

**Prompt:** for each mall buffer zone, calculate sum of M22_39 values for all
census districts (pct_m22_39 > 20%) within the polygon; create a new layer
with 5-mile buffer polygon, mall name, and total count; style with 80%
transparent green fill and outline weight in three buckets (good/better/best)

**What this does:**

Created `mall_buffer_people` as a derived layer that aggregates
`mall_target_intersect` (one row per census tract × mall pair) to produce
one row per mall with the total M22_39 count across all target tracts
intersecting that buffer. The buffer polygon geometry comes from
`mall_buffers`.

Current data (2 malls with ≥ 1 target tract):

| Mall | m22_39_total |
|------|--------------|
| Stanford Shopping Center | 10,040 |
| Westgate Center | 16,216 |

Styled with a `RuleRenderer` (3 rules):

| Bucket | Threshold | Outline |
|--------|-----------|---------|
| Good | ≤ 12,000 | light green `#90ee90`, 0.5 mm |
| Better | 12,001 – 15,000 | medium green `#50a050`, 1.0 mm |
| Best | > 15,000 | dark green `#006400`, 2.0 mm |

Fill is the same for all buckets: CSS lightgreen at 20% opacity (80%
transparent) — `144,238,144,51`.

Layer depends on `target_tracts` and `mall_buffers`. The processing function
reads `target_tracts.shp` (already filtered to pct_m22_39 > 20%), spatially
joins those tracts with the buffer polygons, groups by mall and sums M22_39,
then merges back to the buffer polygon geometry so each output row carries
the 5-mile buffer shape. `M22_39` was added to the `target_tracts` output
fields to support this.

Equal-count quantile breaks (33rd / 67th percentile of `m22_39_total`) are
computed at processing time and written as a `bucket` column (0 = Good,
1 = Better, 2 = Best). The renderer filters on `bucket` so no hardcoded
thresholds are needed in the layer definition.

**Files created/changed:**
- `layers/mall_buffer_people.py` — spatial join + aggregation function +
  RuleRenderer; depends on `target_tracts` and `mall_buffers`; groupby on
  `mall_id` only, merge back to `buf` on `mall_id` to recover geometry and
  `mall_name`; bucket default corrected to 2; palette switched to ColorBrewer
  YlGnBu 3-class (`#edf8b1` / `#7fcdbb` / `#2c7fb8`), fill at 80% transparent,
  outline same hue at full opacity, widths 0.5 / 1.0 / 1.5 mm
- `layers/mall_buffers.py` — fixed NaN `mall_name` for malls 1–9: shapefile
  stores `id` zero-padded (`"01"`–`"09"`) but `mall_names.csv` has bare
  integers; normalise both sides via `.astype(int).astype(str)` before merge
- `layers/target_tracts.py` — added `M22_39` to output field list
- `project.py` — added `mall_buffer_people` to `spec_all` and `spec_near_malls`

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

## Step 4c — Add EPSG:4326 ↔ EPSG:2227 to transform context

**Prompt:** every time I reload the QGIS project I have to click through a
dialog to project Shopping Malls from EPSG:2227 to EPSG:4326

**What this does:**

QGIS uses EPSG:4326 (WGS 84) internally for the geographic coordinate
display in the status bar and for the secondary `mAreaCanvas` in the base
template, even when no project layer uses that CRS. Without a stored
preference, QGIS presents a "Select Datum Transformation" dialog on every
open because PROJ offers multiple paths between NAD83 (underlying
EPSG:2227) and WGS84.

Added a second `<srcDest>` entry to `styles/base.qgs` for EPSG:4326 →
EPSG:2227, using the same NADCON 5.0 grid-shift pipeline
(`us_noaa_cnhpgn.tif`) with `allowFallback="1"`. Also restored
`census_tracts_males_22_39` and `roads` to `project.py` as hidden layers
(`visible=False`) so the build dependency chain works — `make build --force`
was failing with `KeyError: 'census_tracts_males_22_39'` because those
layers had been removed.

**Files changed:**
- `styles/base.qgs` — added EPSG:4326 ↔ EPSG:2227 srcDest entry
- `project.py` — restored hidden dependency layers; added metadata comment
  to `malls.py`

---

## Step 24 — Spatial join: mall buffers × census tracts

**Prompt:** create a new layer: join the mall buffer layer with the
males_22_39_pct_over20 layer with spatial intersects; add Total and M22_39
fields

**What this does:**

Created `mall_buffer_tracts` as a derived layer. `males_22_39_pct_over20.shp`
omits `Total` and `M22_39` (dropped during processing), so the layer depends
on `mall_buffers` and `census_tracts_males_22_39` (the full source shapefiles)
instead. The function:

1. Reads `output/mall_buffers.shp`; keeps `id` (renamed `mall_id`) and
   `mall_name`.
2. Reads `data/M22_39yrs.shp`; computes `pct_m22_39 = M22_39 / Total * 100`;
   filters to tracts where `Total > 0` and `pct_m22_39 > 20` — replicating
   the `males_22_39_pct_over20` threshold inline.
3. `gpd.sjoin(tr, buf, how="inner", predicate="intersects")` — one output row
   per (census tract × mall buffer) pair. Geometry is the census tract polygon.

Output fields: `GEOID`, `NAMELSAD`, `Total`, `M22_39`, `pct_m22_39`,
`mall_id`, `mall_name`. Written to `output/mall_buffer_tracts.shp`.

Styled as a warm yellow-orange fill (`255,200,50,180`) to visually distinguish
it from the blue census tracts and green buffers.

Layer order (top → bottom):

| Layer | Visible |
|-------|---------|
| `malls` | yes |
| `mall_buffers` | yes |
| `mall_buffer_tracts` | yes |
| `males_22_39_pct_over20` | yes |
| `major_roads` | yes |
| `census_tracts_males_22_39` | no (dependency) |
| `roads` | no (dependency) |
| `cartodb_positron` | yes |

**Files created/changed:**
- `layers/mall_buffer_tracts.py` — spatial join function + SingleSymbol renderer
- `project.py` — added `mall_buffer_tracts` between `mall_buffers` and
  `males_22_39_pct_over20`

---

## Step 25 — Rename layers for consistency

**Prompt:** clean up names; update code and text references for these layers
in projects/lab4/layers

**What this does:**

Renamed three layer files, Python variables, layer IDs, human-readable names,
output shapefile paths, and `depends_on` references throughout:

| Old file | New file | Old id | New id |
|----------|----------|--------|--------|
| `census_tracts_males_22_39.py` | `census_tracts.py` | `census_tracts_males_22_39` | `census_tracts` |
| `males_22_39_pct_over20.py` | `target_tracts.py` | `males_22_39_pct_over20` | `target_tracts` |
| `mall_buffer_tracts.py` | `mall_target_intersect.py` | `mall_buffer_tracts` | `mall_target_intersect` |

Output shapefile paths updated:
- `output/males_22_39_pct_over20.shp` → `output/target_tracts.shp`
- `output/mall_buffer_tracts.shp` → `output/mall_target_intersect.shp`

`depends_on` chain updated: `target_tracts` now depends on `["census_tracts"]`;
`mall_target_intersect` now depends on `["mall_buffers", "census_tracts"]`.
`project.py` imports and layer list updated; `.layerss` typo in previous
import fixed.

**Files created/changed:**
- `layers/census_tracts.py` — renamed from `census_tracts_males_22_39.py`
- `layers/target_tracts.py` — renamed from `males_22_39_pct_over20.py`
- `layers/mall_target_intersect.py` — renamed from `mall_buffer_tracts.py`
- `project.py` — updated all imports and layer references

---

## Step 23 — Add mall 5-mile buffer layer; join mall_names.csv

**Prompt:** from malls layer, create a 5 mile buffer polygons around each
feature, and style as light green 50% transparent; join with mall_names.csv
on ID

**What this does:**

Created `mall_buffers` as a derived layer with a `PythonAction` that reads
`output/malls.shp`, buffers each point by 26,400 ft (5 miles × 5,280 survey
ft/mile in EPSG:2227), then left-joins `data/mall_names.csv` on `id` to add
a `mall_name` field. Output written to `output/mall_buffers.shp`.

`mall_names.csv` has a UTF-8 BOM (read with `encoding="utf-8-sig"`); `ID`
is cast to `str` before the merge to match the string `id` field in the
shapefile. Output fields: `id`, `name`, `city`, `mall_name`, geometry.

Styled as a `SimpleFill` with CSS lightgreen fill (`144,238,144,128`, alpha
128 ≈ 50% opacity) and a slightly darker green outline (`80,160,80,255`).
Layer sits between `malls` (above) and `males_22_39_pct_over20` (below).

Layer order (top → bottom):

| Layer | Visible |
|-------|---------|
| `malls` | yes |
| `mall_buffers` | yes |
| `males_22_39_pct_over20` | yes |
| `major_roads` | yes |
| `census_tracts_males_22_39` | no (dependency) |
| `roads` | no (dependency) |
| `cartodb_positron` | yes |

**Files created/changed:**
- `layers/mall_buffers.py` — buffer + join function; `mall_name` field added;
  `project_data_dir` + `pandas` imports added
- `project.py` — added `mall_buffers` between `malls` and `males_22_39_pct_over20`

---

## Step 11 — Geocode malls.csv to create Shopping Malls layer

**Prompt:** geocode data in projects/lab4/data/malls.csv to create a new layer

**What this does:**

Geocoded 11 Bay Area shopping mall addresses from `data/malls.csv` using
Nominatim (OpenStreetMap geocoder, 1 req/s rate limit). All 11 addresses
resolved successfully. Output reprojected from EPSG:4326 (geocoder native)
to EPSG:2227.

CSV fields: `ID`, `Street`, `City`, `State`, `Zip`. File has a UTF-8 BOM
(read with `encoding="utf-8-sig"`). Output shapefile retains `id`, `name`,
`city`.

Styled as 4 mm red circles with dark-red outline, on top of all other layers.

Output shapefile metadata: 11 points, EPSG:2227, fields `id`/`name`/`city`,
extent x=5,990,284–6,175,052 ft · y=1,932,559–2,189,415 ft.

**Files created/changed:**
- `layers/malls.py` — geocoding PythonAction + SimpleMarker renderer; header
  comment with output shapefile metadata
- `project.py` — added `malls` as top layer

---

## Step 22 — Fix SimpleMarker not rendering in QGIS 3.44 (alidade render.py)

**Prompt:** malls layer does not show any markers; right-click shows no style or
properties; compare project.qgs vs project_qgis.qgs

**What this does:**

Diffed the generated `project.qgs` malls maplayer against `project_qgis.qgs`
(saved by QGIS from a working malls import). Three diffs were found in the
SimpleMarker symbol layer that caused QGIS 3.44 to silently fail to render:

1. **`cap_style` missing**: QGIS 3.44 added `cap_style` as a required
   SimpleMarker property. Without it, the symbol layer is invalid and QGIS
   renders nothing. Added `cap_style: str = "square"` to `SimpleMarker` in
   `alidade/models.py` and rendered it in `_render_symbol_layer`.

2. **Symbol layer `id` was empty**: QGIS 3.44 assigns each symbol layer a UUID
   `id` attribute; QGIS 3.30+ may require a non-empty value for registry
   lookup. Changed `id=""` to a generated `"{uuid}"` in `_render_symbol_layer`.

3. **Float formatting**: Properties like `size`, `angle`, `outline_width` were
   formatted with `str()` producing `"4.0"`, `"0.0"`. QGIS saves `"4"`, `"0"`.
   Switched to `f"{val:g}"` format which drops the unnecessary `.0` suffix.

All three fixes applied uniformly in `alidade/render.py` `_render_symbol_layer`
for the `SimpleMarker` branch.

**Files changed:**
- `alidade/models.py` — `cap_style: str = "square"` added to `SimpleMarker`
- `alidade/render.py` — `_render_symbol_layer`: UUID id, `cap_style` property,
  `:g` float formatting for `angle`, `size`, `outline_width`

---

## Step 21 — Fix malls layer: add SimpleMarker renderer

**Prompt:** malls layer does not show any markers in QGIS; compare to
high_schools_2227 in XY_projections; want each feature to draw as a simple marker

**What this does:**

The malls layer had `SimpleMarker`/`SingleSymbol`/`Symbol` imported but never
wired into the `Layer` definition — `renderer` was `None`. Without a
`<renderer-v2>` element in the generated maplayer XML, QGIS renders nothing
(unlike layers with no renderer where QGIS picks a random default, the
`_build_vector_maplayer` path in render.py emits no renderer element at all
when `layer.renderer is None`).

Added `renderer=SingleSymbol(...)` with a red circle `SimpleMarker` (4 mm,
dark-red outline) to match the styling already implied by the imports.

**Files changed:**
- `layers/malls.py` — added `renderer=SingleSymbol(symbol=Symbol(...))` with
  `SimpleMarker(color="220,50,50,255", size=4.0, outline_color="140,20,20,255",
  outline_width=0.5)`

---

## Step 20 — Replace openstreetmap layer with CartoDB Positron from sample

**Prompt:** add cartodb basemap layer to lab4 from example in sample

**What this does:**

Replaced the ad-hoc `openstreetmap` layer (which used `osm_gray_scale.xml` and
a `crs=EPSG:3857&format&type=xyz` source string) with the canonical
`cartodb_positron` layer copied directly from `projects/sample`. The sample
layer uses the standard `http-header:referer=&type=xyz&...` source format and
its own `cartodb_positron.xml` style.

Both layers hit the same CartoDB Positron tile URL; the switch standardises
the layer definition across projects and uses the officially maintained sample
as the reference.

Layer order (top → bottom):

| Layer | Visible |
|-------|---------|
| `malls` | yes |
| `males_22_39_pct_over20` | yes |
| `major_roads` | yes |
| `census_tracts_males_22_39` | no (dependency) |
| `roads` | no (dependency) |
| `cartodb_positron` | yes |

**Files created/changed:**
- `layers/cartodb_positron.py` — copied from projects/sample
- `styles/cartodb_positron.xml` — copied from projects/sample
- `project.py` — replaced `openstreetmap` import/reference with `cartodb_positron`

---

## Step 19 — Fix blank canvas CRS causing Saudi Arabia basemap and transform dialog

**Prompt:** make clean && make build; opening project requests 2227→4326 transform
and basemap shows Saudi Arabia again

**What this does:**

After `make clean`, `_update_crs` in `alidade/render.py` only wrote the authid
into `projectCrs/spatialrefsys/authid` but left `theMapCanvas/destinationsrs/
spatialrefsys` completely blank. QGIS treats `destinationsrs` as the canvas CRS:

- With a blank canvas CRS, the WMS provider sends raw EPSG:2227 US survey foot
  coordinates (~5.9M, ~2.0M) to the tile server as EPSG:3857 meters. That location
  is the Arabian Peninsula — hence Saudi Arabia.
- With a blank canvas CRS, QGIS cannot match the `(EPSG:2227, EPSG:4326)` entry
  in the transform context, so it presents the datum selection dialog on open.

Added `_fill_spatialrefsys()` helper to `alidade/render.py` that populates an
existing `<spatialrefsys>` element in-place using pyproj (WKT, authid, description,
geographicflag, srid). Updated `_update_crs()` to call it for both
`projectCrs/spatialrefsys` and `theMapCanvas/destinationsrs/spatialrefsys`.

Also restored `styles/osm_gray_scale.xml` (was lost from a previous `make clean`
— the file must live in `styles/` and is not regenerated by the build).

Verified: `dump_project_crs_and_canvas()` now shows `destinationsrs authid:
'EPSG:2227'` in the generated project.qgs.

**Files changed:**
- `alidade/render.py` — `_fill_spatialrefsys()` helper; `_update_crs()` now
  populates canvas destinationsrs in addition to projectCrs
- `styles/osm_gray_scale.xml` — restored (copy from XY_projections)

---

## Step 18 — Fix symbol colors for QGIS 3.30+ (alidade render.py)

**Prompt:** malls layer exists but symbols do not show when loaded from
output/project.qgs; compare project files to determine fix

**What this does:**

Compared the generated `output/project.qgs` with `output/project_qgis.qgs`
(saved by QGIS after manually importing the shapefile). Diff showed two bugs
in `alidade/render.py`:

1. **Color format**: QGIS 3.30+ requires the extended color format
   `R,G,B,A,rgb:r_norm,g_norm,b_norm,a_norm`. The generator passed raw
   `R,G,B,A` strings, which QGIS 3.44 no longer renders.

2. **Alpha format**: `str(sym.alpha)` with `alpha=1.0` produced `"1.0"`;
   QGIS saves `"1"`. Fixed with `f"{sym.alpha:g}"`.

Added `_color()` helper to `alidade/render.py` that upgrades bare `R,G,B,A`
strings to the extended format using `%.7g` normalization (matching QGIS's
output). Applied it to all color fields across SimpleFill, SimpleLine,
SvgMarker, and SimpleMarker. Existing hardcoded colors that already contain
`rgb:` are passed through unchanged.

**Files changed:**
- `alidade/render.py` — `_color()` helper + applied to all symbol color props;
  `alpha` serialization fixed

---

## Step 17 — Switch basemap to CartoDB Positron

**Prompt:** basemap not visible in QGIS

**What this does:**

The Wikimedia gray-scale tile service (`tiles.wmflabs.org/bw-mapnik`) was
shut down in 2020; all requests return errors so the layer renders blank.

Switched to CartoDB Positron (`basemaps.cartocdn.com/light_all`), a
light-gray basemap that is actively maintained and requires no API key.
Updated `zmax` from 18 to 20 to match Positron's available zoom range.

**Files changed:**
- `layers/openstreetmap.py` — tile URL updated to CartoDB Positron

---

## Step 16 — Revert generated files back to output/

**Prompt:** revert to generating files to output/ subdir

**What this does:**

Reverted Step 13's data-path change. Generated shapefiles (`malls`,
`males_22_39_pct_over20`, `major_roads`) moved back to `output/`; source
and output paths in all three layer files restored.

**Files changed:**
- `layers/malls.py` — source + output path: `data/` → `output/`
- `layers/males_22_39_pct_over20.py` — same
- `layers/major_roads.py` — same

---

## Step 15 — Add EPSG:2227 → EPSG:4326 to transform context

**Prompt:** QGIS asking for preferred transform from 2227 to 4326 for Shopping
Malls layer; update base.qgs and rebuild

**What this does:**

`QgsCoordinateTransformContext` performs directional lookups: `(src, dest)` is
a distinct key from `(dest, src)`. The context already had `(EPSG:4326 →
EPSG:2227)` but not the reverse, so QGIS asked every time it needed to convert
malls coordinates to geographic (e.g. for `mAreaCanvas` extent).

Added a third `<srcDest>` entry to `styles/base.qgs` with src=EPSG:2227 and
dest=EPSG:4326. The `coordinateOp` is the inverse of the existing 4326→2227
pipeline: steps reversed with `inv` flags toggled, using the same NADCON
CNHPGN grid shift, `allowFallback="1"`.

Transform context now covers all three required pairs:
- EPSG:4326 → EPSG:2227
- EPSG:2227 → EPSG:4326  ← new
- EPSG:3857 → EPSG:2227

**Files changed:**
- `styles/base.qgs` — added EPSG:2227 → EPSG:4326 srcDest entry

---

## Step 14 — Switch basemap to OSM gray scale

**Prompt:** update lab4 to use osm_gray_scale as in XY_projections project

**What this does:**

Replaced the standard OSM color tiles with the Wikimedia gray-scale tile layer
(`tiles.wmflabs.org/bw-mapnik`). The gray-scale basemap reduces visual
competition with the colored census-tract fills.

Copied `styles/osm_gray_scale.xml` from the XY_projections project (unchanged).
Updated `layers/openstreetmap.py` to use the new tile URL and `style_xml`.
Layer id, variable name, and import in `project.py` are unchanged.

**Files changed:**
- `layers/openstreetmap.py` — tile URL + style_xml updated
- `styles/osm_gray_scale.xml` — copied from XY_projections

---

## Step 13 — CRS audit and move generated shapefiles to data/

**Prompt:** help me escape map projection hell; review project content and advise
on a sane setup; generated layer data files should go to data/ not output/

**What this does:**

Added `audit_lab4_crs()` to `claude.py` to confirm CRS consistency.
Audit results — everything clean:
- All five shapefiles resolve to EPSG:2227
- Project CRS: EPSG:2227
- Transform context in `output/project.qgs` pre-fills both pairs that would
  trigger dialogs: EPSG:4326↔2227 and EPSG:3857↔2227, both with `allowFallback=1`
- OSM layer declared EPSG:3857 with native WMS/XYZ provider; QGIS reprojects
  the viewport extent before fetching tiles — no misalignment

Moved generated shapefiles from `output/` to `data/`, where they sit alongside
the source shapefiles. `output/` now contains only `project.qgs`. Updated
`source` and `output` paths in all three derived layer files; rebuilt project.

**Files changed:**
- `layers/malls.py` — `source` and `output` path: `output/` → `data/`
- `layers/males_22_39_pct_over20.py` — same
- `layers/major_roads.py` — same

---

## Step 12 — Add project_data_dir() helper to alidade

**Prompt:** _CSV = Path(__file__).parent.parent / "data" / "malls.csv" is messy;
add a helper function to alidade to return data path from project files

**What this does:**

Added `project_data_dir(layer_file)` to `alidade/__init__.py`. Takes
`__file__` from a layer file and returns the `data/` directory, assuming
the standard layout `projects/<name>/layers/<layer>.py` →
`projects/<name>/data/`.

Updated `malls.py` to use it:
    _CSV = project_data_dir(__file__) / "malls.csv"

**Files changed:**
- `alidade/__init__.py` — new `project_data_dir()` helper
- `layers/malls.py` — replaced `Path(__file__).parent.parent / "data"` with helper

---

## Step 4e — Thick blue polygon outline

**Prompt:** style all males_22_39_pct_over20 polygons with a thick blue outline
(same for all rule buckets)

**What this does:**

Changed `_OUTLINE` from dark-gray semi-transparent (`35,35,35,128`) to solid
blue (`0,80,200,255`) and increased `outline_width` from 0.26 mm to 1.0 mm.
The same `_symbol()` helper is shared by all five rule buckets, so the change
applies uniformly.

**Files changed:**
- `layers/males_22_39_pct_over20.py` — `_OUTLINE` color + `outline_width`

---

## Step 4d — Set fill transparency to 50%

**Prompt:** update transparency of males_22_39_pct_over20 fill to 50%

**What this does:**

Changed the alpha channel of all five `_BLUES` color strings from 255
(opaque) to 128 (≈50% opacity), so the census tract fills are semi-transparent
and the OSM basemap and roads show through.

**Files changed:**
- `layers/males_22_39_pct_over20.py` — `_BLUES` alpha 255 → 128

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

## Step 30 — Apply shared census color scheme to mall_target_intersect

**Prompt:** update mall_target_intersect layer to use the shared census color
scheme used by census_tracts layer

**What this does:**

Replaced the flat yellow-orange `SingleSymbol` renderer on `mall_target_intersect`
with a `GraduatedRenderer` on `M22_39` using the same `CENSUS_BUCKETS` palette
and Jenks break constants as `census_tracts`. The layer shares the same scale
(`_MIN`–`_MAX`, breaks at 424/740/1162/2003) so features read at the same
magnitude across both layers. Outline thinned to match (`0.1 mm`,
`"180,180,180,120"`).

**Files changed:**
- `layers/mall_target_intersect.py` — `SingleSymbol` → `GraduatedRenderer`
  on `M22_39`; `CENSUS_BUCKETS` + break constants imported/defined;
  `SimpleFill`/`SingleSymbol`/`Symbol` imports removed

---

## Step 29 — Rename BLUES → CENSUS_BUCKETS; switch to ColorBrewer Purples

**Prompt:** in util.py, update BLUES to a color brewer purple scale, and rename
from BLUES to CENSUS_BUCKETS

**What this does:**

Replaced the 5-class ColorBrewer Blues palette with ColorBrewer Purples and
renamed the constant throughout.

| Class | Old (Blues) | New (Purples) |
|-------|-------------|---------------|
| 1 | `#eff3ff` | `#f2f0f7` |
| 2 | `#bdd7e7` | `#cbc9e2` |
| 3 | `#6baed6` | `#9e9ac8` |
| 4 | `#3182bd` | `#756bb1` |
| 5 | `#08519c` | `#54278f` |

**Files changed:**
- `util.py` — palette replaced; `BLUES` → `CENSUS_BUCKETS`
- `layers/census_tracts.py` — import and usage updated
- `layers/target_tracts.py` — import and usage updated

---

## Step 28 — Split census_tracts into raw source and filtered layer

**Prompt:** add a new layer `census_tracts`: filter census_tracts_raw to keep
only tracts where Total > 0; move all styling from raw version to new layer

**What this does:**

Split the single census tract layer into two:

- `census_tracts_raw` — bare source layer pointing directly to
  `data/M22_39yrs.shp` (all 1,620 tracts including zero-population ones).
  No renderer; `visible=False`. Serves only as a build dependency.
- `census_tracts` — derived layer (`output/census_tracts.shp`, 1,617 tracts)
  produced by filtering `census_tracts_raw` to `Total > 0`. Carries the
  graduated Blues renderer and Jenks break constants moved from the raw file.
  `depends_on=["census_tracts_raw"]`.

`project.py` updated to import and list both layers; `census_tracts_raw` sits
below `census_tracts` in the layer order.

**Files created/changed:**
- `layers/census_tracts_raw.py` — stripped to a plain dependency layer;
  variable renamed from `census_tracts` to `census_tracts_raw`
- `layers/census_tracts.py` — new; `filter_nonzero_population` processing
  step + graduated renderer moved from raw layer
- `project.py` — added `census_tracts_raw` import and layer reference

---

## Step 27 — Shared palette and Jenks breaks for census_tracts

**Prompt:** pull the _BLUES colors out of target_tracts.py into projects/lab4/util.py
and reuse the same colors in census_tracts.py; also update census_tracts.py to
calculate breaks with Jenks and pull out into constants like target_tracts.py

**What this does:**

Created `util.py` to hold the shared ColorBrewer Blues palette. Updated both
layer files to import from it, and replaced the approximate M22_39 breaks in
`census_tracts.py` with Jenks natural breaks computed from the actual data.

Jenks natural breaks on M22_39 (all 1,620 tracts, computed with mapclassify):

| Class | Range | Count | Color |
|-------|-------|------:|-------|
| 1 | 0 – 424 | 561 | `#eff3ff` (lightest) |
| 2 | 424 – 740 | 594 | `#bdd7e7` |
| 3 | 740 – 1,162 | 367 | `#6baed6` |
| 4 | 1,162 – 2,003 | 91 | `#3182bd` |
| 5 | 2,003+ | 7 | `#08519c` (darkest) |

Break values extracted as `_MIN`, `_B1`–`_B4`, `_MAX` constants following the
same pattern as `target_tracts.py`. Both layers now share the same 5-class Blues
palette (alpha 128, 50% opacity) via `util.BLUES`.

**Files created/changed:**
- `util.py` — new; `_BLUES` 5-class ColorBrewer Blues palette
- `layers/target_tracts.py` — replaced inline `_BLUES` definition with
  `from projects.lab4.util import _BLUES`
- `layers/census_tracts.py` — replaced approximate YlOrRd colors and hardcoded
  breaks with `_BLUES` from util and Jenks break constants

---

## Step 26 — Print layout: overview map (print_overview.qpt)

**Prompt:** implement print_overview to generate a print.qpt spec: set scale,
set specified layers to visible, others to hidden; make requested style changes
to source layer files not in main.py

**What this does:**

Added `GraduatedRenderer` support to the alidade render pipeline, updated
`census_tracts` to use a 5-class YlOrRd graduated color scheme on `M22_39`,
and implemented `print_overview()` in `main.py` to render `print_overview.qpt`
at 1:600,000 scale.

**Alidade model/render changes (`alidade/`):**

- `models.py` — new `GraduatedRange` and `GraduatedRenderer` models added to
  the `Renderer` union; `PrintMapFrame.scale: int | None` added so a fixed
  scale denominator can be embedded in the QPT map item.
- `render.py` — `_render_graduated_renderer()` serializes `GraduatedRenderer`
  to a `<renderer-v2 type="graduatedSymbol">` element with per-range symbols
  (SimpleFill), ranges, source-symbol, and gradient colorramp elements.
  `_qpt_map_frame()` now writes `scale=` attribute when `mf.scale` is set.
  `render_print_layout()` now writes `output/<pl.name>.qpt` instead of the
  hardcoded `output/print.qpt`, so multiple layouts can coexist.

**Layer style change:**

`census_tracts` renderer changed from a flat orange `SingleSymbol` to a
`GraduatedRenderer` on `M22_39` using a 5-class YlOrRd ramp (ColorBrewer),
alpha 180 (≈70% opacity) so the Positron basemap shows through. Thin light-
gray outline (0.1 mm, 120 opacity) instead of the previous dark-brown.

| Class | Range | Color (RGBA) |
|-------|-------|-------------|
| 1 | 0 – 200 | 255,255,178,180 |
| 2 | 200 – 400 | 254,204,92,180 |
| 3 | 400 – 650 | 253,141,60,180 |
| 4 | 650 – 1,000 | 240,59,32,180 |
| 5 | 1,000+ | 189,0,38,180 |

Breaks are approximate quantiles for Bay Area/Central Valley tracts; adjust
if the data distribution skews significantly from the estimates.

**`main.py` `print_overview()`:**

Loads the base project spec, overrides layer visibility to show only
`census_tracts`, `malls`, `major_roads`, and `cartodb_positron`, then calls
`render_print_layout` with a `PrintLayout(name="print_overview", ...)` spec
at 1:600,000 scale. Scale bar set to 50 mi segments.

Run from the repo root:

```bash
uv run python projects/lab4/main.py
# → Wrote projects/lab4/output/print_overview.qpt
```

Then export to PDF from the QGIS Python console:

```python
_pdf = open("/path/to/alidade/alidade/util/export_pdf.py").read()
print_prefix = "print_overview"
exec(_pdf)
```

**Files created/changed:**
- `alidade/models.py` — `GraduatedRange`, `GraduatedRenderer`, `PrintMapFrame.scale`
- `alidade/render.py` — `_render_graduated_renderer()`, QPT filename uses
  `pl.name`, `_qpt_map_frame` writes scale attribute
- `layers/census_tracts.py` — `GraduatedRenderer` on `M22_39` (YlOrRd 5-class)
- `main.py` — `print_overview()` implemented; module-level imports added

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
