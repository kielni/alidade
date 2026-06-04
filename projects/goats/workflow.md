# Goats — workflow

## Layers

| Layer | File | Style | Processing |
|---|---|---|---|
| Staging Areas | `output/staging.shp` | Target icon (`data/goat.svg`), 6 mm, bright yellow (#ffdc00) | Reproject `data/staging.geojson` → EPSG:26910 |
| Park Boundary | `data/park_boundary.geojson` | Hollow polygon, 1.5 mm thick purple (#800080) outline, no fill | — |
| Clip Border | `output/border.gpkg` | Invisible (processing output only) | Buffer park boundary by 100 ft (30.48 m); dissolve → single polygon; used as clip mask for water, roads/trails, vegetation |
| Developed Area | `output/developed_area.shp` | Light gray fill (50% transparent) + medium gray outline, 1.0 mm | Merge GPX `tracks` → simplify 10 m (Douglas-Peucker) → close ring → Polygon → EPSG:26910 |
| Streams | `output/water.shp` | Blue (#446677) lines, 0.6 mm | Reproject + clip `data/water.geojson` to clip border → EPSG:26910 |
| Roads & Trails | `output/roads_trails.shp` | Brown (#785028) lines, 0.5 mm | Reproject + clip `data/roads_trails.geojson` to clip border → EPSG:26910; polygons excluded |
| Slope | `output/slope.tif` | Paletted: Flat to gentle #1a9641 · Moderate #ffffbf · Steep #fdae61 · Too steep #d7191c | `gdaldem slope -p` on elevation → `gdal_calc.py` reclassify to Byte (1–4); breaks at 15/27/58% |
| Elevation | `output/elevation.tif` | Grayscale (black → white) | Reproject DEM `data/USGS_13_n38w122_20250826.tif` EPSG:4269 → EPSG:26910, crop to clip border, bilinear resampling |
| Fine-Scale Vegetation | `output/vegetation.gpkg` | Rule-based: 7 VMP suitability zones (alpha=200) — Shrub #1a9850 · Herbaceous #a6d96a · Non-native herbaceous #fee08b · Non-native woodland #bf812d · Native woodland #dfc27d · Riparian forest #8c510a · Developed #d9d9d9 | Reproject `data/fine_scale_vegetation.gdb` (EPSG:6420) → EPSG:26910, clip to clip border; 343 polygons, 23 MAP_CLASS values |
| CartoDB Positron | XYZ tile basemap | `styles/cartodb_positron.xml` | — |

## Project

- CRS: EPSG:26910 (NAD83 / UTM Zone 10N)
- Extent (padded 5%): `(603628.0, 4138828.9, 607872.9, 4140758.2)`
- Layer order (top → bottom): `staging`, `park_boundary`, `developed_area`, `water`, `roads_trails`, `slope`, `vegetation`, `basemap`

## Data sources

- `park_boundary.geojson` — OpenStreetMap via Overpass Turbo
- `water.geojson` — OSM waterway streams via Overpass Turbo (36 LineString features)
- `roads_trails.geojson` — OSM highway ways via Overpass Turbo (1537 LineStrings + 1 MultiLineString; 1 Polygon excluded during processing)
- `fine_scale_vegetation.gdb` — Santa Cruz/Santa Clara County 121-class NVC vegetation map (2020), EPSG:6420, 309,785 polygons county-wide; 343 polygons within park boundary
