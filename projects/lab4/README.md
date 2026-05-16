# Lab 4

<!-- auto:begin -->
## Layers

### Shopping Malls

**Source:** `output/malls.shp`  
**Style:** single symbol — SVG marker mall.svg, 5.0 MM  
**Processing:** Geocode mall_names.csv addresses with Nominatim; reproject to EPSG:2227. Fields: id, Street, mall_name, city.

### Target Tracts

**Source:** `output/target_tracts.shp`  
**Style:** rule-based (5 rules)  
**Derived from:** `census_tracts`  
**Processing:** Calculate pct_m22_39 = M22_39 / Total * 100; keep tracts where pct_m22_39 > 20.

### Basemap

**Source:** `CartoDB Positron XYZ tile service`  
**Style:** see `styles/cartodb_dark_matter.xml`  

## Data flow

```mermaid
flowchart LR
    census_tracts --> target_tracts
```

## Processing tools

| Layer | Tool | Description |
| --- | --- | --- |
| `mall_points` | `geopandas` | Geocode mall_names.csv addresses with Nominatim; reproject to EPSG:2227. Fields: id, Street, mall_name, city. |
| `target_tracts` | `geopandas` | Calculate pct_m22_39 = M22_39 / Total * 100; keep tracts where pct_m22_39 > 20. |
<!-- auto:end -->
