# Generate or update a project's README.md from the current project spec.
# Called by build.py after render(). Replaces the section between the
# <!-- auto:begin --> / <!-- auto:end --> markers; everything outside is preserved.

from pathlib import Path

from alidade.models import (
    BoundProject,
    GraduatedRenderer,
    Layer,
    PalettedRenderer,
    Renderer,
    RuleRenderer,
    SimpleFill,
    SimpleLine,
    SimpleMarker,
    SingleSymbol,
    SvgMarker,
    SymbolLayer,
)

_BEGIN = "<!-- auto:begin -->"
_END = "<!-- auto:end -->"

# Ordered list of (substring, label) pairs for _source_label. Checked in order;
# first match wins. "wms" is matched case-insensitively via .lower().
_SOURCE_LABELS: list[tuple[str, str]] = [
    ("dark_all", "CartoDB Dark Matter XYZ tile service"),
    ("cartocdn", "CartoDB Positron XYZ tile service"),
    ("openstreetmap.org", "OpenStreetMap tile service"),
    ("<GDAL_WMS>", "OpenStreetMap tile service"),
    ("http-header", "WMS/XYZ tile service"),
    ("wms", "WMS/XYZ tile service"),
]


def _color(rgba: str) -> tuple[str, int]:
    """Return (hex_color, alpha_percent) from a comma-separated 'r,g,b,a' string."""
    parts = rgba.split(",")
    r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
    a = int(parts[3]) if len(parts) > 3 else 255
    return f"#{r:02x}{g:02x}{b:02x}", round(a / 255 * 100)


def _source_label(source: str) -> str:
    """Return a short human-readable label for a layer source path or URI."""
    source_lower = source.lower()
    for substring, label in _SOURCE_LABELS:
        if substring in source or substring in source_lower:
            return label
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


def _describe_symbol_layer(sl: SymbolLayer) -> str:
    """Return a one-line prose description of a SymbolLayer for the README."""
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


def _describe_renderer(renderer: Renderer) -> str:
    """Return a one-line prose description of a Renderer for the README."""
    if isinstance(renderer, SingleSymbol):
        parts = [_describe_symbol_layer(sl) for sl in renderer.symbol.layers]
        return "single symbol — " + "; ".join(parts)
    if isinstance(renderer, RuleRenderer):
        return f"rule-based ({len(renderer.rules)} rules)"
    if isinstance(renderer, PalettedRenderer):
        return f"paletted raster ({len(renderer.entries)} classes)"
    if isinstance(renderer, GraduatedRenderer):
        return f"graduated ({len(renderer.ranges)} classes on `{renderer.attr}`)"
    return type(renderer).__name__


def _describe_style(layer: Layer) -> str:
    """Return a one-line style description for a layer."""
    if layer.renderer is not None:
        return _describe_renderer(layer.renderer)
    if layer.style_xml is not None:
        return f"see `{layer.style_xml}`"
    return "no style configured"


def _auto_section(spec: BoundProject) -> str:
    """Build the auto-generated README section text for spec."""
    lines: list[str] = []

    lines.append("## Layers")
    lines.append("")
    for layer in spec.layers:
        lines.append(f"### {layer.name}")
        lines.append("")
        source = _source_label(layer.datasource)
        lines.append(f"**Source:** `{source}`  ")
        lines.append(f"**Style:** {_describe_style(layer)}  ")
        if layer.action is not None and layer.inputs:
            deps = ", ".join(f"`{inp.id}`" for inp in layer.inputs)
            lines.append(f"**Derived from:** {deps}  ")
        lines.append("")

    derived = [la for la in spec.layers if la.action is not None]
    if derived:
        lines.append("## Data flow")
        lines.append("")
        lines.append("```mermaid")
        lines.append("flowchart LR")
        for layer in derived:
            for inp in layer.inputs:
                lines.append(f"    {inp.id} --> {layer.id}")
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


def update_readme(spec: BoundProject) -> None:
    """Write or update the auto-generated section of README.md."""
    assert spec.project_path is not None
    readme_path = spec.project_path / "README.md"
    section = f"{_BEGIN}\n{_auto_section(spec)}{_END}\n"

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
