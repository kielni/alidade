# Lab 4

<!-- auto:begin -->
## Layers

### Shopping Malls

**Source:** `output/malls.shp`  
**Style:** single symbol — circle marker #dc3232, 4.0 MM  
**Derived from:**   
**Processing:** Geocode malls.csv addresses with Nominatim; reproject to EPSG:2227.

### Mall 5-Mile Buffers

**Source:** `output/mall_buffers.shp`  
**Style:** single symbol — fill #90ee90 at 50% opacity, #50a050 outline  
**Derived from:** `malls`  
**Processing:** Buffer mall points by 5 miles (26,400 ft) in EPSG:2227; join mall_names.csv on id to add mall_name field.

### Mall Target Intersect

**Source:** `output/mall_target_intersect.shp`  
**Style:** single symbol — fill #ffc832 at 71% opacity, #b47800 outline  
**Derived from:** `mall_buffers`, `census_tracts`  
**Processing:** Spatial inner join (intersects) of mall 5-mile buffers with census tracts where pct_m22_39 > 20%; retains Total and M22_39.

### CartoDB Positron

**Source:** `CartoDB Positron XYZ tile service`  
**Style:** see `styles/cartodb_positron.xml`  

## Data flow

```
malls  ──►  mall_buffers
mall_buffers  ──►  mall_target_intersect
census_tracts  ──►  mall_target_intersect
```

## Processing tools

| Layer | Tool | Description |
| --- | --- | --- |
| `malls` | `geopandas` | Geocode malls.csv addresses with Nominatim; reproject to EPSG:2227. |
| `mall_buffers` | `geopandas` | Buffer mall points by 5 miles (26,400 ft) in EPSG:2227; join mall_names.csv on id to add mall_name field. |
| `mall_target_intersect` | `geopandas` | Spatial inner join (intersects) of mall 5-mile buffers with census tracts where pct_m22_39 > 20%; retains Total and M22_39. |
<!-- auto:end -->
