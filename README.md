# Alidade

A toolkit for managing QGIS projects as code, built for working with an LLM.

*An alidade is the sighting rule on a plane table — the instrument that draws
the map line, not just the one that measures.*

## Overview

Alidade treats a QGIS project as build output, not source. The source of truth
is Python — one file per layer — that you edit in an IDE or describe in plain
English to an LLM. A build step renders those files into a `.qgs` that QGIS
opens. QGIS stays open as a viewer; all changes happen in code.

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
This is not a finished product or an installable
package. It is a starting point to fork and shape. The projects/sample/ and
DESIGN.md are a starting point.

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
  not QGIS dialogs

## Use cases

This tool could be for you if:

- You make maps in QGIS and are frustrated that the project file is a
  compressed binary you can't diff, review, or batch-edit
- You're comfortable writing Python and want to manage map configuration the way
  you manage code: IDE editing, meaningful commits, reproducible builds
- You want to describe map changes in plain English to an LLM rather than
  hunting through menus or looking up GDAL flags
- You want to script repetitive work — standard base layers, consistent
  symbology across projects — without clicking through menus each time

## Getting started

### Requirements

- QGIS 3.x desktop app (Mac: `/Applications/QGIS.app`; configure path in
  `local.env`)
- [uv](https://docs.astral.sh/uv/)
- GDAL CLI tools (`brew install gdal`) — used for raster operations (slope,
  hillshade, reprojection) where no clean Python equivalent exists; QGIS.app
  bundles its own GDAL but does not expose the command-line tools

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
the `alidade-build`, `alidade-dump`, `alidade-capture`, and `alidade-validate`
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
    models.py          — Pydantic types for layers, renderers, symbols, print layouts
    dump.py            — import a .qgz into a project directory
    render.py          — render project.py → output/project.qgs and output/print.qpt
    build.py           — entry point with incremental rebuild
    util/
      qgis_startup.py  — QGIS startup script (Ctrl-R reload shortcut)
      export_pdf.py    — QGIS console script to export the print layout to PDF
  
  projects/            — one directory per project
    project.py         — source of truth (edit this)
    data/              — data files
    styles/            — per-layer XML extracted from the .qgz
    output/            — generated .qgs, print.qpt, and derived rasters (gitignored)
```

### Import an existing QGIS project

```bash
# place my_project.qgz inside my_project/, then:
make dump DIR=my_project    # extract layers and styles from the .qgz
make build DIR=my_project   # render project.py → output/project.qgs
```

`dump` writes one Python file per layer under `layers/` and one XML file per
style under `styles/`. Rename the layer IDs from QGIS-generated UUIDs to
human-friendly names before committing.

Edit `my_project/project.py` to assemble your layers. Add layer files under
`my_project/layers/` and data under `my_project/data/`.

```bash
make build DIR=my_project
# open my_project/output/project.qgs in QGIS
# after each rebuild, reload with Ctrl-R
```

### Workflow

- Edit a layer file or describe the change to an LLM. 
- Run `make build DIR=my_project`. 
- Reload in QGIS with Ctrl-R. 
- Commit `project.py` and updated `layers` and `styles/`.

For derived rasters, run `make prepare DIR=my_project` when source data or a
processing command changes. This re-runs stale transforms in dependency order,
then triggers a build.


### Build

`make build DIR=my_project` runs black on the project source, loads
`project.py`, runs any stale processing steps in dependency order, and renders
the spec into the `output/` directory. Steps whose output already exists are
skipped; `make build-all` forces a full rebuild.

**Artifacts:**

- `output/project.qgs` — the QGIS project file. Open this in QGIS; reload
  after each rebuild with Ctrl-R.
- `output/<derived files>` — shapefiles, rasters, or other outputs produced by
  processing steps (filtering, reprojection, reclassification, etc.).
- `output/print.qpt` — QGIS print template, produced when `project.py` has a
  `print_layout` field. US Letter landscape with a full-page map frame, title
  strip, north arrow, scale bar, legend, and credits label. Page dimensions,
  item positions, and scale bar units are all configurable fields — see
  `alidade/models.py` for defaults and a layout diagram.
- `README.md` — the Layers and Data flow sections are regenerated from the
  current project spec.

**Using the print template in QGIS:** open *Project → Layout Manager → From
template* and select `output/print.qpt`. From there you can adjust items
interactively and export via the normal print menu.

**Exporting the print layout to PDF from the console:** open the Python console
in QGIS (**Plugins → Python Console**) and run:

```python
exec(open("/path/to/alidade/alidade/util/export_pdf.py").read())
```

The script loads `output/print.qpt` into the Layout Manager if it is not
already there, then writes `output/print.pdf`. To use a different template and output filename, set `print_prefix` before the
`exec` call — it loads `<prefix>.qpt` and writes `<prefix>.pdf`:

```python
print_prefix = "overview"
exec(open("/path/to/alidade/alidade/util/export_pdf.py").read())
```


#### Building your toolbox

This project does not try to cover every use case. The models, renderers, and
utilities here are a starting point, not a complete framework. The layout may not
fit your mental model or workflow style.

Iterate to build and customize your own toolbox:

1. **Craft the artifact the tedious way.** Do it manually in QGIS — click
   through the dialogs, export the QPT, write the console script by hand. Get
   the thing working before you think about abstraction.
2. **Study it.** Read the file it produced. Understand which parts are fixed
   structure and which parts are project-specific variables. Note what you had
   to look up.
3. **Generalize it.** Extract the variables into a Pydantic model. Write the
   render function. Document what each field controls and what can be left at
   its default. Add it to the toolbox so the next project starts further along.

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