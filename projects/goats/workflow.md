# Goats — workflow

## Layer model conventions (post-refactor)

Layer files now use the flat `Layer` model directly — no `ProcessingStep` wrapper.
Processing functions have a PEP-257 docstring describing what they do. They take a `BoundLayer` and use:
- `(dep,) = layer.inputs` — unpack single input; raises if count ≠ 1
- `dep.path` — absolute path to a dependency layer's output
- `layer.raw_path` — absolute path to the layer's `raw_file` (raw source data)
- `layer.path` — absolute path to this layer's output (derived from `datasource`)

Layer parameter order: `id`, `name`, `type`, then `inputs=[…]` and `raw_file=` (if present) immediately before `datasource=`. `datasource` paths have no `./` prefix.
The `action=` field replaces `processing_step=ProcessingStep(…)`.

## Layers

| Layer | File | Style | Processing |
|---|---|---|---|
| Staging Areas | `output/staging.shp` | Circle marker, 3 mm, dark red (160,30,30) + dark outline | Reproject `data/staging.geojson` → EPSG:26910 |
| Park Boundary | `data/park_boundary.geojson` | Hollow polygon, 1.5 mm thick purple (#800080) outline, no fill | — |
| Clip Border | `output/border.gpkg` | Invisible (processing output only) | Buffer park boundary by 100 ft (30.48 m); dissolve → single polygon; used as clip mask for water, roads/trails, vegetation |
| Developed Area | `output/developed_area.shp` | Light gray fill (50% transparent) + medium gray outline, 1.0 mm | Merge GPX `tracks` → simplify 10 m (Douglas-Peucker) → close ring → Polygon → EPSG:26910 |
| Streams | `output/water.shp` | Blue (#446677) lines, 0.6 mm | Reproject + clip `data/water.geojson` to clip border → EPSG:26910; keep only `@id` and `name` columns |
| Roads & Trails | `output/roads_trails.shp` | Brown (#785028) lines, 0.5 mm | Reproject + clip `data/roads_trails.geojson` to clip border → EPSG:26910; polygons excluded |
| Slope | `output/slope.tif` | Paletted: Flat to gentle #1a9641 · Moderate #ffffbf · Steep #fdae61 · Too steep #d7191c | `gdaldem slope -p` on elevation → `gdal_calc.py` reclassify to Byte (1–4); breaks at 15/27/58% |
| Elevation | `output/elevation.tif` | Grayscale (black → white) | Reproject DEM `data/USGS_13_n38w122_20250826.tif` EPSG:4269 → EPSG:26910, crop to clip border, bilinear resampling |
| Fine-Scale Vegetation | `output/vegetation.gpkg` | Rule-based: 7 VMP suitability zones (alpha=200) — Shrub #1a9850 · Herbaceous #a6d96a · Non-native herbaceous #fee08b · Non-native woodland #bf812d · Native woodland #dfc27d · Riparian forest #8c510a · Developed #d9d9d9 | Reproject `data/fine_scale_vegetation.gdb` (EPSG:6420) → EPSG:26910, clip to clip border; 343 polygons, 23 MAP_CLASS values |
| CartoDB Positron | XYZ tile basemap | `styles/cartodb_positron.xml` | — |
| Priority: Developed Area Buffer | `output/priority_developed.gpkg` | Orange fill (255,140,0 @ 50%) + dark orange outline, 0.5 mm | Buffer `output/developed_area.shp` by 100 ft (30.48 m), union, clip to park boundary |
| Priority: Roads & Trails Buffer | `output/priority_roads_trails.gpkg` | Yellow fill (255,200,0 @ 50%) + dark yellow outline, 0.5 mm | Buffer `output/roads_trails.shp` by 30 ft (9.144 m), union, clip to park boundary |
| Exclusion: Riparian Buffer | `output/exclude_water_vegetation.gpkg` | Blue fill (68,119,170 @ 50%) + dark blue outline, 0.5 mm | Buffer `output/water.shp` by 30 ft (9.144 m), union, clip to park boundary |

| Staging Area Scores | `output/staging_scored.gpkg` | Rule-based circle marker: 3 mm, RdYlBu diverging — red 215,25,28 (rank 1 best) / orange 253,174,97 (rank 2) / blue 44,123,182 (rank 3+) | rasterstats.zonal_stats within 0.5-mile buffer; score = suit_mean / max(suit_mean); rank 1 = best; mean avoids penalising staging areas near riparian exclusion zones |
| Suitability | `output/suitability.tif` | Paletted: Purples 4-class (#f2f0f7·#cbc9e2·#9e9ac8·#6a51a3); 0=excluded transparent | Weighted overlay: rasterize veg+priority layers to slope.tif grid; weights slope 25% + veg 25% + priority_developed 25% + priority_trails 25%; zero-mask exclusions (too-steep, riparian buffer, excluded veg); Jenks 4-class on non-zero pixels; clip to exact park boundary via geometry_mask |
| Grazeable Patches | `output/patches.gpkg` | Rule-based polygon fill: Purples 4-class (#f2f0f7·#cbc9e2·#9e9ac8·#6a51a3, alpha=200), darker = higher patch_score; 0.1 mm gray outline | Vectorize non-zero suitability pixels (contiguous regions) → filter < 500 m² → convex hull → union overlapping hulls + re-explode → bisect patches > 120,000 m² → subtract riparian exclusion zones (re-explode; drop fragments < 500 m²) → clip to park boundary; fields: patch_id (sequential int), size_acres, perimeter, suitability_sum, patch_score, patch_class 1–4 (Jenks); prints High + Very high patches by size descending. Hull precedes exclusion: hull of a notched polygon re-fills the notch. |
| Staging Area Ranking | `output/staging_ranked.gpkg` | Rule-based circle marker: 3 mm, YlGn 3-class — #31a354 dark green (rank 1 best) / #addd8e mid green (rank 2) / #f7fcb9 pale yellow (rank 3+) | Distance-decay scoring: score = Σ(patch_score / distance) over all patches; distance clamped ≥ 1 m to avoid divide-by-zero; rank 1 = highest score |

## Project

- CRS: EPSG:26910 (NAD83 / UTM Zone 10N)
- Extent (padded 5%): `(603628.0, 4138828.9, 607872.9, 4140758.2)`
- Layer order (top → bottom): `staging`, `park_boundary`, `developed_area`, `water`, `roads_trails`, `slope`, `vegetation`, `basemap`

## Data sources

- `park_boundary.geojson` — OpenStreetMap via Overpass Turbo
- `water.geojson` — OSM waterway streams via Overpass Turbo (36 LineString features)
- `roads_trails.geojson` — OSM highway ways via Overpass Turbo (1537 LineStrings + 1 MultiLineString; 1 Polygon excluded during processing)
- `fine_scale_vegetation.gdb` — Santa Cruz/Santa Clara County 121-class NVC vegetation map (2020), EPSG:6420, 309,785 polygons county-wide; 343 polygons within park boundary
