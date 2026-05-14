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

Created `national_parks` as a derived layer with a `PythonAction` that filters
`usaparks` to `FCC == "D83"` using geopandas. The filter runs at `make build`
time and writes `output/national_parks.shp`.

Why D83 and not D84/D85: the exercise target is NPS-administered lands
(national parks, monuments, historic parks, seashores). National Forests
(D84) and state/local parks (D85) are separate jurisdictions.

**Files created:**
- `layers/national_parks.py` — `filter_national_park_service(src, output)` filters to `FCC == "D83"`

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

---

## Step 4 — Replace OpenStreetMap basemap with CartoDB Positron

**Prompt:** replace openstreetmap layer with a cartodb light basemap

**What this does:**

Swapped the basemap from OpenStreetMap (GDAL WMS/TMS) to CartoDB Positron
(WMS XYZ tile service). Positron is a neutral light-gray basemap that keeps
focus on the data layers rather than road/label detail.

Source URL: `https://basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png`
(percent-encoded in the QGIS WMS connection string).

**Files created/changed:**
- `layers/cartodb_positron.py` — new layer file (same source as sample project)
- `styles/cartodb_positron.xml` — copied from `sample/styles/`
- `project.py` — replaced `openstreetmap` import and layer reference

---

## Step 5 — Create 25-mile buffer around State Capitol buildings

**Prompt:** create a new layer with one 25-mile polygon around each point in
State Capitol buildings

**What this does:**

Created `capitol_buffer` as a derived layer with a `PythonAction` that buffers
each capitol building point using geopandas.

Buffer distance: 25 mi × 1,609.344 m/mi = **40,233.6 m** (planar, in EPSG:3857).

```python
BUFFER_METERS = 25 * 1_609.344  # 25 miles, in EPSG:3857 meters
gdf["geometry"] = gdf.geometry.buffer(BUFFER_METERS)
```

Styling: semi-transparent blue fill (`100,150,255` at ~31% opacity) with a
solid medium-blue outline (`0,80,200`).

Layer order in project.py (top → bottom):

| Layer | Note |
|-------|------|
| `state_capitol_bldgs` | Points stay on top |
| `capitol_buffer` | Buffer polygons beneath points |
| `national_parks` | Park polygons below buffers |
| `cartodb_positron` | Basemap |

**Files created/changed:**
- `layers/capitol_buffer.py` — `buffer_capitol_buildings(src, output)` using `gdf.geometry.buffer()`
- `project.py` — added `capitol_buffer` import and layer reference

---

## Step 6 — Select capitol buffers that intersect a national park

**Prompt:** add a new layer: state capitol buffer polygons that intersect a
national park polygon; output the count of selected state capitols

**What this does:**

Created `capitol_parks_intersect` as a derived layer with a `PythonAction` that
uses a geopandas spatial join to select capitol buffers overlapping at least one
national park. The count is printed to stdout.

```python
joined = gpd.sjoin(buffers, parks[["geometry"]], how="inner", predicate="intersects")
result = buffers.loc[joined.index.unique()]
```

`parks[["geometry"]]` is passed as the right frame (geometry only) to avoid
column-name conflicts. `index.unique()` deduplicates buffers that intersect
multiple parks.

Result: **15** state capitol buffers intersect a national park.

Styling: orange fill (`255,160,50` at ~43% opacity) with a dark-orange outline
(`200,90,0`) so the selected buffers are visually distinct from the full blue
buffer set beneath them.

Layer order in project.py (top → bottom):

| Layer | Note |
|-------|------|
| `state_capitol_bldgs` | Points stay on top |
| `capitol_parks_intersect` | Highlighted matching buffers |
| `capitol_buffer` | All 25-mile buffers |
| `national_parks` | Park polygons |
| `cartodb_positron` | Basemap |

**Files created/changed:**
- `layers/capitol_parks_intersect.py` — `filter_capitol_buffers_near_parks(buffers_path, parks_path, output)` using `gpd.sjoin`
- `project.py` — added `capitol_parks_intersect` import and layer reference
