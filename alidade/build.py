"""Entry point: render <project_path>/project.py → <project_path>/output/project.qgs."""

import argparse
import subprocess
from pathlib import Path

from alidade.makefile_gen import write
from alidade.readme import update_readme
from alidade.render_lyrx import render_lyrx
from alidade.render_map import render as render_map
from alidade.render_qgis import render as render_qgis
from alidade.util.helpers import bind_project


def build_layer(project_path: Path, layer_id: str) -> None:
    """Build a layer by id."""
    spec = bind_project(project_path)
    layers_by_id = {layer.id: layer for layer in spec.layers if layer.action}
    layer = layers_by_id.get(layer_id)
    if layer is None:
        raise SystemExit(f"No actionable layer with id {layer_id!r}")
    bound = layer.bind(project_path, with_inputs=True)
    bound.path.parent.mkdir(parents=True, exist_ok=True)
    action = layer.action
    assert action is not None
    if hasattr(action, "fn"):
        print(f"  [python] building {layer.name!r}")
        action.fn(bound)
    else:
        fmt = {
            "output": bound.path,
            **{
                ("input" if i == 0 else f"input_{i}"): inp.path
                for i, inp in enumerate(bound.inputs)
            },
        }
        cmd = action.command.format(**fmt)
        print(f"  [shell] {cmd}")
        subprocess.run(cmd, shell=True, check=True)


def build_layer_main() -> None:
    """CLI entry point for alidade-build-layer."""
    parser = argparse.ArgumentParser(description="Build a single project layer by id.")
    parser.add_argument("project_dir", help="Path to project directory")
    parser.add_argument("layer_id", help="Layer id to build")
    args = parser.parse_args()
    project_path = (Path.cwd() / args.project_dir).resolve()
    build_layer(project_path, args.layer_id)


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
    project_path = (Path.cwd() / args.project_dir).resolve()
    spec = bind_project(project_path)

    gen_mk = write(spec)

    make_cmd = ["make", "-f", str(gen_mk)]
    if args.force:
        make_cmd.append("-B")
    subprocess.run(make_cmd, check=True)

    if spec.output_format == "qgis":
        render_qgis(spec)
        update_readme(spec)
    elif spec.output_format == "lyrx":
        render_lyrx(spec)
    else:
        raise NotImplementedError(f"Unknown output_format {spec.output_format!r}")
    render_map(spec)


if __name__ == "__main__":
    main()
