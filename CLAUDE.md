Do not pass code as string on the command line — this includes `python -c "..."` and
any shell one-liner that embeds Python.  When writing Python code to explore or test
something, append it as a function to claude.py and run `uv run python claude.py`.
Include a comment about the purpose of the code.

When writing Python code

  - Always use PEP-8 style.
  - Do not use inline imports.
  - Always run `make lint` after editing code, not black on individual files.
  - Always break string literals that exceed 88 characters using implicit string
    concatenation, since black does not split string literals.

After adding, removing, or restyling a layer (any edit to a `layers/*.py`
file inside a map directory), update that map's `workflow.md` in the
same session. Do not wait for the user to ask.

The build system uses make for dependency tracking. `make build DIR=<dir>` generates
`output/GEN.mk` from the layer graph and invokes make against it. Each layer output
is a make target.
Do not add manual `black` or formatting calls to build-related code; run `make lint`.
Use `uv run alidade-makefile <dir>` to inspect the generated Makefile, and
`uv run alidade-build-layer <dir> <layer_id>` to build exactly one layer.

When writing scratch exploration code in `claude.py`, import helpers from
`alidade.util.claude_toolbox` instead of writing new implementations. Available
helpers:

- `inspect_shapefile(path, sample_rows=0)` — CRS, count, geometry types, column
  samples; use instead of one-off `inspect_*` functions
- `find_qgs_layer(path, *, layer_id, datasource_contains, datasource_excludes,
  layername)` — find a `<maplayer>` element in a QGS file by any combination of
  criteria; use instead of one-off `find_*` helpers
- `flatten_xml(el, prefix="")` — flatten an XML subtree to `{xpath: value}` for
  diffing; never copy-paste this implementation again
- `dump_qgs_layer(path, *, layer_id, datasource_contains, datasource_excludes,
  layername, subtree, max_chars)` — pretty-print a maplayer (or subtree like
  `"renderer-v2"`) from a QGS file
- `diff_qgs_layers(path_a, path_b, *, layer_id, datasource_contains,
  datasource_excludes, layername, subtree)` — diff two QGS files and print
  changed paths; use instead of one-off `compare_*` / `diff_*` functions
- `compute_jenks_breaks(shapefile_path, field, k=5, filter_fn=None)` — Jenks
  natural breaks on any shapefile field
- `compute_layer_extent(shapefile_path, pad_pct=0.05)` — padded bounding box
- `audit_map_crs(map_dir)` — CRS consistency across shapefiles,
  transform context, and layer declarations in project.qgs

## Project layout

A project lives under `projects/<name>/` with this structure:

```
projects/<name>/
  __init__.py        — from .main import maps, spec; __all__ = ["maps", "spec"]
  main.py            — Map declarations; maps = [...]; spec = <default>
  palette.py         — all Color constants for the project
  util.py            — CRS string, buffer distances, shared clip helpers
  layers/
    __init__.py      — empty
    <layer>.py       — one layer per file; variable name matches filename
  data/              — raw input files (geojson, gpkg, tif, ...)
  output/            — generated outputs (gitignored)
  workflow.md        — LLM session log
```

## Layer file conventions

Structure a layer file in this order:

1. **Module docstring** — what the layer is, why it exists, data source. For raw
   data downloaded from an external service (Overpass Turbo, USGS, etc.), include
   the query or download URL in the docstring. The docstring goes at the very top
   of the file, before imports.
2. **Imports** — from `alidade.models`, `projects.<name>.palette`, and
   `projects.<name>.util`. Never construct a `Color` directly in a layer file;
   always import named constants from `palette.py`.
3. **Constants** — layer-specific constants (classification thresholds, GDAL
   expressions) before the build function.
4. **Build function** (derived layers only) — `def build_<name>(layer: BoundLayer)`.
   Raw source layers that require no processing have no build function.
5. **Layer definition** — `<name> = Layer(...)`. The variable name must match the
   filename (e.g., `roads_trails` in `roads_trails.py`).

For raw source layers, set `source_description` and `source_origin` on the `Layer`.
For derived layers, set `inputs` to the list of upstream layer variables.

## `palette.py` conventions

All `Color` objects for a project live in `palette.py` as module-level constants.
Name by role (`ROADS_LINE`, `WATER_FILL`), not by color value, so names stay
meaningful if the palette changes. No layer file should call `Color(...)` or
`Color.from_hex(...)` directly.

## `util.py` conventions

Place in `util.py`:

- Project CRS as a string constant (`CRS = "EPSG:26910"`)
- Buffer/distance constants with units in the name (`BUFFER_100FT_M = 30.48`)
- Shared spatial helpers used by more than one layer (`clip_border`, `clip_park`)
- Shared typed dataclasses used across layers (e.g., `VegetationZone`)

## `main.py` conventions

Declare each named map as a module-level variable. Place a string literal
immediately above each `Map(...)` call to describe its purpose:

```python
"""
3: Vegetation classification; lifeform classes grouped into 6 categories
"""
map_veg = Map(id="vegetation", title="...", crs=CRS, extent=EXTENT, layers=[...])
```

At the bottom, collect named maps and assign the default build target:

```python
maps = [map_park, map_slope, map_veg, ...]
spec = map_all
```

## When adding an `SvgMarker` to a layer

1. **Use a solid fill color — never transparent.**  Most QGIS built-in SVGs
   (tourist, amenity, etc.) are solid-fill silhouette paths with no separate
   stroke geometry.  Setting `color="0,0,0,0"` makes the icon completely
   invisible.  Use a solid color, e.g. `color="0,0,0,255"` for black.

2. **Use built-in QGIS SVGs by relative path** — e.g.
   `name="tourist/tourist_zoo.svg"`.  QGIS resolves these against its internal
   SVG library (`<QGIS.app>/Contents/Resources/qgis/svg/` on macOS).  Do not
   hard-code the absolute system path.

3. **Verify the SVG exists** before referencing it:
   `find /Applications/QGIS.app -name "<name>.svg" 2>/dev/null`

4. **Inspect the SVG source** to understand its parameterisation before
   choosing colors.  A path with only `param(fill)` needs a solid `color`;
   one with both `param(fill)` and `param(outline)` supports fill + stroke.
   Run `cat /Applications/QGIS.app/Contents/Resources/qgis/svg/<path>` and
   look for `param(fill)` vs `param(outline)` usage.

5. **When a marker is invisible, diff against a QGIS-saved file** using
   `diff_qgs_layers(generated, qgis_saved, layer_id=..., subtree="renderer-v2")`
   to see exactly what QGIS changed.  If QGIS stripped the `renderer-v2`
   entirely on save, it rejected the renderer — check the SVG path and color.
