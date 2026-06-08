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
| Staging Areas | `output/staging.shp` | Diamond marker, 4 mm, bright purple (180,0,255) + dark purple outline (110,0,160), 0.4 mm | Reproject `data/staging.geojson` → EPSG:26910 |
| Park Boundary | `data/park_boundary.geojson` | Hollow polygon, 1.5 mm thick purple (#800080) outline, no fill | — |
| Park Fill | `data/park_boundary.geojson` (same source) | Solid white fill, no outline; placed above basemap in map_patches and map_targets_cluster to make non-patch areas white | — |
| Clip Border | `output/border.gpkg` | Invisible (processing output only) | Buffer park boundary by 100 ft (30.48 m); dissolve → single polygon; used as clip mask for water, roads/trails, vegetation |
| Developed Area | `output/developed_area.shp` | Light gray fill (50% transparent) + medium gray outline, 1.0 mm | Merge GPX `tracks` → simplify 10 m (Douglas-Peucker) → close ring → Polygon → EPSG:26910 |
| Streams | `output/water.shp` | Blue (#446677) lines, 0.6 mm | Reproject + clip `data/water.geojson` to clip border → EPSG:26910; keep only `@id` and `name` columns |
| Roads & Trails | `output/roads_trails.shp` | Brown (#785028) lines, 0.5 mm | Reproject + clip `data/roads_trails.geojson` to clip border → EPSG:26910; polygons excluded |
| Slope | `output/slope.tif` | Paletted: Flat to gentle #1a9641 · Moderate #ffffbf · Steep #fdae61 · Too steep #ddd0c0 (warm light gray, readable against light basemap) | `gdaldem slope -p` on elevation → `gdal_calc.py` reclassify to Byte (1–4); breaks at 15/27/58% |
| Elevation | `output/elevation.tif` | Grayscale (black → white) | Reproject DEM `data/USGS_13_n38w122_20250826.tif` EPSG:4269 → EPSG:26910, crop to clip border, bilinear resampling |
| Fine-Scale Vegetation | `output/vegetation.gpkg` | Rule-based: 7 VMP suitability zones (alpha=200) — Shrub #1a9850 · Herbaceous #a6d96a · Non-native herbaceous #fee08b · Non-native woodland #bf812d · Native woodland #dfc27d · Riparian forest #8c510a · Developed #d9d9d9 | Reproject `data/fine_scale_vegetation.gdb` (EPSG:6420) → EPSG:26910, clip to clip border, dissolve by `ENHANCED_LIFEFORM` (merges adjacent same-category polygons); retains only `ENHANCED_LIFEFORM` + geometry |
| Fine-Scale Vegetation Highlight | `output/vegetation.gpkg` (same source) | Rule-based outline+thin fill, 3 zones only: Shrub #1a9850 · Non-native herbaceous #a6d96a · Herbaceous #fee08b (alpha=32 fill, alpha=255 outline, 1.0 mm) | No processing — shares output with Fine-Scale Vegetation |
| CartoDB Positron | XYZ tile basemap | `styles/cartodb_positron.xml` | — |
| ESRI World Imagery (satellite) | XYZ tile basemap | `styles/esri_satellite.xml` | — |
| Priority: Developed Area Buffer | `output/priority_developed.gpkg` | Orange fill (255,140,0 @ 50%) + dark orange outline, 0.5 mm | Buffer `output/developed_area.shp` by 100 ft (30.48 m), union, clip to park boundary |
| Priority: Roads & Trails Buffer | `output/priority_roads_trails.gpkg` | Yellow fill (255,200,0 @ 50%) + dark yellow outline, 0.5 mm | Buffer `output/roads_trails.shp` by 30 ft (9.144 m), union, clip to park boundary |
| Exclusion: Riparian Buffer | `output/exclude_water_vegetation.gpkg` | Blue fill (68,119,170 @ 50%) + dark blue outline, 0.5 mm | Buffer `output/water.shp` by 30 ft (9.144 m), union, clip to park boundary |

| Staging Area Scores | `output/staging_scored.gpkg` | Rule-based circle marker: 3 mm, RdYlBu diverging — red 215,25,28 (rank 1 best) / orange 253,174,97 (rank 2) / blue 44,123,182 (rank 3+) | rasterstats.zonal_stats within 0.5-mile buffer; score = suit_mean / max(suit_mean); rank 1 = best; mean avoids penalising staging areas near riparian exclusion zones |
| Suitability | `output/suitability.tif` | Paletted: Purples 4-class (#f2f0f7·#cbc9e2·#9e9ac8·#6a51a3); 0=excluded transparent | Weighted overlay: rasterize veg+priority layers to slope.tif grid; weights slope 25% + veg 25% + priority_developed 25% + priority_trails 25%; zero-mask exclusions (too-steep, riparian buffer, excluded veg); Jenks 4-class on non-zero pixels; clip to exact park boundary via geometry_mask |
| Grazeable Patches | `output/patches.gpkg` | Rule-based polygon fill: Purples 4-class (#f2f0f7·#cbc9e2·#9e9ac8·#6a51a3, alpha=200), darker = higher patch_score; 0.2 mm gray outline; patch_class=0 unstyled (transparent) | Vectorize non-zero suitability pixels (contiguous regions) → filter < 500 m² → morphological closing (buffer +10 m / −10 m; merges adjacent pixels, rounds staircase edges without filling terrain notches) → union overlapping patches + re-explode → Voronoi-split patches > 120,000 m² using k-means cluster centers as seeds (split lines run through low-suitability terrain gaps) → subtract riparian exclusion zones (re-explode; drop fragments < 500 m²) → clip to park boundary; fields: patch_id (sequential int), size_acres, perimeter, suitability_sum, patch_score (suitability_sum / perimeter), patch_class 1–4 (Jenks on patch_score); prints High + Very high patches by size descending. |
| Terrain Basins | `output/basins.gpkg` | Rule-based polygon fill: Purples 4-class (#f2f0f7·#cbc9e2·#9e9ac8·#6a51a3, alpha=200), darker = higher suitability_sum; 0.4 mm gray outline | DEM → pysheds (fill pits/depressions, resolve flats, D8 flowdir + accumulation) → stream reaches labeled via scipy connected components (acc > _STREAM_THRESHOLD=200 cells ≈ 5 acres) → non-stream cells labeled by D8 propagation in decreasing-accumulation order → boundary-draining cells labeled by connected components → vectorize → dissolve per basin ID → clip to park → subtract riparian exclusion buffer (splits cross-valley basins at creek corridor) → explode → drop < 1 acre; fields: basin_id (sequential int), size_acres, suitability_sum, basin_class 1–4 (Jenks on suitability_sum); prints High + Very high basins by suitability_sum descending. Boundaries follow terrain ridgelines and drainage divides; no convex hulls or rectangular bisection. |
| Staging Area Ranking | `output/staging_ranked.gpkg` | Rule-based diamond marker: 4 mm, saturated YlGn 3-class — (0,200,60) vivid green (rank 1 best) / (120,230,90) bright green (rank 2) / (225,255,80) bright lime (rank 3+) | Distance-decay scoring: score = Σ(patch_score / distance) over High and Very high patches only (patch_class >= 3); class 1–2 fragments excluded so marginal terrain does not inflate scores for staging areas that lack access to genuinely high-priority grazing zones; distance clamped ≥ 50 m so patches closer than that contribute equally; rank 1 = highest score; prints rank, name, score_norm, raw score (4 dp) for each staging area |

## Project

- CRS: EPSG:26910 (NAD83 / UTM Zone 10N)
- Extent (padded 5%): `(603628.0, 4138828.9, 607872.9, 4140758.2)`
- Layer order (top → bottom): `staging`, `park_boundary`, `developed_area`, `water`, `roads_trails`, `slope`, `vegetation`, `basemap`
- `map_detail` uses `basemap_satellite` (ESRI World Imagery) instead of `basemap`

## Data sources

- `park_boundary.geojson` — OpenStreetMap via Overpass Turbo
- `water.geojson` — OSM waterway streams via Overpass Turbo (36 LineString features)
- `roads_trails.geojson` — OSM highway ways via Overpass Turbo (1537 LineStrings + 1 MultiLineString; 1 Polygon excluded during processing)
- `fine_scale_vegetation.gdb` — Santa Cruz/Santa Clara County 121-class NVC vegetation map (2020), EPSG:6420, 309,785 polygons county-wide; 343 polygons within park boundary
