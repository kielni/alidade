"""Generate or update a map's README.md from the current map spec.

Called by build.py after render(). Replaces the section between the
<!-- auto:begin --> / <!-- auto:end --> markers; everything outside is preserved.
"""

from graphlib import TopologicalSorter
from pathlib import Path

from alidade.models import (
    BoundMap,
    Layer,
    PythonAction,
)

BEGIN = "<!-- auto:begin -->"
END = "<!-- auto:end -->"

# Ordered list of (substring, label) pairs for _source_label. Checked in order;
# first match wins. "wms" is matched case-insensitively via .lower().
SOURCE_LABELS: list[tuple[str, str]] = [
    ("dark_all", "CartoDB Dark Matter XYZ tile service"),
    ("cartocdn", "CartoDB Positron XYZ tile service"),
    ("openstreetmap.org", "OpenStreetMap tile service"),
    ("<GDAL_WMS>", "OpenStreetMap tile service"),
    ("http-header", "WMS/XYZ tile service"),
    ("wms", "WMS/XYZ tile service"),
]


def _source_label(source: str) -> str:
    """Return a short human-readable label for a layer source path or URI."""
    source_lower = source.lower()
    for substring, label in SOURCE_LABELS:
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


def _data_source_rows(
    layer: Layer,
) -> list[tuple[str, str, str, str]]:
    """Return (dedup_key, file_label, description, origin) for a layer's raw inputs."""
    rows = []
    if layer.provider == "wms":
        label = _source_label(layer.datasource)
        desc = layer.source_description or layer.name
        origin = layer.source_origin or "XYZ / WMS tile service"
        rows.append((label, label, desc, origin))
    elif layer.raw_file:
        desc = layer.source_description or layer.name
        origin = layer.source_origin or ""
        rows.append((layer.raw_file, layer.raw_file, desc, origin))
    elif layer.action is None:
        src = _source_label(layer.datasource)
        if src.startswith("data/"):
            desc = layer.source_description or layer.name
            origin = layer.source_origin or ""
            rows.append((src, src, desc, origin))
    return rows


def _step_description(layer: Layer) -> str:
    """Return a one-line description of a processing step from the action docstring."""
    if isinstance(layer.action, PythonAction):
        doc = getattr(layer.action.fn, "__doc__", None)
        if doc:
            return doc.strip().split("\n")[0].strip().rstrip(".")
    return ""


def _topo_sort(derived: list[Layer]) -> list[Layer]:
    """Return derived layers in topological order (inputs before their dependents)."""
    id_to_layer = {la.id: la for la in derived}
    ts = TopologicalSorter({la.id: [inp.id for inp in la.inputs] for la in derived})
    return [id_to_layer[i] for i in ts.static_order() if i in id_to_layer]


def _auto_section(spec: BoundMap) -> str:
    """Build the auto-generated README section text for spec."""
    lines: list[str] = []

    # ── Data Sources ──────────────────────────────────────────────────────────
    lines.append("## Data Sources")
    lines.append("")
    lines.append("| File | Description | Origin |")
    lines.append("|---|---|---|")
    seen: set[str] = set()
    for layer in spec.layers:
        for key, file_label, desc, origin in _data_source_rows(layer):
            if key not in seen:
                seen.add(key)
                lines.append(f"| `{file_label}` | {desc} | {origin} |")
    lines.append("")

    # ── Processing Steps ──────────────────────────────────────────────────────
    derived = [la for la in spec.layers if la.action is not None]
    if derived:
        ordered = _topo_sort(derived)
        lines.append("## Processing Steps")
        lines.append("")
        for i, layer in enumerate(ordered, 1):
            desc = _step_description(layer)
            if desc:
                lines.append(f"{i}. **{layer.name}** — {desc}")
            else:
                lines.append(f"{i}. **{layer.name}**")
        lines.append("")

    # ── Data Flow ─────────────────────────────────────────────────────────────
    if derived:
        lines.append("## Data Flow")
        lines.append("")
        lines.append("```mermaid")
        lines.append("flowchart LR")
        for layer in derived:
            for inp in layer.inputs:
                lines.append(f"    {inp.id} --> {layer.id}")
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


def update_readme(spec: BoundMap) -> None:
    """Write or update the auto-generated section of README.md."""
    assert spec.map_path is not None
    readme_path = spec.map_path / "README.md"
    section = f"{BEGIN}\n{_auto_section(spec)}{END}\n"

    if not readme_path.exists():
        readme_path.write_text(f"# {spec.title}\n\n{section}")
        print(f"Wrote {readme_path}")
        return

    existing = readme_path.read_text()

    if BEGIN in existing and END in existing:
        before = existing[: existing.index(BEGIN)]
        after = existing[existing.index(END) + len(END) :].lstrip("\n")
        updated = before + section + ("\n" + after if after else "")
    else:
        updated = existing.rstrip("\n") + "\n\n" + section

    if updated != existing:
        readme_path.write_text(updated)
        print(f"Updated {readme_path}")
