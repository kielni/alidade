# Alidade

A toolkit for managing GIS projects as code, built for working with an LLM.

*An alidade is the sighting rule on a plane table — the instrument that draws
the map line, not just the one that measures.*

## Overview

Alidade treats a GIS project as build output, not source. The source of truth
is Python — one file per layer — that you edit in an IDE or describe in plain
English to an LLM. A build step renders those files into a `.qgs` that QGIS
opens, or an `.aprx` that ArcGIS Pro opens. The GIS application stays open as
a viewer; all changes happen in code.

Data processing steps (reprojection, slope calculation, reclassification) are
recorded alongside the layers they produce. The shell command and its inputs are
captured so the full pipeline is reproducible from a fresh checkout, and the
system knows which downstream steps need re-running when an input changes.

## Inspiration

QGIS started as a GUI layer over GDAL, OGR, and GRASS — command-line GIS tools
made accessible through menus and dialogs. That was a big improvement in ease
of use. Over the decades, trying to serve every use case has resulted in
hundreds of buttons, deep menu trees, and a steep learning curve.

This project goes back to those roots — code and shell commands — treating a map
project the way DevOps treats infrastructure: defined in code, committed to git,
and reproducible from a clean checkout. The configuration is visible, diffable,
and batch-editable. Write in English, Python, or both.

