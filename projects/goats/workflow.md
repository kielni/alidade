# Goats — workflow

## Layers

| Layer | File | Style | Processing |
|---|---|---|---|
| Staging Areas | `output/staging.shp` | Target icon (`data/goat.svg`), 6 mm, bright yellow (#ffdc00) | Reproject `data/staging.geojson` → EPSG:26910 |
| Park Boundary | `data/park_boundary.geojson` | Hollow polygon, 1.5 mm thick purple (#800080) outline, no fill | — |
| Developed Area | `output/developed_area.shp` | Light gray fill (50% transparent) + medium gray outline, 1.0 mm | Merge GPX `tracks` → simplify 10 m (Douglas-Peucker) → close ring → Polygon → EPSG:26910 |
| Streams | `output/water.shp` | Blue (#446677) lines, 0.6 mm | Reproject + clip `data/water.geojson` to park boundary → EPSG:26910 |
| Roads & Trails | `output/roads_trails.shp` | Brown (#785028) lines, 0.5 mm | Reproject + clip `data/roads_trails.geojson` to park boundary → EPSG:26910; polygons excluded |
| CartoDB Positron | XYZ tile basemap | `styles/cartodb_positron.xml` | — |

## Project

- CRS: EPSG:26910 (NAD83 / UTM Zone 10N)
- Extent (padded 5%): `(603628.0, 4138828.9, 607872.9, 4140758.2)`
- Layer order (top → bottom): `park_boundary`, `developed_area`, `water`, `roads_trails`, `basemap`

## Data sources

- `park_boundary.geojson` — OpenStreetMap via Overpass Turbo
- `water.geojson` — OSM waterway streams via Overpass Turbo (36 LineString features)
- `roads_trails.geojson` — OSM highway ways via Overpass Turbo (1537 LineStrings + 1 MultiLineString; 1 Polygon excluded during processing)
