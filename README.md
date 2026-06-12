# Alidade

A toolkit for managing GIS projects as code, built for working with an LLM.

*An alidade is the sighting rule on a plane table - the instrument that draws
the map line, not just the one that measures.*

## Overview

Alidade treats a GIS project as build output, not source. The source of truth
is Python that you edit in an IDE or describe in plain English to an LLM.

The same project spec renders to multiple formats: QGIS project files (`.qgs`)
for desktop review, ArcGIS Pro layer files (`.lyrx`) for handoff, static PNG
maps for documentation and story maps, or published directly to ArcGIS Online
as hosted feature and imagery layers.

Data processing steps — reprojection, slope calculation, reclassification — are
written as Python functions or shell commands and stored alongside the layers
they produce. The full pipeline is reproducible from a fresh checkout; the build
system tracks which downstream steps need re-running when an input changes.

## Inspiration

QGIS started as a GUI layer over GDAL, OGR, and GRASS: command-line GIS tools
made accessible through menus and dialogs. Over the decades, trying to serve every
use case has resulted in hundreds of buttons, deep menu trees, and a steep learning
curve.

This project goes back to roots in code and shell commands, treating a map
project the way DevOps treats infrastructure: defined in code, committed to git,
and reproducible from a clean checkout. The configuration is visible, diffable,
and batch-editable. Write in English, Python, or both.

