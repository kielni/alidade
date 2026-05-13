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

Alidade goes back to those roots — code and shell commands — made newly
accessible by modern tools. Instead of clicking dialogs, you write Python or describe
changes in plain English. The steps in building a map are visible and editable,
expressed in code rather than dialog boxes. Using an LLM adds an English
interface: "add a slope layer colored by steepness," "make the park boundary
dashed", without requiring you to know the GDAL command or where to find the
symbology dialog.

QGIS bundles its own Python interpreter, version-locked to each release and
lagging behind the current language, with editing confined to a limited console.
Alidade runs outside that environment: use the latest Python, manage
dependencies with uv, and bring in any library you want. You also get a full
development environment: your own IDE, key bindings, syntax highlighting, and
completion, rather than a stripped-down console.

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

This tool could be for for you if:

- You make maps in QGIS and are frustrated that the project file is a
  compressed binary you can't diff, review, or batch-edit
- You're comfortable writing Python and want to manage map configuration the way
  you manage code: IDE editing, meaningful commits, reproducible builds
- You want to describe map changes in plain English to an LLM rather than
  hunting through menus or looking up GDAL flags
- You want to script repetitive work — standard base layers, consistent
  symbology across projects — without clicking through menus each time

**This is not a finished framework.** The scripts are a working base to fork
and modify. Expect to read the code and adapt it to your workflow. The
`projects/sample/` project and `DESIGN.md` give you enough to orient, but you are
starting a fork, not installing a package.

## Getting started

### Requirements

- QGIS 3.x desktop app (Mac: `/Applications/QGIS.app`; configure path in
  `local.env`)
- [uv](https://docs.astral.sh/uv/)
- GDAL CLI tools (`brew install gdal`) — used for data preparation; QGIS.app
  bundles its own GDAL but does not expose the command-line tools

### Install

```bash
git clone <repo>
cd alidade
uv sync
cp local.env.example local.env   # edit if QGIS is not at the default path
```

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

### Print layout

Add a `print_layout` field to `project.py`:

```python
spec = Project(
    ...
    print_layout=PrintLayout(
        title_text="My Map Title",
        credits_text="© OpenStreetMap contributors\nData: My Source",
    ),
)
```

`make build` writes `output/print.qpt` alongside `output/project.qgs`. Page size,
positions, scale bar units, and north arrow SVG are all overrideable fields on the
sub-models (`PrintPage`, `PrintScaleBar`, etc.).

To export a PDF, open the Python console in QGIS (**Plugins → Python Console**) and run:

```python
exec(open("/path/to/alidade/alidade/util/export_pdf.py").read())
```

The script loads the QPT template automatically if it is not already in the Layout
Manager, then writes `output/print.pdf`.

See `DESIGN.md` for architecture decisions and `projects/sample/workflow.md` for an
example of the LLM prompt log.
