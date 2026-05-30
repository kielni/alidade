"""Render project.py → output/{layer.id}.lyrx (one file per layer)."""

import json
from pathlib import Path

from alidade.lyrx.build import build_lyrx
from alidade.models import Project


def render_lyrx(spec: Project, project_dir: Path) -> None:
    """Write output/{layer.id}.lyrx for each layer in spec."""
    output_dir = project_dir / "output"
    output_dir.mkdir(exist_ok=True)
    for layer in spec.layers:
        doc = build_lyrx(layer, project_dir)
        out_path = output_dir / f"{layer.id}.lyrx"
        out_path.write_text(json.dumps(doc, indent=4))
        print(f"Wrote {out_path}")