Using an LLM lowers the remaining barrier. Geoffrey Litt's
[malleable software](https://www.geoffreylitt.com/2023/03/25/llm-end-user-programming)
argues that LLMs can make any software customizable by its users — not just
programmers, but anyone willing to describe what they want. Tell an LLM to
"add a slope layer colored by steepness" or "make the park boundary dashed" and
it finds the right GDAL flag, the right XML attribute, writes clean Python, and
logs what it did to `workflow.md`. The result is committed, readable, and
reusable — not a sequence of menu clicks that vanishes the moment you close the
dialog.

Robin Sloan's [home-cooked app](https://www.robinsloan.com/notes/home-cooked-app/)
draws a distinction between software built for a mass audience and software you
cook for yourself — personal, imperfect, and fitted exactly to how you work.
This is not a finished product or an installable package. It is a starting
point to fork and shape. The `projects/sample/` and `DESIGN.md` are a starting
point.

QGIS bundles its own Python interpreter, version-locked to each release and
confined to a stripped-down console. This runs in your own environment:
any Python version, any library, full IDE support — key bindings, syntax
highlighting, completion, and navigation.

## Advantages

- **Reproducible** — a fresh checkout rebuilds the project exactly, including
  derived rasters (slope, hillshade) from recorded GDAL commands
- **Diffable** — styles committed as XML; no compressed binaries; meaningful
  git history
- **Batch edits** — change all symbol sizes, swap a color palette, add a
  standard base layer: edit code, not menus
- **LLM-friendly** — each layer is a self-contained Python file; describe a
  change in English and let the LLM implement it; a `workflow.md` log captures
  the prompts and decisions so a new session can continue without reconstructing
  context
- **IDE-native** — browse, search, and edit layer configuration in your editor,
  not GIS dialogs
- **Dual output** — the same `project.py` spec can render to QGIS or ArcGIS Pro
  without duplicating layer definitions

## Use cases

This tool could be for you if:

- You make maps in QGIS or ArcGIS Pro and are frustrated that the project file
  is a compressed binary you can't diff, review, or batch-edit
- You're comfortable writing Python and want to manage map configuration the way
  you manage code: IDE editing, meaningful commits, reproducible builds
- You want to describe map changes in plain English to an LLM rather than
  hunting through menus or looking up GDAL flags
- You want to script repetitive work — standard base layers, consistent
  symbology across projects — without clicking through menus each time

## Getting started

### Requirements

- QGIS 3.x desktop app (Mac: `/Applications/QGIS.app`; configure path in
  `local.env`) — for QGIS output
- ArcGIS Pro 3.4+ — for `.aprx` output
- [uv](https://docs.astral.sh/uv/)
- GDAL CLI tools (`brew install gdal`) — used for raster operations (slope,
  hillshade, reprojection) where no clean Python equivalent exists

Processing steps prefer Python libraries (geopandas for vector operations like
filtering, buffering, and spatial joins) over shell commands. GDAL CLI is
reserved for raster work (`gdaldem`, `gdalwarp`, `gdal_calc`) that has no
clean Python equivalent.

### Install

```bash
git clone <repo>
cd alidade
uv sync                          # installs alidade as an editable package
cp local.env.example local.env   # edit if QGIS is not at the default path
```

`uv sync` installs `alidade` into the project virtualenv in editable mode, so
the `alidade-build`, `alidade-dump`, `alidade-extent`, and `alidade-validate`
console scripts are available via `uv run`. Project layer files import from
`alidade.models` like any other installed package.

### QGIS setup

Copy `alidade/util/qgis_startup.py` to your QGIS startup script so that the
project reload shortcut is available:

```bash
cp alidade/util/qgis_startup.py \
   ~/Library/Application\ Support/QGIS/QGIS3/startup.py
```

Optionally install the **Reloader** plugin via *Plugins → Manage and Install
Plugins* — it watches data files and auto-reloads affected layers on change.

## Directory layout

```
alidade/
  alidade/
    models.py               — Pydantic types: Project, Layer, renderers, symbols, print layouts
    dump_qgis.py            — import a .qgz into a project directory (QGIS only)
    render_qgis.py          — project.py → output/project.qgs + output/print.qpt
    render_lyrx.py          — project.py → output/{layer.id}.lyrx (CIM v3.4.0 JSON)
    lyrx/                   — CIM builder subpackage
    build.py                — entry point; dispatches on output_format
    util/
      qgis_startup.py       — QGIS startup script (Ctrl-R reload shortcut)
      export_pdf.py         — QGIS console script to export print layout to PDF

  projects/                 — one directory per project
    project.py              — source of truth (edit this)
    data/                   — data files
    styles/                 — per-layer XML extracted from the .qgz (QGIS only)
    output/                 — generated project files and derived data (gitignored)
```

## Project types

`project.py` declares the output format via `output_format`:

```python
# QGIS project
from alidade.models import Project

spec = Project(output_format="qgis", title="My Map", crs="EPSG:3857", layers=[...])
```

```python
# ArcGIS Pro project (.lyrx per layer)
from alidade.models import Project

spec = Project(output_format="lyrx", title="My Map", crs="EPSG:3857", layers=[...])
```

`make build DIR=my_project` detects the format and routes to the right renderer.

## Import an existing QGIS project

```bash
# place my_project.qgz inside my_project/, then:
make dump DIR=my_project    # extract layers and styles from the .qgz
make build DIR=my_project   # render project.py → output/project.qgs
```

`dump` writes one Python file per layer under `layers/` and one XML file per
style under `styles/`. Rename the layer IDs from QGIS-generated UUIDs to
human-friendly names before committing.

## Workflow

- Edit a layer file or describe the change to an LLM.
- Run `make build DIR=my_project`.
- **QGIS:** reload with Ctrl-R.
- **ArcGIS Pro:** copy `output/*.lyrx` and shapefiles to Windows, then drag
  into the map (see [Using .lyrx files in ArcGIS Pro](#using-lyrx-files-in-arcgis-pro)).
- Commit `project.py` and updated layer files.

For derived rasters, run `make build --force DIR=my_project` when source data
or a processing command changes. This re-runs stale transforms in dependency
order before rendering.

## Build

`make build DIR=my_project` runs black on the project source, loads
`project.py`, runs any stale processing steps in dependency order, and renders
the spec. Steps whose output already exists are skipped.

**QGIS output** (`QGISProject`):

- `output/project.qgs` — open in QGIS; reload after each rebuild with Ctrl-R
- `output/print.qpt` — print template, when `project.py` has a `print_layout`
  field; US Letter with map frame, title, north arrow, scale bar, legend,
  credits
- `output/<derived files>` — shapefiles, rasters from processing steps
- `README.md` — Layers and Data flow sections regenerated from the spec

**ArcGIS Pro output** (`output_format="lyrx"`):

- `output/{layer.id}.lyrx` — one standalone CIM v3.4.0 JSON file per layer;
  each file embeds both the symbology and the path to its shapefile
- `output/<derived files>` — shapefiles, rasters from processing steps

### Using .lyrx files in ArcGIS Pro

Each `.lyrx` is a self-contained `CIMLayerDocument` — it carries the full
renderer (graduated colors, SVG markers, etc.) *and* a data connection that
points to the shapefile on disk. The data connection uses an absolute path, so
it must match where the files land on the ArcGIS Pro machine.

**Setup (once):** add `ARCGIS_WORKSPACE_ROOT` to `local.env` so paths in the
generated `.lyrx` files are written for the Windows machine rather than the Mac.
`local.env` uses Makefile syntax; forward slashes work on Windows and avoid
any backslash ambiguity:

```makefile
ARCGIS_WORKSPACE_ROOT := C:/Users/you/GIS
```

With this set, a source like `./output/census_tracts.shp` in a project at
`projects/lab5/` becomes `DATABASE=C:/Users/you/GIS/lab5/output` in the
`.lyrx`, which ArcGIS Pro resolves without any manual path repair.

**Each build:**

1. Run `make build DIR=my_project` on the Mac — `.lyrx` files appear in `output/`.
2. Copy `output/*.lyrx` and the matching `output/*.shp` (plus `.dbf`, `.shx`,
   `.prj`, `.cpg` sidecar files) to `C:\Users\you\GIS\my_project\output\` on
   the Windows machine.
3. In ArcGIS Pro, open the **Catalog** pane (*View → Catalog Pane*), navigate
   to that folder, and drag one or more `.lyrx` files into the map — **or** use
   *Map → Add Data → Add Layer From File*.
4. Each layer opens with its symbology intact and data already connected.

After rebuilding, remove the old layers from the Contents pane and drag the
updated `.lyrx` files back in; ArcGIS Pro does not live-reload layer files.

### Using the QGIS print template

Open *Project → Layout Manager → From template* and select `output/print.qpt`.
Adjust items interactively and export via the normal print menu. Export as a
template to a new filename to preserve manual edits across builds.

**Exporting to PDF from the QGIS console:** open *Plugins → Python Console* and run:

```python
exec(open("/path/to/alidade/alidade/util/export_pdf.py").read())
```

The script loads `output/print.qpt` and writes `output/print.pdf`. To use a
different template, set `print_prefix` before the `exec` call.

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

Create and describe a new layer `national_parks` that filters the `usaparks`
source to National Park Service polygons.

```python
from pathlib import Path

import geopandas as gpd

from alidade.models import Layer, ProcessingStep, PythonAction


def filter_national_park_service(src: Path, output: Path) -> None:
    gdf = gpd.read_file(src)
    gdf[gdf["FCC"] == "D83"].to_file(output)


national_parks = Layer(
    id="national_parks",
    name="National Parks",
    type="vector",
    source="./output/national_parks.shp",
    provider="ogr",
    crs="EPSG:3857",
    visible=True,
    geometry_type="Polygon",
    processing_step=ProcessingStep(
        description=(
            "Filter USAParks to FCC='D83' (National Park Service units:"
            " national parks, monuments, historic parks, seashores, etc.)."
        ),
        action=PythonAction(fn=filter_national_park_service),
        depends_on=["usaparks"],
        output=Path("output/national_parks.shp"),
    ),
)
```

along with a human-readable log

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
- `layers/national_parks.py` — processing function defined inline in the layer file

See `DESIGN.md` for architecture decisions and `projects/sample/workflow.md` for an
example of the LLM prompt log.
