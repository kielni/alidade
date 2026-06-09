# DESIGN.md

Handoff document for working on this repo with Claude Code. Captures
architecture decisions. Read this before writing any code.

## Goal

Treat GIS projects as build output, not source. Source of truth is Python in
this repo. A build script renders either a `.qgs` file (QGIS) or a `.aprx` file
(ArcGIS Pro) from the same Python spec. The GIS application is used as a viewer;
edits happen in code.

Data processing steps (reprojection, slope calculation, reclassification, etc.)
are captured in code alongside the layers they produce. Each transform records
its inputs and the command to run, so the full pipeline is reproducible from a
fresh checkout.

## Why

Coming from software engineering, the user wants:

- Minimal repetitive clicking through GIS menus
- Batch edits via text files
- Incremental commits with metadata and meaningful diffs
- Reproducibility - a fresh checkout rebuilds the project exactly
- Browse/edit configuration with Python in an IDE
- No hand-editing XML; no committing compressed binaries

## Non-goals (for now)

- Writing QGIS or ArcGIS plugins
- Reinventing the PyQGIS or arcpy APIs
- Modeling the entire QGIS or ArcGIS project schema upfront
- Building a generic framework before getting hands-on experience

Generalize after friction, not before.

## Architecture

```
alidade/
  alidade/
    models.py              # Pydantic: Project, Layer, renderers, symbols
    dump_qgis.py           # .qgz → layers/*.py + styles/*.xml  (QGIS only)
    render_qgis.py         # project.py → output/project.qgs   (QGIS)
    render_lyrx.py         # project.py → output/{layer.id}.lyrx  (ArcGIS Pro)
    render_map.py          # project.py → output/map_<id>.png for each map in maps list
    lyrx/                  # CIM builder subpackage (data_connection, symbols, renderers, build)
    build.py               # entry point; dispatches on output_format
    publish_arcgis.py      # publish layers + web maps to ArcGIS Online
    readme.py              # auto-generates README from spec
  Makefile
  local.env                # machine-local config (gitignored)
  local.env.example        # template

  projects/                # one subdirectory per project
    <project_dir>/
      project.py           # assembles Project (output_format="qgis" or "lyrx")
      layers/              # one .py file per layer, named by layer ID
      styles/              # per-layer XML extracted from .qgz, committed (QGIS only)
      output/              # gitignored; derived data and project files
```

### Dispatch

`build.py` reads `project.py` to determine the output format via `spec.output_format`:

- `"qgis"` → `render_qgis.py` → `output/project.qgs` + optional `output/print.qpt`
- `"lyrx"` → `render_lyrx.py` → `output/{layer.id}.lyrx` (one file per layer)

Both share `_run_processing_steps` (format-agnostic).

### Key choices

**Pydantic models, hybrid typing.** Typed fields for things we touch; `extra="allow"`
for everything else. Expand the typed surface as we hit specific needs.

**`.qgs` not `.qgz`.** Uncompressed XML output, gitignored. Compressed projects
defeat diffing.

**Derived data is gitignored, regenerated from recorded transforms.** Each
`Layer` with a `ProcessingStep` records the shell command and its inputs.

## Models

```python
class Layer(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str                           # human-friendly, e.g. "slope"
    name: str                         # display name
    type: Literal["vector", "raster"]
    datasource: str                   # relative path, e.g. "data/boundary.geojson"
    provider: str = "ogr"             # "ogr" (default), "gdal", "wms"
    style_xml: Path | None = None     # QGIS-only
    crs: str | None = None
    geometry_type: str | None = None  # "Polygon", "LineString", "Point"
    alpha_band: int | None = None     # QGIS raster alpha band
    visible: bool = True
    renderer: Renderer | None = None
    label: Label | None = None
    inputs: list[Layer] = []          # layers this one depends on
    action: ShellAction | PythonAction | None = None
    raw_file: str | None = None       # path to unprocessed source data
    source_description: str | None = None
    source_origin: str | None = None
    extra: dict[str, Any] = {}

class Project(BaseModel):
    model_config = ConfigDict(extra="allow")
    output_format: Literal["qgis", "lyrx"] = "qgis"
    title: str
    crs: str
    layers: list[Layer]
    extent: tuple[float, float, float, float] | None = None
    print_layout: PrintLayout | None = None  # QGIS only
    extra: dict[str, Any] = {}
```

When constructing a `Layer`, omit fields that use the default value. Common defaults
to leave out: `provider="ogr"`, `visible=True`. Only pass fields that differ from
the model default.

**`project.py` pattern** - import `Project` and set `output_format`:

```python
from alidade.models import Project

spec = Project(output_format="qgis", title="My Map", crs="EPSG:3857", layers=[...])
# or
spec = Project(output_format="lyrx", title="My Map", crs="EPSG:3857", layers=[...])
```

