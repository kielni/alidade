# Goats — workflow

Habitat suitability analysis for goat grazing at Alum Rock Park. Follow
these steps from a fresh checkout to reproduce the full project.

CRS: EPSG:26910 (NAD83 / UTM Zone 10N).
Extent (padded 5%): `(603628.0, 4138828.9, 607872.9, 4140758.2)`.

---

## Step 1 — Acquire source data

Downloaded park boundary from OpenStreetMap via Overpass Turbo
(`https://overpass-turbo.eu`), querying
`relation["name"="Alum Rock Park"]["leisure"="park"]` and
`way["name"="Alum Rock Park"]["leisure"="park"]`.
Saved as `data/park_boundary.geojson`.

Downloaded stream network from OSM via Overpass Turbo, querying
`way["waterway"~"stream|river|canal|creek"]`, `way["natural"="water"]`, and
matching relation types. 36 LineString features.
Saved as `data/water.geojson`.

Downloaded road and trail network from OSM via Overpass Turbo, querying hiking
paths (`highway="path|footway|track"`, `route="hiking"`, `sac_scale`) and roads
(`highway=motorway|trunk|primary|secondary|tertiary|unclassified|residential|service`).
1537 LineStrings + 1 MultiLineString; the one Polygon feature is filtered out
during processing. Saved as `data/roads_trails.geojson`.

Downloaded fine-scale vegetation GDB (layer `CRUZ_CLARA_FINESCALE_VEG_6_15_2023`)
from Santa Cruz / Santa Clara County, 2020 NVC classification, EPSG:6420,
309,785 polygons county-wide. Saved as `data/fine_scale_vegetation.gdb`.

Downloaded USGS 1/3 arc-second DEM (EPSG:4269) from
`https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/historical/n38w122/USGS_13_n38w122_20250826.tif`.
Saved as `data/USGS_13_n38w122_20250826.tif`.

Field-recorded GPX tracks walking the perimeter of the developed area
(buildings, playgrounds, picnic areas, parking lots).
Saved as `data/Alum_Rock_developed_area.gpx`.

Field-recorded GPS waypoints for candidate staging areas (parking lots with
trailer access). Saved as `data/staging.geojson`.

**Files created:**
- `data/park_boundary.geojson`
- `data/water.geojson`
- `data/roads_trails.geojson`
- `data/fine_scale_vegetation.gdb/`
- `data/USGS_13_n38w122_20250826.tif`
- `data/Alum_Rock_developed_area.gpx`
- `data/staging.geojson`

---

## Step 2 — Project scaffold and basemaps

Created project scaffold. Two basemap layers: CartoDB Positron
(`basemaps.cartocdn.com/light_all`) used in most maps; ESRI World Imagery
(`server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer`)
used in `map_detail` for satellite context.

**Files created:**
- `__init__.py`, `util.py`
- `project.py`
- `layers/__init__.py`
- `layers/basemap.py` — CartoDB Positron XYZ tile service
- `layers/basemap_satellite.py` — ESRI World Imagery XYZ tile service

---

## Step 3 — Clip border

Buffered park boundary by 100 ft (30.48 m) and dissolved to a single polygon.
Used as clip mask for all raster and vector inputs so derived data extends just
past the park boundary edge; the suitability layer clips back to exact park
geometry at the end of processing.

**Files created:**
- `layers/border.py` — `create_border`: `gdf.buffer(30.48)` after dissolve;
  output `output/border.gpkg`

---

## Step 4 — Developed area

Read GPX `tracks` layer, merged into a single LineString via `linemerge`,
simplified 10 m (Douglas-Peucker), closed the ring, converted to Polygon,
reprojected to EPSG:26910. This polygon marks high-human-use areas used as
a priority factor in the suitability overlay.

**Files created:**
- `layers/developed_area.py` — `convert_developed_area`;
  output `output/developed_area.gpkg`

---

## Step 5 — Elevation

Reprojected USGS DEM from EPSG:4269 to EPSG:26910 using `gdalwarp`, cutline
clipped to the clip border, bilinear resampling. Nodata set to −999999.

**Files created:**
- `layers/elevation.py` — `crop_elevation`:
  `gdalwarp -s_srs EPSG:4269 -t_srs EPSG:26910 -cutline border.gpkg -r bilinear`;
  output `output/elevation.tif`

---

## Step 6 — Streams

Reprojected `data/water.geojson` to EPSG:26910 and clipped to clip border.
Retained only `@id` and `name` columns to keep output compact.

**Files created:**
- `layers/water.py` — `clip_water`; output `output/water.shp`

---

## Step 7 — Roads and trails

Reprojected `data/roads_trails.geojson` to EPSG:26910, filtered to LineString
and MultiLineString only (drops the one Polygon feature), clipped to clip border.

