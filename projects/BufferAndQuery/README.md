# BufferAndQuery

Practice project: buffer state capitol buildings and query which national parks
fall within a given distance. Data covers the continental US.

<!-- auto:begin -->
## Layers

### State Capitol Buildings

**Source:** `data/state_Capitol_bldgs.shp`  
**Style:** see `styles/state_capitol_bldgs.xml`  

### Capitol Buffers Intersecting National Parks

**Source:** `output/capitol_parks_intersect.shp`  
**Style:** single symbol — fill #ffa032 at 43% opacity, #c85a00 outline  
**Derived from:** `capitol_buffer`, `national_parks`  
**Processing:** Filter 25-mile capitol buffers to those intersecting at least one national park polygon; print count to stdout.

### State Capitol 25-Mile Buffer

**Source:** `output/capitol_buffer.shp`  
**Style:** single symbol — fill #6496ff at 31% opacity, #0050c8 outline  
**Derived from:** `state_capitol_bldgs`  
**Processing:** Buffer each State Capitol building point by 25 miles (40,233.6 m in EPSG:3857) using geopandas.

### National Parks

**Source:** `output/national_parks.shp`  
**Style:** single symbol — fill #78c864 at 50% opacity, #006400 outline  
**Derived from:** `usaparks`  
**Processing:** Filter USAParks to FCC='D83' (National Park Service units: national parks, monuments, historic parks, seashores, etc.).

### CartoDB Positron

**Source:** `CartoDB Positron XYZ tile service`  
**Style:** see `styles/cartodb_positron.xml`  

## Data flow

```
capitol_buffer  ──►  capitol_parks_intersect
national_parks  ──►  capitol_parks_intersect
state_capitol_bldgs  ──►  capitol_buffer
usaparks  ──►  national_parks
```

## Processing tools

| Layer | Tool | Description |
| --- | --- | --- |
| `capitol_parks_intersect` | `geopandas` | Filter 25-mile capitol buffers to those intersecting at least one national park polygon; print count to stdout. |
| `capitol_buffer` | `geopandas` | Buffer each State Capitol building point by 25 miles (40,233.6 m in EPSG:3857) using geopandas. |
| `national_parks` | `geopandas` | Filter USAParks to FCC='D83' (National Park Service units: national parks, monuments, historic parks, seashores, etc.). |
<!-- auto:end -->

## Workflow log

See `workflow.md` for the prompt-by-prompt build history and decisions made at
each step.
