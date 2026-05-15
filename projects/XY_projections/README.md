# 

<!-- auto:begin -->
## Layers

### High Schools Buffer

**Source:** `data/high_schools_buffer.shp`  
**Style:** single symbol — fill #4080ff, #232323 outline  
**Derived from:** `high_schools_2227`  
**Processing:** 1-mile buffer around each high school point (EPSG:2227 ft)

### High Schools 2227

**Source:** `data/high_schools_2227.shp`  
**Style:** no style configured  
**Derived from:** `high_schools`  
**Processing:** Reproject high schools CSV from EPSG:4326 to EPSG:2227

### High Schools

**Source:** `data/high_schools.csv?type=csv&xField=Longitude&yField=Latitude&crs=EPSG:4326`  
**Style:** no style configured  

### Libraries

**Source:** `Libraries.shp`  
**Style:** see `styles/libraries.xml`  

### PaloAlto_cityboundary

**Source:** `PaloAlto_cityboundary.shp`  
**Style:** see `styles/paloalto_cityboundary.xml`  

### Carto test 3

**Source:** `CartoDB Positron XYZ tile service`  
**Style:** see `styles/carto_test_3.xml`  

### OSM gray scale

**Source:** `%7By%7D.png&zmax=18&zmin=0`  
**Style:** see `styles/osm_gray_scale.xml`  

## Data flow

```
high_schools_2227  ──►  high_schools_buffer
high_schools  ──►  high_schools_2227
```

## Processing tools

| Layer | Tool | Description |
| --- | --- | --- |
| `high_schools_buffer` | `geopandas` | 1-mile buffer around each high school point (EPSG:2227 ft) |
| `high_schools_2227` | `geopandas` | Reproject high schools CSV from EPSG:4326 to EPSG:2227 |
<!-- auto:end -->