**Files created:**
- `layers/roads_trails.py` — `clip_roads_trails`; output `output/roads_trails.shp`

---

## Step 8 — Fine-scale vegetation

Read layer `CRUZ_CLARA_FINESCALE_VEG_6_15_2023` from the GDB, reprojected from
EPSG:6420 to EPSG:26910, clipped to clip border, dissolved by `ENHANCED_LIFEFORM`
to merge adjacent same-category polygons. Retains only `ENHANCED_LIFEFORM` and
geometry; 343 source polygons collapse to 7 suitability zones. A second layer
(`vegetation_highlight`) shares the same output file with a different renderer
showing only 3 zones for the detail map.

**Files created:**
- `layers/vegetation.py` — `clip_vegetation`; output `output/vegetation.gpkg`
- `layers/vegetation_highlight.py` — no processing step, shared output

---

## Step 9 — Slope

Ran `gdaldem slope -p` on `elevation.tif` to produce percent slope, then
`gdal_calc.py` to reclassify into 4 byte classes: 1 = flat/gentle (0–15%),
2 = moderate (15–27%), 3 = steep (27–58%), 4 = too steep (58%+). Breaks chosen
to match goat grazing literature; 58% is the practical limit for safe travel
with a handler. Colors: Flat #1a9641 · Moderate #ffffbf · Steep #fdae61 ·
Too steep #ddd0c0.

**Files created:**
- `layers/slope.py` — `build_slope`: temp percent-slope file → `gdal_calc`
  reclassify; output `output/slope.tif`

---

## Step 10 — Priority buffers

Two priority buffers used as factors in the suitability overlay. Pixels inside
each buffer score 4; pixels outside score 1.

- `priority_developed`: 100 ft (30.48 m) buffer around developed area, unioned,
  clipped to park boundary. Orange fill at 50% opacity.
- `priority_roads_trails`: 30 ft (9.144 m) buffer along roads and trails, unioned,
  clipped. Yellow fill at 50% opacity.

Goats prioritize areas near roads and developed zones because handlers can access
them quickly for daily checks.

**Files created:**
- `layers/priority_developed.py` — `build_priority_developed`;
  output `output/priority_developed.gpkg`
- `layers/priority_roads_trails.py` — `build_priority_roads_trails`;
  output `output/priority_roads_trails.gpkg`

---

## Step 11 — Riparian exclusion buffer

Buffered streams by 100 ft (30.48 m), unioned, clipped to park boundary. Used
as a hard zero mask in the suitability overlay (not a weighted factor) so that
riparian vegetation is never scored as grazeable regardless of other inputs.
Blue fill at 50% opacity.

**Files created:**
- `layers/exclude_water_vegetation.py` — `build_exclusion`;
  output `output/exclude_water_vegetation.gpkg`

---

## Step 12 — Suitability raster

Weighted overlay: rasterized vegetation, priority_developed, and
priority_roads_trails to the slope.tif grid (~10 m, EPSG:26910). Weights:
slope 25% + vegetation 25% + developed priority 25% + roads/trails priority 25%.

Slope is scored *inversely* (steeper = higher suitability) because goats prefer
sloped terrain: slope class 1 → suit 2, class 2 → 3, class 3 → 4, class 4 → 0.
Vegetation mapping: Shrub → 4, Non-native/native Herbaceous → 3, Forest types → 1,
Riparian Forest/Developed → 0 (hard exclude).

After the weighted sum, pixels are zeroed where slope class = 4, vegetation = 0,
or riparian exclusion = 1. Clipped to exact park boundary via `geometry_mask`
to remove the 100 ft clip border overhang. Jenks natural breaks (k=4) on non-zero
pixels → byte raster with classes 1–4 (0 = excluded). Colors: Purples 4-class
#f2f0f7 · #cbc9e2 · #9e9ac8 · #6a51a3.

**Files created:**
- `layers/suitability.py` — `build_suitability`; output `output/suitability.tif`

---

## Step 13 — Grazeable patches

Vectorized non-zero suitability pixels into scored grazeable patch polygons.

Processing pipeline:
1. Vectorize contiguous non-zero regions; drop < 500 m²
2. Morphological closing (+10 m / −10 m buffer) to merge adjacent pixels and
   smooth staircase raster edges without filling real terrain notches
3. Voronoi-split patches > 120,000 m² using k-means cluster centers as seeds —
   split lines run through low-suitability terrain gaps
4. Subtract riparian exclusion buffer; re-explode; drop fragments < 500 m²
5. Clip to exact park boundary

Scoring: `patch_score = suitability_sum / perimeter` (rewards compact
high-suitability zones over elongated low-value strips). Jenks 4-class on
patch_score → `patch_class` 1–4. Colors: same Purples 4-class as suitability.

