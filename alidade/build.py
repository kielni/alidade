"""Entry point: render <project_path>/project.py → <project_path>/output/project.qgs."""

import argparse
import hashlib
import subprocess
from pathlib import Path

from alidade.models import BoundLayer, BoundProject, Layer
from alidade.readme import update_readme
from alidade.render_lyrx import render_lyrx
from alidade.render_map import render as render_map
from alidade.render_qgis import render as render_qgis
from alidade.util.helpers import bind_project

_LAYER_STATE_DIR = ".layer_state"


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
        assert layer.action is not None
        for inp in layer.inputs:
            _visit(inp.id, steps, visited, ordered)
        ordered.append(layer)


def _topo_sort(spec: BoundProject) -> list[Layer]:
    """Return layers-with-actions in dependency order."""
    steps = {layer.id: layer for layer in spec.layers if layer.action}
    ordered: list[Layer] = []
    visited: set[str] = set()
    for layer in spec.layers:
        if layer.action is not None:
            _visit(layer.id, steps, visited, ordered)
    return ordered


def _bind(layer: Layer, project_path: Path) -> BoundLayer:
    """Return a BoundLayer copy with project_path set on it and its direct inputs."""
    fields = {f: getattr(layer, f) for f in Layer.model_fields if f != "inputs"}
    bound_inputs = [
        BoundLayer(
            **{f: getattr(inp, f) for f in Layer.model_fields if f != "inputs"},
            project_path=project_path,
        )
        for inp in layer.inputs
    ]
    return BoundLayer(**fields, project_path=project_path, inputs=bound_inputs)


def _find_layer_source(layer_id: str, layers_dir: Path) -> Path | None:
    """Find the layers/*.py file that defines layer_id."""
    needle = f'id="{layer_id}"'
    for f in sorted(layers_dir.glob("*.py")):
        if needle in f.read_text():
            return f
    return None


def _layer_source_hash(layer: Layer, spec: BoundProject) -> str:
    """Hash the source files most likely to affect this layer's output.

    Includes util.py (shared helpers) and the layer's own layers/*.py file.
    """
    assert spec.project_path is not None
    h = hashlib.sha256()
    util_py = spec.project_path / "util.py"
    if util_py.exists():
        h.update(util_py.read_bytes())
    layers_dir = spec.project_path / "layers"
    src = _find_layer_source(layer.id, layers_dir)
    if src is not None:
        h.update(src.read_bytes())
    return h.hexdigest()


def _run_processing_steps(spec: BoundProject, force: bool) -> None:
    """Run processing steps for layers whose output is missing or stale."""
    assert spec.project_path is not None
    state_dir = spec.output_path / _LAYER_STATE_DIR
    for layer in _topo_sort(spec):
        bound = _bind(layer, spec.project_path)
        output = bound.path
        current_hash = _layer_source_hash(layer, spec)
        state_file = state_dir / layer.id
        stored_hash = state_file.read_text().strip() if state_file.exists() else ""

        if not force and output.exists() and stored_hash == current_hash:
            print(f"  [skip] {layer.name!r} up to date")
            continue

        spec.output_path.mkdir(parents=True, exist_ok=True)
        state_dir.mkdir(parents=True, exist_ok=True)
        action = layer.action
        assert action is not None
        if hasattr(action, "fn"):
            print(f"  [python] building {layer.name!r}")
            action.fn(bound)
        else:
            fmt = {
                "output": output,
                **{
                    ("input" if i == 0 else f"input_{i}"): inp.path
                    for i, inp in enumerate(bound.inputs)
                },
            }
            cmd = action.command.format(**fmt)
            print(f"  [shell] {cmd}")
            subprocess.run(cmd, shell=True, check=True)

        state_file.write_text(current_hash)


def _needs_rebuild(spec: BoundProject) -> bool:
    """Return True if any layer output is missing or its source hash has changed."""
    assert spec.project_path is not None
    if spec.output_format == "qgis" and not (spec.output_path / "project.qgs").exists():
        return True
    state_dir = spec.output_path / _LAYER_STATE_DIR
    for layer in _topo_sort(spec):
        bound = _bind(layer, spec.project_path)
        if not bound.path.exists():
            return True
        state_file = state_dir / layer.id
        if not state_file.exists():
            return True
        if state_file.read_text().strip() != _layer_source_hash(layer, spec):
            return True
    return False


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
    spec = bind_project(project_path)

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
        render_map(spec)
        update_readme(spec)
    elif spec.output_format == "lyrx":
        _run_processing_steps(spec, force=force)
        render_lyrx(spec)
        render_map(spec)
    else:
        raise NotImplementedError(f"Unknown output_format {spec.output_format!r}")


if __name__ == "__main__":
    main()
