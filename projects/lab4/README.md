# Lab 4

<!-- auto:begin -->
## Layers

### Shopping Malls

**Source:** `output/malls.shp`  
**Style:** single symbol — circle marker #dc3232, 4.0 MM  
**Derived from:**   
**Processing:** Geocode malls.csv addresses with Nominatim; reproject to EPSG:2227.

### Males 22-39 > 20% of Population

**Source:** `output/males_22_39_pct_over20.shp`  
**Style:** rule-based (5 rules)  
**Derived from:** `census_tracts_males_22_39`  
**Processing:** Calculate pct_m22_39 = M22_39 / Total * 100; keep tracts where pct_m22_39 > 20.

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
census_tracts_males_22_39  ──►  males_22_39_pct_over20
roads  ──►  major_roads
```

## Processing tools

| Layer | Tool | Description |
| --- | --- | --- |
| `malls` | `geopandas` | Geocode malls.csv addresses with Nominatim; reproject to EPSG:2227. |
| `males_22_39_pct_over20` | `geopandas` | Calculate pct_m22_39 = M22_39 / Total * 100; keep tracts where pct_m22_39 > 20. |
| `major_roads` | `geopandas` | Filter roads to primary/major highway FCC codes A10–A21. |
<!-- auto:end -->
