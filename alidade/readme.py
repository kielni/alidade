# Generate or update a project's README.md from the current project spec.
# Called by build.py after render(). Replaces the section between the
# <!-- auto:begin --> / <!-- auto:end --> markers; everything outside is preserved.

import inspect
import re
from pathlib import Path

from models import (
    Layer,
    PalettedRenderer,
    PythonAction,
    RuleRenderer,
    ShellAction,
    SimpleFill,
    SimpleLine,
    SimpleMarker,
    SingleSymbol,
    SvgMarker,
)

_BEGIN = "<!-- auto:begin -->"
_END = "<!-- auto:end -->"


def _describe_action_tool(action) -> str:
    """Return a short tool label for a processing step action."""
    if isinstance(action, ShellAction):
        return f"`{action.command.split()[0]}`"
    # PythonAction: inspect source for the library doing the heavy lifting
    src = inspect.getsource(action.fn)
    if "subprocess.run" in src or "subprocess.call" in src:
        m = re.search(r'\[\s*["\']([^"\']+)["\']', src)
        exe = m.group(1) if m else "subprocess"
        return f"`{exe}` (subprocess)"
    if "gpd." in src or "geopandas" in src:
        return "shapely via geopandas"
    return "Python"


def _color(rgba: str) -> tuple[str, int]:
    """Return (hex, alpha_pct) from a comma-separated 'r,g,b,a' string."""
    parts = rgba.split(",")
    r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
    a = int(parts[3]) if len(parts) > 3 else 255
    return f"#{r:02x}{g:02x}{b:02x}", round(a / 255 * 100)


def _source_label(source: str) -> str:
    if "cartocdn" in source:
        return "CartoDB Positron XYZ tile service"
    if "openstreetmap.org" in source or "<GDAL_WMS>" in source:
        return "OpenStreetMap tile service"
    if "http-header" in source or "wms" in source.lower():
        return "WMS/XYZ tile service"
    path_part = source.split("|")[0]
    p = Path(path_part)
    parts = p.parts
    if "data" in parts:
        idx = list(parts).index("data")
        return "data/" + "/".join(parts[idx + 1 :])
    if "output" in parts:
        idx = list(parts).index("output")
        return "output/" + "/".join(parts[idx + 1 :])
    return p.name


def _describe_symbol_layer(sl) -> str:
    if isinstance(sl, SimpleFill):
        fill_hex, fill_alpha = _color(sl.color)
        out_hex, _ = _color(sl.outline_color)
        desc = f"fill {fill_hex}"
        if fill_alpha < 100:
            desc += f" at {fill_alpha}% opacity"
        desc += f", {out_hex} outline"
        return desc
    if isinstance(sl, SimpleLine):
        hex_, _ = _color(sl.line_color)
        return f"{sl.line_style} line {hex_}, {sl.line_width} {sl.line_width_unit}"
    if isinstance(sl, SimpleMarker):
        hex_, _ = _color(sl.color)
        return f"{sl.name} marker {hex_}, {sl.size} {sl.size_unit}"
    if isinstance(sl, SvgMarker):
        return f"SVG marker {Path(sl.name).name}, {sl.size} {sl.size_unit}"
    return type(sl).__name__


def _describe_renderer(renderer) -> str:
    if isinstance(renderer, SingleSymbol):
        parts = [_describe_symbol_layer(sl) for sl in renderer.symbol.layers]
        return "single symbol — " + "; ".join(parts)
    if isinstance(renderer, RuleRenderer):
        return f"rule-based ({len(renderer.rules)} rules)"
    if isinstance(renderer, PalettedRenderer):
        return f"paletted raster ({len(renderer.entries)} classes)"
    return type(renderer).__name__


def _describe_style(layer: Layer) -> str:
    if layer.renderer is not None:
        return _describe_renderer(layer.renderer)
    if layer.style_xml is not None:
        return f"see `{layer.style_xml}`"
    return "no style configured"


def _auto_section(spec, project_dir: Path) -> str:
    lines: list[str] = []

    lines.append("## Layers")
    lines.append("")
    for layer in spec.layers:
        lines.append(f"### {layer.name}")
        lines.append("")
        source = _source_label(layer.source)
        lines.append(f"**Source:** `{source}`  ")
        lines.append(f"**Style:** {_describe_style(layer)}  ")
        if layer.processing_step is not None:
            step = layer.processing_step
            deps = ", ".join(f"`{d}`" for d in step.depends_on)
            lines.append(f"**Derived from:** {deps}  ")
            lines.append(f"**Processing:** {step.description}")
        lines.append("")

    derived = [la for la in spec.layers if la.processing_step is not None]
    if derived:
        lines.append("## Data flow")
        lines.append("")
        lines.append("```")
        for layer in derived:
            step = layer.processing_step
            for dep in step.depends_on:
                lines.append(f"{dep}  ──►  {layer.id}")
        lines.append("```")
        lines.append("")

        lines.append("## Processing tools")
        lines.append("")
        lines.append("| Layer | Tool | Description |")
        lines.append("| --- | --- | --- |")
        for layer in derived:
            step = layer.processing_step
            tool = _describe_action_tool(step.action)
            lines.append(f"| `{layer.id}` | {tool} | {step.description} |")
        lines.append("")

    return "\n".join(lines)


def update_readme(spec, project_dir: Path) -> None:
    readme_path = project_dir / "README.md"
    section = f"{_BEGIN}\n{_auto_section(spec, project_dir)}{_END}\n"

    if not readme_path.exists():
        readme_path.write_text(f"# {spec.title}\n\n{section}")
        print(f"Wrote {readme_path}")
        return

    existing = readme_path.read_text()

    if _BEGIN in existing and _END in existing:
        before = existing[: existing.index(_BEGIN)]
        after = existing[existing.index(_END) + len(_END) :].lstrip("\n")
        updated = before + section + ("\n" + after if after else "")
    else:
        updated = existing.rstrip("\n") + "\n\n" + section

    if updated != existing:
        readme_path.write_text(updated)
        print(f"Updated {readme_path}")