**Files created:**
- `layers/patches.py` — `vectorize_patches`; output `output/patches.gpkg`

---

## Step 14 — Staging area ranking

Distance-decay score over grazeable patches:
`score = Σ(patch_score / distance)` summed over High and Very high patches only
(`patch_class ≥ 3`). Low-quality patches (class 1–2) are excluded so marginal
terrain does not inflate scores for staging areas near poor zones. Distance
clamped ≥ 50 m so patches inside a staging lot don't contribute disproportionately.
Rank 1 = highest score. Colors: YlGn 3-class diamond markers.

**Files created:**
- `layers/staging_ranked.py` — `build_staging_ranked`;
  output `output/staging_ranked.gpkg`

---

## Step 15 — Experimental layers (not in current spec)

Two approaches explored and not retained:

`layers/basins.py` — watershed basin delineation using pysheds (D8 flow
direction and accumulation → stream network → basin polygons). Scored by
suitability_sum per basin. Not retained because basins follow drainage divides
rather than accessible grazing zones.

`layers/targets.py` — alternative staging scorer using rasterstats.zonal_stats
within a 1-mile buffer (suit_mean per point). Not retained because the uniform
buffer does not distinguish which high-quality zones are reachable on foot;
replaced by the distance-decay approach in `staging_ranked.py`.

---

## Step 16 — Multiple output maps

Defined 8 sub-maps in `project.py` sharing layer objects, each focused on one
analysis stage.

| ID | Title | Key layers |
|---|---|---|
| `park` | Alum Rock Park | boundary, staging, streams, roads, developed |
| `slope` | Slopes | slope overlay |
| `vegetation` | Vegetation | vegetation classification |
| `zones` | Priority and Exclusion Zones | priority + exclusion buffers |
| `suitability` | Grazing Suitability | suitability raster |
| `patches` | Grazeable Patches | patches + staging |
| `targets_cluster` | Grazing Targets | patches + staging_ranked |
| `detail` | Rustic Lands detail | satellite basemap, vegetation highlight, staging_ranked |

`spec = map_all` assembles all layers for development; the named sub-maps
are used for final output and the story map.

**Files changed:**
- `project.py` — all 8 map definitions; `spec = map_all`

---

## Step 17 — README auto-generation

Added `source_description` and `source_origin` fields to the `Layer` model.
Updated `readme.py` to generate a three-section format: Data Sources table
(from `raw_file` fields and non-derived `data/` layers), Processing Steps
numbered list (from action function docstrings in topological order), and
Data Flow mermaid diagram. Populated the metadata on the seven raw-data layer
files.

**Files changed:**
- `alidade/models.py` — added `source_description`, `source_origin`
- `alidade/readme.py` — rewrote `_auto_section`; added `_data_source_rows`,
  `_step_description`, `_topo_sort`
- `layers/park_boundary.py`, `layers/water.py`, `layers/roads_trails.py`,
  `layers/vegetation.py`, `layers/elevation.py`, `layers/developed_area.py`,
  `layers/staging.py` — added `source_description` and `source_origin`

---

## Step 18 — Color system refactor

Replaced scattered color format strings (QGIS `"R,G,B,A"` strings, hex
literals, matplotlib float tuples) with a single canonical `Color` type.

- `alidade/color.py` — new `Color` frozen dataclass with `from_hex()`,
  `from_qgis()`, `with_alpha()`, `.qgis`, `.mpl`, `.hex`; `brewer()` helper
  via palettable; named constants `BLACK`, `DARK_GRAY`, `WHITE`, `TRANSPARENT`,
  `LABEL_GRAY`.
- `palette.py` — new file; all project colors as named semantic constants
  (role-based names, never color-descriptive): `PARK_FILL`, `PARK_BORDER`,
  `WATER_FILL`, `ROADS_LINE`, `VEG_*`, `SLOPE_*`, `SUITABILITY` (4-class
  Purples brewer), `STAGING_FILL`, `PRIORITY_*`, `STAGING_RANK_TIERS`,
  `TARGET_RANK_TIERS`.
- All `layers/*.py` — inline QGIS strings replaced with named palette
  constants; `from_qgis()` and `.with_alpha()` used at layer boundaries.
- `alidade/colors.py` deleted; `colour` dependency replaced by `palettable`.

**Files changed:**
- `alidade/color.py` (new), `palette.py` (new), `alidade/colors.py` (deleted)
- `alidade/models.py`, `alidade/render_map.py`, `alidade/render_qgis.py`,
  `alidade/dump_qgis.py`, `alidade/publish_arcgis.py`
- `alidade/lyrx/build.py`, `alidade/lyrx/symbols.py`
- `util.py` — `VegetationZone.color: str` → `Color`; `VEGETATION_ZONES` uses
  palette constants
- All 17 `layers/*.py` files
