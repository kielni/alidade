# Goats — workflow

## Layers

| Layer | File | Style |
|---|---|---|
| Park Boundary | `data/park_boundary.geojson` | Hollow polygon, 1.5 mm thick purple (#800080) outline, no fill |
| CartoDB Positron | XYZ tile basemap | `styles/cartodb_positron.xml` |

## Project

- CRS: EPSG:26910 (NAD83 / UTM Zone 10N)
- Extent (padded 5%): `(603628.0, 4138828.9, 607872.9, 4140758.2)`
- Layer order (top → bottom): `park_boundary`, `basemap`
