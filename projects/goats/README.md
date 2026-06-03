# Goats

<!-- auto:begin -->
## Layers

### Park Boundary

**Source:** `data/park_boundary.geojson`  
**Style:** single symbol — fill #000000 at 0% opacity, #800080 outline  

### Clip Border (100 ft buffer)

**Source:** `output/border.gpkg`  
**Style:** single symbol — fill #000000 at 0% opacity, #6464c8 outline  
**Derived from:** `park_boundary`  
**Processing:** Buffer park boundary by 100 ft (30.48 m) to create clip border

### Developed Area

**Source:** `output/developed_area.shp`  
**Style:** single symbol — fill #c8c8c8 at 50% opacity, #808080 outline  
**Processing:** Simplify GPX track (10 m tolerance), close ring, convert to polygon, reproject to EPSG:26910

### Riparian Areas

**Source:** `output/water.shp`  
**Style:** single symbol — solid line #4477aa, 0.6 MM  
**Derived from:** `clip_border`  
**Processing:** Reproject and clip streams to park boundary

### Roads & Trails

**Source:** `output/roads_trails.shp`  
**Style:** single symbol — solid line #785028, 0.5 MM  
**Derived from:** `clip_border`  
**Processing:** Reproject and clip roads and trails to park boundary

### Fine-Scale Vegetation (2020)

**Source:** `output/vegetation.gpkg`  
**Style:** rule-based (6 rules)  
**Derived from:** `clip_border`  
**Processing:** Reproject and clip Santa Cruz/Santa Clara fine-scale vegetation to park boundary

### CartoDB Positron

**Source:** `CartoDB Positron XYZ tile service`  
**Style:** see `styles/cartodb_positron.xml`  

## Data flow

```mermaid
flowchart LR
    park_boundary --> clip_border
    clip_border --> riparian_zone
    clip_border --> roads_trails
    clip_border --> vegetation_15f989a8
```

## Processing tools

| Layer | Tool | Description |
| --- | --- | --- |
| `clip_border` | `geopandas` | Buffer park boundary by 100 ft (30.48 m) to create clip border |
| `developed_area` | `geopandas` | Simplify GPX track (10 m tolerance), close ring, convert to polygon, reproject to EPSG:26910 |
| `riparian_zone` | `geopandas` | Reproject and clip streams to park boundary |
| `roads_trails` | `geopandas` | Reproject and clip roads and trails to park boundary |
| `vegetation_15f989a8` | `geopandas` | Reproject and clip Santa Cruz/Santa Clara fine-scale vegetation to park boundary |
<!-- auto:end -->
