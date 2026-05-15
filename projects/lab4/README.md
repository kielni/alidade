# Lab 4

<!-- auto:begin -->
## Layers

### Males 22-39 > 20% of Population

**Source:** `output/males_22_39_pct_over20.shp`  
**Style:** rule-based (5 rules)  
**Derived from:** `census_tracts_males_22_39`  
**Processing:** Calculate pct_m22_39 = M22_39 / Total * 100; keep tracts where pct_m22_39 > 20.

### Males Ages 22-39 (Census Tracts)

**Source:** `data/M22_39yrs.shp`  
**Style:** single symbol — fill #c87832 at 71% opacity, #783c00 outline  

### Roads

**Source:** `data/roads.shp`  
**Style:** single symbol — solid line #505050, 0.5 MM  

### OpenStreetMap

**Source:** `OpenStreetMap tile service`  
**Style:** no style configured  

## Data flow

```
census_tracts_males_22_39  ──►  males_22_39_pct_over20
```

## Processing tools

| Layer | Tool | Description |
| --- | --- | --- |
| `males_22_39_pct_over20` | `geopandas` | Calculate pct_m22_39 = M22_39 / Total * 100; keep tracts where pct_m22_39 > 20. |
<!-- auto:end -->
