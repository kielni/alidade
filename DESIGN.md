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
- Reproducibility — a fresh checkout rebuilds the project exactly
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
    models.py              # Pydantic: BaseProject/QGISProject/ArcGISProject,
                           #   Layer, ProcessingStep, renderers, symbols
    dump.py                # .qgz → layers/*.py + styles/*.xml  (QGIS only)
    render.py              # project.py → output/project.qgs   (QGIS)
    render_arcgispro.py    # project.py → output/project.aprx  (ArcGIS Pro)
    build.py               # entry point; dispatches on output_format
    readme.py              # auto-generates README from spec
  Makefile
  local.env                # machine-local config (gitignored)
  local.env.example        # template

  projects/                # one subdirectory per project
    <project_dir>/
      project.py           # assembles QGISProject or ArcGISProject from layers
      layers/              # one .py file per layer, named by layer ID
      styles/              # per-layer XML extracted from .qgz, committed
      output/              # gitignored; derived data and project files
```

### Dispatch

`build.py` reads `project.py` to determine the output format:

- `QGISProject` → `render.py` → `output/project.qgs` + optional `output/print.qpt`
- `ArcGISProject` → `render_arcgispro.py` → `output/project.aprx`

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
    source: str                       # path or URI
    provider: str = "ogr"             # "ogr", "gdal", "wms"
    style_xml: Path | None = None     # QGIS-only
    crs: str | None = None
    geometry_type: str | None = None  # "Polygon", "LineString", "Point"
    alpha_band: int | None = None     # QGIS raster alpha band
    arcgispro_workspace: str | None = None  # explicit ArcGIS Pro WorkspaceConnectionString
    visible: bool = True
    renderer: Renderer | None = None
    label: Label | None = None
    processing_step: ProcessingStep | None = None
    extra: dict[str, Any] = {}

class BaseProject(BaseModel):
    model_config = ConfigDict(extra="allow")
    output_format: str   # overridden as Literal by subclasses
    title: str
    crs: str
    layers: list[Layer]
    extent: tuple[float, float, float, float] | None = None
    extra: dict[str, Any] = {}

class QGISProject(BaseProject):
    output_format: Literal["qgis"] = "qgis"
    print_layout: PrintLayout | None = None

class ArcGISProject(BaseProject):
    output_format: Literal["arcgispro"] = "arcgispro"
```

**`project.py` pattern** — import `QGISProject as Project` or `ArcGISProject`:

```python
from alidade.models import QGISProject as Project   # QGIS
# or
from alidade.models import ArcGISProject            # ArcGIS Pro
```

## Layer IDs and filenames

Layer IDs are human-friendly strings: `"slope"`, `"elevation_10n"`, `"park_polygon"`.
Not QGIS-generated UUIDs. The ID is the stable handle used as the filename
(`layers/slope.py`) and in `depends_on` declarations.

QGIS silently drops layers whose `<id>` is ≤10 characters. The `Layer` validator
auto-pads short IDs to `{id}_{uuid[:8]}` and emits a warning.

## QGIS output

No PyQGIS — generate XML directly. `render.py` builds a `.qgs` XML tree from the
`QGISProject` spec and writes `output/project.qgs`. Style is embedded from
`styles/*.xml` or rendered from typed `Renderer` models.

Supported renderers in QGIS path:
`SingleSymbol`, `RuleRenderer`, `GraduatedRenderer`, `PalettedRenderer` (raster).
Symbol layers: `SimpleFill`, `SimpleLine`, `SimpleMarker`, `SvgMarker`.

## ArcGIS Pro output

`render_arcgispro.py` writes `output/project.aprx` — a ZIP archive of CIM
(Cartographic Information Model) documents. Target version: **CIM v3.4.0**
(ArcGIS Pro 3.4, build 55405).

### CIM format

In Pro 3.x, all CIM documents except `DocumentInfo.xml` and `Metadata/*.xml`
are **JSON**, even when the filename ends in `.xml`. The type discriminator is
a `"type"` field, not `xsi:type`. Keys are camelCase.

Primary CIM reference: **https://github.com/Esri/cim-spec**
(use the `docs/v3/` tree; the repo is currently at v3.7 — check git history/tags
for the v3.4 snapshot). The .NET SDK CIM namespace docs have better descriptions
for terse spec pages.

### ZIP layout

```
DocumentInfo.xml             ← XML; version 3.4.0, build 55405
GISProject.json              ← JSON; CIMGISProject with views array
Index.json                   ← JSON; node graph of all documents
map/map.xml                  ← JSON; CIMMap
map/Ground.json              ← JSON; CIMElevationSurfaceLayer (required in 3.x)
map/<layer_id>.xml           ← JSON; CIMFeatureLayer per operational layer
<uuid>.xml                   ← JSON; CIMTiledServiceLayer (wms/tile provider)
Metadata/<uuid>.xml          ← XML; stub metadata
```

`007Index.ind` (Esri positional object-store index) is regenerated by ArcGIS Pro
on first save; we do not include it.

### Spatial reference

