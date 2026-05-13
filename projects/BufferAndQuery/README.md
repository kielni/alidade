# BufferAndQuery

Practice project: buffer state capitol buildings and query which national parks
fall within a given distance. Data covers the continental US.

<!-- auto:begin -->
## Layers

### National Parks

**Source:** `output/national_parks.shp`  
**Style:** single symbol — fill #78c864 at 50% opacity, #006400 outline  
**Derived from:** `usaparks`  
**Processing:** Filter USAParks to FCC='D83' (National Park Service units: national parks, monuments, historic parks, seashores, etc.).

### State Capitol Buildings

**Source:** `data/state_Capitol_bldgs.shp`  
**Style:** see `styles/state_capitol_bldgs.xml`  

### CartoDB Positron

**Source:** `CartoDB Positron XYZ tile service`  
**Style:** see `styles/cartodb_positron.xml`  

## Data flow

```
usaparks  ──►  national_parks
```
<!-- auto:end -->

## Workflow log

See `workflow.md` for the prompt-by-prompt build history and decisions made at
each step.
