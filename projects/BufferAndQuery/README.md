# BufferAndQuery

Practice project: buffer state capitol buildings and query which national parks
fall within a given distance. Data covers the continental US.

<!-- auto:begin -->
## Layers

### State Capitol Buildings

**Source:** `data/state_Capitol_bldgs.shp`  
**Style:** see `styles/state_capitol_bldgs.xml`  

### State Capitol 25-Mile Buffer

**Source:** `output/capitol_buffer.shp`  
**Style:** single symbol — fill #6496ff at 31% opacity, #0050c8 outline  
**Derived from:** `state_capitol_bldgs`  
**Processing:** Buffer State Capitol building points by 25 miles (40,233.6 m in EPSG:3857).

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
state_capitol_bldgs  ──►  capitol_buffer
usaparks  ──►  national_parks
```
<!-- auto:end -->

## Workflow log

See `workflow.md` for the prompt-by-prompt build history and decisions made at
each step.