v2.x used WKT strings. v3.x uses WKID-based dicts:

```json
{"wkid": 102100, "latestWkid": 3857}
```

`_sr_dict(crs_str)` resolves via pyproj `to_epsg()`. The Esri legacy wkid
differs from the EPSG latestWkid only for Web Mercator (3857 → 102100) and a
handful of others; `_ESRI_WKID_ALIASES` holds the mapping.

### Colors

```json
{"type": "CIMRGBColor", "values": [R, G, B, A]}
```

Alpha is 0–100 (percent), not 0–255. `_rgb_color("R,G,B,A")` converts.

### Data connections

`_cim_source(layer, project_dir)` returns `(WorkspaceConnectionString, WorkspaceFactory, Dataset)`:

| `layer.source` | WorkspaceFactory | WorkspaceConnectionString |
|---|---|---|
| ends with `.shp` | `Shapefile` | `DATABASE=.\<rel-dir>` |
| inside `.gdb/` | `FileGDB` | `DATABASE=.\<name>.gdb` |
| `arcgispro_workspace` set | use that string verbatim | that string |
| `provider == "wms"` | — | → `CIMTiledServiceLayer` |
| anything else | warn + skip | — |

### Supported renderers (ArcGIS Pro path)

| alidade model | CIM type | Status |
|---|---|---|
| `SingleSymbol` + `SimpleFill` | `CIMSimpleRenderer` → `CIMPolygonSymbol` | ✓ |
| `SingleSymbol` + `SimpleLine` | `CIMSimpleRenderer` → `CIMLineSymbol` | ✓ |
| `SingleSymbol` + `SimpleMarker` | `CIMSimpleRenderer` → `CIMPointSymbol` | deferred |
| `GraduatedRenderer` | `CIMClassBreaksRenderer` | deferred |
| `RuleRenderer` | `CIMUniqueValueRenderer` | deferred |
| `PalettedRenderer` | `CIMRasterColorizer` | deferred |

Layers with a deferred renderer type get no `"renderer"` key; ArcGIS Pro
assigns a default. The CIM spec (`docs/v3/CIMRenderers.md`) documents all types.

### Ground elevation surface

Every CIM v3.x map requires a `CIMElevationSurfaceLayer` at `map/Ground.json`.
Feature layers reference it via:

```json
"layerElevation": {
  "type": "CIMLayerElevationSurface",
  "elevationSurfaceLayerURI": "CIMPATH=map/Ground.json"
}
```

### Index.json

Lists every document in the archive as a node with `NodeId`, `NodeType`,
`FileName`, `ChildNodeIds`. The Map node's `ChildNodeIds` lists metadata,
all feature layers (which each reference Ground), and tile layers. `GISProject.json`
and `DocumentInfo.xml` are not in the Index.

## Makefile targets

| Target | What it does |
|---|---|
| `make build DIR=...` | Builds `.qgs` or `.aprx` depending on project type |
| `make build-arcgispro DIR=...` | Alias for `make build` for clarity |
| `make build-all` | Builds all projects under `projects/` |
| `make dump DIR=...` | Extracts layers from a `.qgz` (QGIS only) |
| `make lint` | black + flake8 + mypy |
| `make extent DIR=...` | Prints bounding box of project data |

## One layer per file

Each layer lives in `layers/{layer_id}.py` and exports a single variable with
the same name as the file. `project.py` only imports layers and assembles the spec.

## Processing steps

Derived layers are produced by `ProcessingStep` — shell commands (GDAL/GRASS) or
Python functions. `build.py` runs them in topological order, skipping steps
whose output already exists (pass `--force` to re-run all).

```python
class ProcessingStep(BaseModel):
    description: str          # plain-English sentence
    action: ShellAction | PythonAction
    depends_on: list[str]     # layer IDs that are step inputs
    output: Path              # e.g. Path("output/slope.tif")
```

Prefer `PythonAction` (geopandas) over `ShellAction` for vector operations;
reserve `ShellAction` for raster tools like `gdaldem slope` or `gdalwarp`.

## LLM workflow documentation

Each project directory contains `workflow.md` recording prompts, what each did,
non-obvious choices, and data source URLs. Update in the same session as the
work — not retroactively.

## File ownership

| File | Written by | Human edits? |
|---|---|---|
| `layers/*.py` | dump (once, bootstrap) | yes — source of truth |
| `styles/*.xml` | dump / QGIS Save Style | no — treat as opaque |
| `project.py` | human | yes |
| `workflow.md` | LLM + human | yes |
| `output/` | build | no — gitignored |

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

## Deferred

Add when concrete need arises, not before:

- `CIMSimpleMarker` / `CIMPointSymbol` for ArcGIS Pro point layers
- `CIMClassBreaksRenderer` for graduated rendering in ArcGIS Pro
- Label support (`CIMLabelClass`) in ArcGIS Pro
- Raster layer support in ArcGIS Pro
- Symbol library integration (NPS symbols, etc.)
- DVC for large derived rasters
- File watcher that triggers QGIS Ctrl-R automatically