## Layer IDs and filenames

Layer IDs are human-friendly strings: `"slope"`, `"elevation_10n"`, `"park_polygon"`.
Not QGIS-generated UUIDs. The ID is the stable handle used as the filename
(`layers/slope.py`) and referenced when a layer imports another as an input.

QGIS silently drops layers whose `<id>` is ≤10 characters. The `Layer` validator
auto-pads short IDs to `{id}_{uuid[:8]}` and emits a warning.

## QGIS output

No PyQGIS - generate XML directly. `render_qgis.py` builds a `.qgs` XML tree from the
`QGISProject` spec and writes `output/project.qgs`. Style is embedded from
`styles/*.xml` or rendered from typed `Renderer` models.

Supported renderers in QGIS path:
`SingleSymbol`, `RuleRenderer`, `GraduatedRenderer`, `PalettedRenderer` (raster).
Symbol layers: `SimpleFill`, `SimpleLine`, `SimpleMarker`, `SvgMarker`.

## ArcGIS Pro output

`render_lyrx.py` writes one `output/{layer.id}.lyrx` per layer - a standalone
JSON file using the CIM (Cartographic Information Model) v3.4.0 format.
Each `.lyrx` can be dragged directly into ArcGIS Pro without building a full
project archive.

### CIM format

CIM documents are **JSON** with a `"type"` discriminator field and camelCase keys.

Primary CIM reference: **https://github.com/Esri/cim-spec**
(use the `docs/v3/` tree). The .NET SDK CIM namespace docs have better
descriptions than the terse spec markdown pages.

### .lyrx structure

A `.lyrx` file is a flat `CIMLayerDocument` JSON object:

```json
{
  "type": "CIMLayerDocument",
  "version": "3.4.0",
  "build": 55405,
  "layers": ["CIMPATH=layers/<layer_id>.json"],
  "layerDefinitions": [{ "type": "CIMFeatureLayer", "uRI": "CIMPATH=layers/<layer_id>.json", ... }]
}
```

The `layers[0]` CIMPATH must exactly match `layerDefinitions[0].uRI`.

### Colors

```json
{"type": "CIMRGBColor", "values": [R, G, B, A]}
```

Alpha is 0-100 (percent), not 0-255. `_rgb_color("R,G,B,A")` converts.

### Data connections

`build_data_connection(layer, project_dir)` derives workspace and dataset from
`layer.source` (uses the shapefile stem, not `layer.id`):

```json
{
  "type": "CIMStandardDataConnection",
  "workspaceConnectionString": "DATABASE=<absolute folder path>",
  "workspaceFactory": "Shapefile",
  "dataset": "<stem>",
  "datasetType": "esriDTFeatureClass"
}
```

Standalone `.lyrx` files require absolute paths. Set `ARCGIS_WORKSPACE_ROOT`
in `local.env` (gitignored) to remap local paths to the ArcGIS machine path.
The project directory name is appended automatically so the value is machine-level
only - no per-project secrets committed.

### Supported renderers (lyrx path)

| alidade model | CIM type | Status |
|---|---|---|
| `SingleSymbol` + `SimpleFill` | `CIMSimpleRenderer` → `CIMPolygonSymbol` | ✓ |
| `SingleSymbol` + `SimpleLine` | `CIMSimpleRenderer` → `CIMLineSymbol` | ✓ |
| `GraduatedRenderer` | `CIMClassBreaksRenderer` (GraduatedColor) | ✓ |
| `SingleSymbol` + `SimpleMarker` | `CIMSimpleRenderer` → `CIMPointSymbol` | deferred |
| `RuleRenderer` | `CIMUniqueValueRenderer` | deferred |
| `PalettedRenderer` | `CIMRasterColorizer` | deferred |

Layers with a deferred renderer type get no `"renderer"` key; ArcGIS Pro
assigns a default. The CIM spec (`docs/v3/CIMRenderers.md`) documents all types.

### Symbol layer order

In `CIMPolygonSymbol.symbolLayers`: `CIMSolidStroke` first (index 0),
`CIMSolidFill` second. This is the opposite of QGIS QML layer order.
`CIMSolidStroke` requires 3D fields: `anchor3D`, `height3D`, `lineStyle3D`.

## Makefile targets

| Target | What it does |
|---|---|
| `make build DIR=...` | Builds `.qgs` or `.lyrx` files depending on project type |
| `make build-all DIR=...` | Force rebuild even if up to date |
| `make dump DIR=...` | Extracts layers from a `.qgz` (QGIS only) |
| `make lint` | black + flake8 + mypy |
| `make extent DIR=...` | Prints bounding box of project data |

## One layer per file