Using an LLM lowers the remaining barrier. Geoffrey Litt's
[malleable software](https://www.geoffreylitt.com/2023/03/25/llm-end-user-programming)
argues that LLMs can make any software customizable by its users - not just
programmers, but anyone willing to describe what they want. Tell an LLM to
"add a slope layer colored by steepness" or "make the park boundary dashed" and
it finds the right GDAL flag, the right XML attribute, writes clean Python, and
logs what it did to `workflow.md`. The result is committed, readable, and
reusable, not a sequence of menu clicks that vanishes the moment you close the
dialog.

Robin Sloan's [home-cooked app](https://www.robinsloan.com/notes/home-cooked-app/)
draws a distinction between software built for a mass audience and software you
cook for yourself: personal, imperfect, and fitted exactly to how you work.
This is not a finished product or an installable package. It is a starting
point to fork and shape. The `projects/sample/` and `DESIGN.md` are a starting
point.

QGIS bundles its own Python interpreter, version-locked to each release and
confined to a stripped-down console. This runs in your own environment:
any Python version, any library, full IDE support, key bindings, syntax
highlighting, completion, and navigation.

## Advantages

- **Reproducible** - a fresh checkout rebuilds the project exactly, including
  derived rasters (slope, hillshade) from recorded GDAL commands
- **Diffable** - styles committed as XML; no compressed binaries; meaningful
  git history
- **Batch edits** - change all symbol sizes, swap a color palette, add a
  standard base layer: edit code, not menus
- **LLM-friendly** - each layer is a self-contained Python file; describe a
  change in English and let the LLM implement it; a `workflow.md` log captures
  the prompts and decisions so a new session can continue without reconstructing
  context
- **IDE-native** - browse, search, and edit layer configuration in your editor,
  not GIS dialogs
- **Multi output** - the same `main.py` spec renders to QGIS project files,
  ArcGIS Pro `.lyrx` layer files, ArcGIS Online hosted layers, or static PNG
  maps — without duplicating layer definitions

## Use cases

- You make maps in QGIS or ArcGIS Pro and are frustrated that the project file
  is a compressed binary you can't diff, review, or batch-edit
- You're comfortable writing Python and want to manage map configuration the way
  you manage code: IDE editing, meaningful commits, reproducible builds
- You want to describe map changes in plain English to an LLM rather than
  hunting through menus or looking up GDAL flags
- You want to script repetitive work (standard base layers, consistent
  symbology across projects) without clicking through menus each time

## Getting started

### Requirements

- [uv](https://docs.astral.sh/uv/)
- GDAL CLI tools (`brew install gdal`) - used for raster operations (slope,
  hillshade, reprojection) where no clean Python equivalent exists

Prefer Python libraries (geopandas for vector operations like
filtering, buffering, and spatial joins) over shell commands. GDAL CLI is
reserved for raster work (`gdaldem`, `gdalwarp`, `gdal_calc`) that has no
clean Python equivalent.

Optional, to open or export the generated output:

- QGIS 3.x — to view `.qgs` project files and export print layouts to PDF
- ArcGIS Pro — to use `.lyrx` layer files

### Install

```bash
git clone <repo>
cd alidade
uv sync                          # installs alidade as an editable package
cp local.env.example local.env   # add ArcGIS credentials and workspace settings
```

`uv sync` installs `alidade` into the project virtualenv in editable mode. All
operations are available as `make` targets:

| Target | Purpose |
|---|---|
| `make build DIR=<dir>` | Full build: process layers, render output |
| `make build-all DIR=<dir>` | Force rebuild of all layers regardless of timestamps |
| `make map DIR=<dir>` | Render static PNG maps without a full rebuild |
| `make publish DIR=<dir>` | Publish layers and web maps to ArcGIS Online |
| `make dump DIR=<dir>` | Import a `.qgz` into a project directory |
| `make extent DIR=<dir>` | Print canvas extent from a saved `.qgs` |
| `make validate DIR=<dir>` | Check that all source and style paths exist |
| `make lint` | Run black + flake8 + mypy on all source |
| `make clean DIR=<dir>` | Remove `output/` |

## Output formats

### QGIS

`output_format="qgis"` (the default). `make build DIR=<dir>` writes:

- `output/project.qgs` — open in QGIS; reload after each build with Ctrl-R
- `output/print.qpt` — print template, when `main.py` defines a `print_layout`;
  US Letter with map frame, title, north arrow, scale bar, legend, and credits

```python
from alidade.models import Map

spec = Map(output_format="qgis", title="My Map", crs="EPSG:3857", layers=[...])
```

**Setup (once):** copy the startup script so the Ctrl-R reload shortcut is
available in QGIS:

```bash
cp alidade/util/qgis_startup.py \
   ~/Library/Application\ Support/QGIS/QGIS3/startup.py
```

Optionally install the **Reloader** plugin (*Plugins → Manage and Install
Plugins*) — it watches data files and auto-reloads affected layers on change.

**Print template:** open *Project → Layout Manager → From template* and select
`output/print.qpt`. Adjust items interactively and export via the normal print
menu. Export as a template to a new filename to preserve manual edits across
builds.

**Exporting to PDF:** open *Plugins → Python Console* and run:

```python
exec(open("/path/to/alidade/alidade/util/export_pdf.py").read())
```

The script loads `output/print.qpt` and writes `output/print.pdf`. To use a
different template, set `print_prefix` before the `exec` call.

**Importing an existing QGIS project:**

```bash
# place my_project.qgz inside my_project/, then:
make dump DIR=my_project    # extract layers and styles from the .qgz
make build DIR=my_project   # render main.py → output/project.qgs
```

`dump` writes one Python file per layer under `layers/` and one XML file per
style under `styles/`. Rename the layer IDs from QGIS-generated UUIDs to
human-friendly names before committing.

### ArcGIS Pro

`output_format="lyrx"`. `make build DIR=<dir>` writes one `.lyrx` file per
layer:

- `output/{layer.id}.lyrx` — standalone CIM v3.4.0 JSON; embeds the full
  renderer (graduated colors, SVG markers, etc.) and a data connection pointing
  to its shapefile on disk

```python
from alidade.models import Map

spec = Map(output_format="lyrx", title="My Map", crs="EPSG:3857", layers=[...])
```

**Setup (once):** add `ARCGIS_WORKSPACE_ROOT` to `local.env` so paths in
`.lyrx` files are written for the Windows machine rather than the Mac.
`local.env` uses Makefile syntax; forward slashes work on Windows and avoid
backslash ambiguity:

```makefile
ARCGIS_WORKSPACE_ROOT := C:/Users/you/GIS
```

With this set, a source like `./output/census_tracts.shp` in a project at
`projects/lab5/` becomes `DATABASE=C:/Users/you/GIS/project/output` in the
`.lyrx`, which ArcGIS Pro resolves without any manual path repair.

**Each build:**

1. Run `make build DIR=<dir>` on the Mac — `.lyrx` files appear in `output/`.
2. Copy `output/*.lyrx` and the matching shapefiles (`.shp`, `.dbf`, `.shx`,
   `.prj`, `.cpg` sidecar files) to `C:\Users\you\GIS\<project>\output\` on
   Windows.
3. In ArcGIS Pro, open the **Catalog** pane (*View → Catalog Pane*), navigate
   to that folder, and drag `.lyrx` files into the map — or use
   *Map → Add Data → Add Layer From File*.
4. Each layer opens with its symbology intact and data already connected.

After rebuilding, remove the old layers from the Contents pane and drag the
updated `.lyrx` files back in — ArcGIS Pro does not live-reload layer files.

### ArcGIS Online

`make publish DIR=<dir>` uploads every layer to ArcGIS Online and creates or
updates web maps. Layers are published as hosted Feature Layers (vector) or
Imagery Layers (raster); renderers from the alidade spec are translated to the
ArcGIS REST API format. It can also create or update Story Maps.

**Setup (once):** add to `local.env`:

```makefile
ARCGIS_CLIENT_ID := <your OAuth client ID>
```

To get a client ID: in ArcGIS Online go to *Content > New Item > Application*,
register a new application, and copy the Client ID from its item page. The
publish script uses this ID to trigger a browser-based OAuth login; credentials
are cached locally by the arcgis SDK after the first sign-in.

`local.arcgis.json` (created automatically on first publish, gitignored) stores
the ArcGIS item IDs for each published layer. Subsequent runs overwrite rather
than create duplicate items.

```bash
make publish DIR=projects/goats              # publish all layers, create web maps
make publish DIR=projects/goats MAP=slope    # publish one named map
```

To pass additional options, call the module directly:

```bash
uv run python -m alidade.publish_arcgis <dir> [options]
```

Options:

- `--map <id>` — publish one named map from the `maps` list
- `--renderer-only` — skip data upload; re-apply renderers to already-registered layers
- `--dry-run` — prepare data files and print what would be published without making any API calls
- `--create-maps` — create or update ArcGIS web maps (included automatically by `make publish`)
- `--story-map-id <item_id>` — update a Story Map after publishing; new web maps are appended

**What gets published:**

| Layer type | Upload format | ArcGIS type |
|---|---|---|
| vector (.geojson) | GeoJSON, reprojected to WGS84 | Feature Layer |
| vector (.shp / .gpkg) | zipped shapefile | Feature Layer |
| raster (.tif) | GeoTiff, reprojected to EPSG:3857 | Imagery Layer |

Tile services (XYZ/WMS basemaps) and layers whose output files do not yet
exist are skipped with a warning. Raster renderers (PalettedRenderer) cannot
be applied via the REST API — configure color classification in Map Viewer after
upload.

### Static PNG

`make map DIR=<dir>` renders each map in the project's `maps` list to a static
PNG using matplotlib and geopandas. No GIS application needed; useful for
quick visual review and documentation.

```bash
make map DIR=projects/goats              # render all maps → output/map_<id>.png
make map DIR=projects/goats MAP=slope    # render one named map
```

Output lands in `output/` alongside built project files. WMS/tile basemap
layers are skipped; raster layers are drawn from local `.tif` files.

If `main.py` defines no `maps` list, the default `spec` is rendered as
`output/map.png`.

## Workflow

1. Edit a layer file or describe the change to an LLM (ie "update census layer to use color brewer purples").
2. Run `make build DIR=<dir>`.
3. Review the output for your format:
   - **QGIS:** reload with Ctrl-R.
   - **ArcGIS Pro:** copy `output/*.lyrx` and shapefiles to Windows, remove old
     layers, and drag the updated files into the map.
   - **ArcGIS Online:** run `make publish DIR=<dir>`.
   - **Static PNG:** open `output/map_*.png` in IDE, browser, or other image viewer.
4. Commit `main.py` and updated layer files.

## Colors

Specify colors as `Color` objects constructed from hex strings. Conversions to
other formats happen automatically at the rendering boundary.

```python
from alidade.color import Color, brewer

Color.from_hex("#1a9850")               # opaque
Color.from_hex("#1a9850", alpha=200)    # semi-transparent (alpha 0-255)
Color.from_hex("#1a9850").with_alpha(128)  # copy at different opacity
brewer("sequential.Purples", 4)          # 4-color ColorBrewer ramp → list[Color]
```

Put project-specific colors in `projects/<name>/palette.py` as named semantic
constants. Name by role, not by color (`ROADS_LINE` not `ROAD_BROWN`), so names
stay meaningful if the palette changes later:

```python
# projects/myproject/palette.py
from alidade.color import Color, brewer

PARK_FILL    = Color.from_hex("#ffffff")
PARK_BORDER  = Color.from_hex("#6464c8", alpha=180)
SLOPE_GENTLE = Color.from_hex("#1a9641")
SUITABILITY  = brewer("sequential.Purples", 4, alpha=200)
```

Then import them in layer files:

```python
from projects.myproject.palette import PARK_BORDER, SLOPE_GENTLE
```

Generic constants (`BLACK`, `WHITE`, `TRANSPARENT`, `DARK_GRAY`, `LABEL_GRAY`)
are in `alidade.color` for use in model defaults and shared rendering code.

## Build

`make build DIR=<dir>` generates `output/GEN.mk` from the layer graph,
invokes make against it to run any stale processing steps in dependency order,
then renders the spec. Each layer output is a make target; make skips it when
the output file is newer than its source files and inputs. Formatting (`black`)
is tracked by an `output/.formatted` stamp and runs only when a source file
changes.

`make build-all DIR=<dir>` forces all processing steps to re-run regardless of
timestamps.

## Building your toolbox

This project does not try to cover every use case. The models, renderers, and
utilities here are a starting point, not a complete framework.

1. **Craft the artifact the tedious way.** Do it manually in the GIS app —
   click through the dialogs, get the thing working before thinking about
   abstraction.
2. **Study it.** Read the file it produced. Understand which parts are fixed
   structure and which are project-specific variables.
3. **Generalize it.** Extract the variables into a Pydantic model. Write the
   render function. Document what each field controls and what can be left at
   its default.

## When generated artifacts don't work

Copy the broken generated file to a separate path (e.g. `project_bad.qgs` or
`project_bad.aprx`) so you can compare it later. Open the project in the GIS
app, manually fix the layer, and save to the original path. You now have a
working file the app produced and a broken file the generator produced.

Ask the LLM to compare the two files and explain what differs. Once the
differences are understood, apply updates so the generator produces correct
output. Regenerate and verify before committing.

## Example

Each layer lives in its own file. The module docstring describes what the layer
does and why; the `Layer` definition declares its inputs, output, and renderer;
the build function runs at `make build` time when any input has changed.

`projects/goats/layers/roads_trails.py`:

```python
def clip_roads_trails(layer: BoundLayer) -> None:
    """Reproject and clip roads and trails to park boundary."""
    (border,) = layer.inputs
    gdf = gpd.read_file(layer.raw_path)
    keep = {"@id", "name", gdf.geometry.name}
    gdf = gdf[[c for c in gdf.columns if c in keep]]
    gdf = gdf[gdf.geom_type.isin(["LineString", "MultiLineString"])].to_crs(CRS)
    clip_border(gdf, border.path).to_file(layer.path, driver="GPKG")


roads_trails = Layer(
    id="roads_trails",
    name="Roads & Trails",
    type="vector",
    inputs=[border],
    raw_file="data/roads_trails.geojson",
    source_description="Road and trail lines",
    source_origin="OpenStreetMap via Overpass Turbo",
    datasource="output/roads_trails.gpkg",
    crs=CRS,
    geometry_type="LineString",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="line",
            layers=[SimpleLine(line_color=ROADS_LINE, line_width=0.5)],
        )
    ),
    action=PythonAction(fn=clip_roads_trails),
)
```

The corresponding `workflow.md` entry, written in the same session:

```markdown
## Step 7 — Roads and trails

Reprojected `data/roads_trails.geojson` to EPSG:26910, filtered to LineString
and MultiLineString only (drops the one Polygon feature), clipped to clip border.

**Files created:**
- `layers/roads_trails.py` — `clip_roads_trails`; output `output/roads_trails.gpkg`
```

See `DESIGN.md` for architecture decisions and `projects/sample/workflow.md` for an
example of the LLM prompt log.
