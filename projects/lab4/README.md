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

### Major Roads

**Source:** `output/major_roads.shp`  
**Style:** single symbol — solid line #1e1e1e, 1.0 MM  
**Derived from:** `roads`  
**Processing:** Filter roads to primary/major highway FCC codes A10–A21.

### Census Tracts

**Source:** `output/census_tracts.shp`  
**Style:** GraduatedRenderer  
**Derived from:** `census_tracts_raw`  
**Processing:** Filter census tracts to those with Total > 0.

### Census Tracts (raw)

**Source:** `data/M22_39yrs.shp`  
**Style:** no style configured  

### Target Tracts

**Source:** `output/target_tracts.shp`  
**Style:** rule-based (5 rules)  
**Derived from:** `census_tracts`  
**Processing:** Calculate pct_m22_39 = M22_39 / Total * 100; keep tracts where pct_m22_39 > 20.

### Roads

**Source:** `data/roads.shp`  
**Style:** single symbol — solid line #505050, 0.5 MM  

### CartoDB Positron

**Source:** `CartoDB Positron XYZ tile service`  
**Style:** see `styles/cartodb_positron.xml`  

## Data flow

```
malls  ──►  mall_buffers
mall_buffers  ──►  mall_target_intersect
census_tracts  ──►  mall_target_intersect
roads  ──►  major_roads
census_tracts_raw  ──►  census_tracts
census_tracts  ──►  target_tracts
```

## Processing tools

| Layer | Tool | Description |
| --- | --- | --- |
| `malls` | `geopandas` | Geocode malls.csv addresses with Nominatim; reproject to EPSG:2227. |
| `mall_buffers` | `geopandas` | Buffer mall points by 5 miles (26,400 ft) in EPSG:2227; join mall_names.csv on id to add mall_name field. |
| `mall_target_intersect` | `geopandas` | Spatial inner join (intersects) of mall 5-mile buffers with census tracts where pct_m22_39 > 20%; retains Total and M22_39. |
| `major_roads` | `geopandas` | Filter roads to primary/major highway FCC codes A10–A21. |
| `census_tracts` | `geopandas` | Filter census tracts to those with Total > 0. |
| `target_tracts` | `geopandas` | Calculate pct_m22_39 = M22_39 / Total * 100; keep tracts where pct_m22_39 > 20. |
<!-- auto:end -->
