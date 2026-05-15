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

### Mall Buffer Census Tracts

**Source:** `output/mall_buffer_tracts.shp`  
**Style:** single symbol — fill #ffc832 at 71% opacity, #b47800 outline  
**Derived from:** `mall_buffers`, `census_tracts_males_22_39`  
**Processing:** Spatial inner join (intersects) of mall 5-mile buffers with census tracts where pct_m22_39 > 20%; retains Total and M22_39.

### Major Roads

**Source:** `output/major_roads.shp`  
**Style:** single symbol — solid line #1e1e1e, 1.0 MM  
**Derived from:** `roads`  
**Processing:** Filter roads to primary/major highway FCC codes A10–A21.

### Males Ages 22-39 (Census Tracts)

**Source:** `data/M22_39yrs.shp`  
**Style:** single symbol — fill #c87832 at 71% opacity, #783c00 outline  

### Roads

**Source:** `data/roads.shp`  
**Style:** single symbol — solid line #505050, 0.5 MM  

### CartoDB Positron

**Source:** `CartoDB Positron XYZ tile service`  
**Style:** see `styles/cartodb_positron.xml`  

## Data flow

```
malls  ──►  mall_buffers
mall_buffers  ──►  mall_buffer_tracts
census_tracts_males_22_39  ──►  mall_buffer_tracts
roads  ──►  major_roads
```

## Processing tools

| Layer | Tool | Description |
| --- | --- | --- |
| `malls` | `geopandas` | Geocode malls.csv addresses with Nominatim; reproject to EPSG:2227. |
| `mall_buffers` | `geopandas` | Buffer mall points by 5 miles (26,400 ft) in EPSG:2227; join mall_names.csv on id to add mall_name field. |
| `mall_buffer_tracts` | `geopandas` | Spatial inner join (intersects) of mall 5-mile buffers with census tracts where pct_m22_39 > 20%; retains Total and M22_39. |
| `major_roads` | `geopandas` | Filter roads to primary/major highway FCC codes A10–A21. |
<!-- auto:end -->
