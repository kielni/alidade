# Lab 4

<!-- auto:begin -->
## Layers

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

### OpenStreetMap

**Source:** `OpenStreetMap tile service`  
**Style:** no style configured  

## Data flow

```
census_tracts_males_22_39  ──►  males_22_39_pct_over20
roads  ──►  major_roads
```

## Processing tools

| Layer | Tool | Description |
| --- | --- | --- |
| `males_22_39_pct_over20` | `geopandas` | Calculate pct_m22_39 = M22_39 / Total * 100; keep tracts where pct_m22_39 > 20. |
| `major_roads` | `geopandas` | Filter roads to primary/major highway FCC codes A10–A21. |
<!-- auto:end -->
