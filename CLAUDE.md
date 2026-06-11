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
file inside a project directory), update that project's `workflow.md` in the
same session. Do not wait for the user to ask.

The build system uses make for dependency tracking. `alidade-build` generates
`output/GEN.mk` from the layer graph and invokes make against it. Each layer
output is a make target; formatting (`black`) is tracked by an
`output/.formatted` stamp. Do not add manual `black` or formatting calls to
build-related code — make handles it. Use `alidade-makefile <dir>` to inspect
the generated Makefile, and `alidade-build-layer <dir> <layer_id>` to build
exactly one layer.

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
- `audit_project_crs(project_dir)` — CRS consistency across shapefiles,
  transform context, and layer declarations in project.qgs

When adding an `SvgMarker` to a layer:

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
