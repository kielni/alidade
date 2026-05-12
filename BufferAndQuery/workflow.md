# BufferAndQuery workflow

Practice project: buffer state capitol buildings and query which parks fall
within a given distance. Data covers the continental US.

---

## Step 1 — Bootstrap project from existing .qgs file

**Prompt:** dump the BufferAndQuery project; find the qgs or qgz under the path

**What this does:**

Parsed `BufferAndQuery.qgs` to generate layer Python files and style XMLs.
Three source layers:

| Layer | File | Description |
|-------|------|-------------|
| `usaparks` | `data/USAParks.shp` | 6,370 US parks of all types (TIGER FCC D83–D85) |
| `state_capitol_bldgs` | `data/state_Capitol_bldgs.shp` | State capitol building footprints |
| `openstreetmap` | TMS tile service | Basemap |

Project CRS: EPSG:3857. Extent: western continental US.

**Files created:**
- `layers/usaparks.py`
- `layers/state_capitol_bldgs.py`
- `layers/openstreetmap.py`
- `styles/usaparks.xml`, `styles/state_capitol_bldgs.xml`, `styles/openstreetmap.xml`
- `project.py`

---

## Step 2 — Create National Parks layer from USAParks

**Prompt:** create a new layer from Parks: find all polygons with the TIGER FCC
codes for National Parks; log to project workflow

**What this does:**

Inspected `data/USAParks.dbf` to identify TIGER FCC codes:

| FCC | Count | Description |
|-----|------:|-------------|
| D83 |   423 | National Park Service units (NP, NHP, NMEM, seashores, etc.) |
| D84 |   155 | National Forests (USFS) |
| D85 | 5,792 | State and local parks |

Created `national_parks` as a derived layer that filters `usaparks` to
`FCC='D83'` using `ogr2ogr`. The filter runs as a processing step at
`make build` time and writes `output/national_parks.shp`.

Why D83 and not D84/D85: the exercise target is NPS-administered lands
(national parks, monuments, historic parks, seashores). National Forests
(D84) and state/local parks (D85) are separate jurisdictions.

**Files created:**
- `layers/national_parks.py`
- `helpers.py` — `filter_national_parks(inputs, output)` using `ogr2ogr -where "FCC='D83'"`

---

## Step 3 — Style national parks layer

**Prompt:** update national parks layer styling: dark green outline, lighter green fill with 50% opacity

**What this does:**

Added a `SingleSymbol` renderer to `national_parks` with a `SimpleFill`:

- Fill: `120,200,100` at 50% opacity (alpha 128) — medium-light green
- Outline: `0,100,0` at full opacity — dark green

The fill alpha is set in the color string rather than on the `Symbol`, so the
outline stays fully opaque while only the fill is transparent.

**Files changed:**
- `layers/national_parks.py` — added `renderer=SingleSymbol(...)`
