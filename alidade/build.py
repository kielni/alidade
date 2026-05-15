"""Entry point: render <project_dir>/project.py → <project_dir>/output/project.qgs."""

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

from alidade.models import Layer, Project
from alidade.readme import update_readme
from alidade.render import _load_spec, render

HERE = Path(__file__).parent  # alidade/


def _resolve_source_path(source: str, project_dir: Path) -> Path:
    """Return the absolute filesystem path for a layer source string."""
    path_part = source.split("|")[0].split("?")[0]
    if path_part.startswith("/") or ":" in path_part.split("/")[0]:
        return Path(path_part)
    if path_part.startswith("./") or path_part.startswith("data/"):
        return (project_dir / path_part).resolve()
    return (HERE / path_part).resolve()


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


def _run_processing_steps(spec: Project, project_dir: Path, force: bool) -> None:
    """Run processing steps in dependency order for outputs that don't exist."""
    sources = {
        layer.id: _resolve_source_path(layer.source, project_dir)
        for layer in spec.layers
    }
    for layer in _topo_sort(spec):
        step = layer.processing_step
        assert step is not None
        output = (project_dir / step.output).resolve()
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


def _source_hash(project_dir: Path) -> str:
    """Return a SHA-256 hex digest of project.py and all layers/*.py files."""
    h = hashlib.sha256()
    project_py = project_dir / "project.py"
    if project_py.exists():
        h.update(project_py.read_bytes())
    layers_dir = project_dir / "layers"
    if layers_dir.exists():
        for f in sorted(layers_dir.glob("*.py")):
            h.update(f.read_bytes())
    return h.hexdigest()


def _needs_rebuild(project_dir: Path) -> bool:
    """Return True if output/project.qgs is absent or source files have changed."""
    output_dir = project_dir / "output"
    if not (output_dir / "project.qgs").exists():
        return True
    state_file = output_dir / ".state"
    if not state_file.exists():
        return True
    return state_file.read_text().strip() != _source_hash(project_dir)


def main() -> None:
    """Build project_dir/output/project.qgs from project_dir/project.py."""
    parser = argparse.ArgumentParser(
        description="Build QGIS project file from project.py."
    )
    parser.add_argument("project_dir", help="Path to project directory")
    parser.add_argument(
        "--force", action="store_true", help="Force rebuild even if up to date"
    )
    args = parser.parse_args()
    force = args.force

    project_dir = (Path.cwd() / args.project_dir).resolve()
    project_py = project_dir / "project.py"

    if not project_py.exists():
        print(f"project.py not found in {project_dir} — run 'make dump' first")
        sys.exit(1)

    if not force and not _needs_rebuild(project_dir):
        print("project.qgs is up to date")
        return

    fmt_targets = [str(project_py)]
    layers_dir = project_dir / "layers"
    if layers_dir.exists():
        fmt_targets += [str(layers_dir)]
    subprocess.run(["uv", "run", "black"] + fmt_targets, check=True)

    spec = _load_spec(project_dir)
    _run_processing_steps(spec, project_dir, force=force)
    render(spec, project_dir)
    update_readme(spec, project_dir)

    output_dir = project_dir / "output"
    output_dir.mkdir(exist_ok=True)
    (output_dir / ".state").write_text(_source_hash(project_dir))


if __name__ == "__main__":
    main()
