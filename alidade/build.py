"""Entry point: render <project_path>/project.py → <project_path>/output/project.qgs."""

import argparse
import hashlib
import subprocess
from pathlib import Path

from alidade.models import Layer, Project
from alidade.readme import update_readme
from alidade.render_map import render as render_map
from alidade.render_qgis import render as render_qgis
from alidade.util.helpers import load_spec, resolve_source_path


def _visit(
    layer_id: str,
    steps: dict[str, Layer],
    visited: set[str],
    ordered: list[Layer],
) -> None:
    """Add layer_id and its unvisited dependencies to ordered in topological order."""
    if layer_id in visited:
        return
    visited.add(layer_id)
    layer = steps.get(layer_id)
    if layer is not None:
        assert layer.processing_step is not None
        for dep in layer.processing_step.depends_on:
            _visit(dep, steps, visited, ordered)
        ordered.append(layer)


def _topo_sort(spec: Project) -> list[Layer]:
    """Return layers-with-processing-steps in dependency order."""
    steps = {layer.id: layer for layer in spec.layers if layer.processing_step}
    ordered: list[Layer] = []
    visited: set[str] = set()
    for layer in spec.layers:
        if layer.processing_step is not None:
            _visit(layer.id, steps, visited, ordered)
    return ordered


def _run_processing_steps(spec: Project, force: bool) -> None:
    """Run processing steps in dependency order for outputs that don't exist."""
    sources = {
        # TODO: verify path usage
        layer.id: resolve_source_path(layer.source, spec.project_path)
        for layer in spec.layers
    }
    for layer in _topo_sort(spec):
        step = layer.processing_step
        assert step is not None
        output = (spec.project_path / step.output).resolve()
        if not force and output.exists():
            print(f"  [skip] {layer.name!r} output exists")
            continue
        inputs = [sources[dep] for dep in step.depends_on]
        output.parent.mkdir(parents=True, exist_ok=True)
        action = step.action
        if hasattr(action, "fn"):
            print(f"  [python] {step.description}")
            action.fn(*inputs, output)
        else:
            fmt = {
                "output": output,
                **{
                    ("input" if i == 0 else f"input_{i}"): p
                    for i, p in enumerate(inputs)
                },
            }
            cmd = action.command.format(**fmt)
            print(f"  [shell] {cmd}")
            subprocess.run(cmd, shell=True, check=True)


def _source_hash(spec: Project) -> str:
    """Return a SHA-256 hex digest of project.py and all layers/*.py files."""
    # TODO: what is this? replace with id from ProjectSpec?
    assert spec.project_path is not None
    h = hashlib.sha256()
    project_py = spec.project_path / "project.py"
    if project_py.exists():
        h.update(project_py.read_bytes())
    layers_dir = spec.project_path / "layers"
    if layers_dir.exists():
        for f in sorted(layers_dir.glob("*.py")):
            h.update(f.read_bytes())
    return h.hexdigest()


def _needs_rebuild(spec: Project) -> bool:
    """Return True if source files have changed or (for qgis) output is absent."""
    assert spec.project_path is not None
    output_dir = spec.project_path / "output"
    if spec.output_format == "qgis" and not (output_dir / "project.qgs").exists():
        return True
    state_file = output_dir / ".state"
    if not state_file.exists():
        return True
    return state_file.read_text().strip() != _source_hash(spec)


def main() -> None:
    """Build output/ from project_path/project.py."""
    parser = argparse.ArgumentParser(
        description="Build QGIS or ArcGIS Pro lyrx output from project.py."
    )
    parser.add_argument("project_dir", help="Path to project directory")
    parser.add_argument(
        "--force", action="store_true", help="Force rebuild even if up to date"
    )
    args = parser.parse_args()
    force = args.force

    project_path = (Path.cwd() / args.project_dir).resolve()
    spec = load_spec(project_path)
    assert spec.project_path is not None

    if not force and not _needs_rebuild(spec):
        print("project is up to date")
        return

    fmt_targets = [str(spec.project_path / "project.py")]
    layers_dir = spec.project_path / "layers"
    if layers_dir.exists():
        fmt_targets += [str(layers_dir)]
    subprocess.run(["uv", "run", "black"] + fmt_targets, check=True)

    if spec.output_format == "qgis":
        _run_processing_steps(spec, force=force)
        render_qgis(spec)
        render_map(spec.project_path)  # TODO: update render_map to take spec
        update_readme(spec)
    elif spec.output_format == "lyrx":
        from alidade.render_lyrx import render_lyrx

        _run_processing_steps(spec, force=force)
        render_lyrx(spec)
        render_map(spec.project_path)  # TODO: update render_map to take spec
    else:
        raise NotImplementedError(f"Unknown output_format {spec.output_format!r}")

    output_dir = spec.project_path / "output"
    output_dir.mkdir(exist_ok=True)
    (output_dir / ".state").write_text(_source_hash(spec))


if __name__ == "__main__":
    main()