Each layer lives in `layers/{layer_id}.py` and exports a single variable with
the same name as the file. `project.py` only imports layers and assembles the spec.

## Processing steps

Derived layers are produced by running a Python function or a shell command (GDAL/GRASS). `build.py` runs them in topological order, skipping steps
whose output already exists (pass `--force` to re-run all).

Prefer Python (geopandas) over shell for vector operations;
reserve shell commands for raster tools like `gdaldem slope` or `gdalwarp`.

## Coding conventions

**Output file format.** Prefer `.gpkg` over `.shp` for derived vector output.
Keep existing `.geojson` files as-is; do not convert them to another format.
Raster output uses `.tif`.
Example: `datasource="output/vegetation.gpkg"` not `"output/vegetation.shp"`.

**Omit default params.** When constructing a `Layer`, leave out fields that
match the model default: `provider="ogr"` and `visible=True` are the most
common. Only pass fields that differ from the default.

**Constants naming.** Use `UPPER_CASE` for module-level constants. Do not use
a leading underscore prefix. Example: `RANK_TIERS`, `WEIGHT_SLOPE`,
`RIPARIAN_BUFFER_M`.

**Tunable parameters as constants.** Define buffer distances, weights,
thresholds, and other tunable values as named constants at the top of the
layer file, not as literal values embedded in function bodies. Reviewers and
future sessions can then adjust parameters without hunting through code.

```python
RIPARIAN_BUFFER_M = 30.0
DEVELOPED_BUFFER_M = 100.0
WEIGHT_SLOPE = 0.25
```

**Avoid abbreviations.** Write full names in variables: `boundary_layer`,
`slope_layer`, `vegetation_layer` - not `bnd`, `slp`, `veg`, `lyr`, `pts`.
The `_layer` suffix makes the role of each variable obvious in `build_*`
functions that unpack `layer.inputs`.

**Checking package versions.** Use `pyproject.toml` as the source of truth
for which packages are installed and at what versions. Do not write one-off
`pip show` checks or inline `import pkg; pkg.__version__` lookups.

## LLM workflow documentation

Each project directory contains `workflow.md`. Its purpose is to let another
person reconstruct the project from scratch by following the recorded steps in
order.

Each entry covers one logical unit of work: what was done, the key parameters
and values (URLs, thresholds, CRS codes, algorithm choices), and which files
were created or changed. Two or three sentences is typical; more when the
change involves a non-obvious decision or a discovered constraint.

Format:

```markdown
## Step N - Brief title

What was done and the specific values that matter: URLs, distances,
field names, color codes, algorithm choices, tradeoffs.

**Files created/changed:**
- `path/to/file.py` - one-line summary of the change
```

Update in the same session as the work - not retroactively.

## File ownership

| File | Written by | Human edits? |
|---|---|---|
| `layers/*.py` | dump (once, bootstrap) | yes - source of truth |
| `styles/*.xml` | dump / QGIS Save Style | no - treat as opaque |
| `project.py` | human | yes |
| `workflow.md` | LLM + human | yes |
| `output/` | build | no - gitignored |

## External references

| Resource | URL | Notes |
|---|---|---|
| CIM spec | github.com/Esri/cim-spec | `docs/v3/` tree; v3.4 in git history |
| ArcGIS Pro .NET SDK CIM namespace | ArcGIS.Core.CIM docs | Better descriptions than spec markdown |
| CIM Viewer add-in | github.com/Esri/arcgis-pro-sdk-cim-viewer | Inspect live CIM in ArcGIS Pro |
| arcpy.cim module | arcpy.cim.CreateCIMObjectFromClassName | Python CIM access within Pro |
| ArcGIS REST API | developers.arcgis.com/rest/ | Geometry/feature JSON in DataConnection blocks |
| Web Map spec | developers.arcgis.com/web-map-specification/ | ArcGIS Online; cross-platform but lossy |
| File Geodatabase API | github.com/Esri/file-geodatabase-api | C++/Java read+write |
| GDAL OpenFileGDB driver | GDAL docs | Open-source .gdb read+write |
| Shapefile spec | ESRI 1998 white paper | Still authoritative |

## Update documentation

Update DESIGN.md, README.md, Makefile to reflect the new layout.

Add a section to README with a styled ArcGIS layer.

## Deferred

Add when concrete need arises, not before:

- `CIMSimpleMarker` / `CIMPointSymbol` for ArcGIS Pro point layers
- `CIMClassBreaksRenderer` for graduated rendering in ArcGIS Pro
- Label support (`CIMLabelClass`) in ArcGIS Pro
- Raster layer support in ArcGIS Pro
- Symbol library integration (NPS symbols, etc.)
- DVC for large derived rasters
- File watcher that triggers QGIS Ctrl-R automatically
