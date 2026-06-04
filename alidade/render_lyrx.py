"""Render project.py → output/{layer.id}.lyrx (one file per layer)."""

import json
from alidade.lyrx.build import build_lyrx
from alidade.models import Project


def render_lyrx(spec: Project) -> None:
    """Write output/{layer.id}.lyrx for each layer in spec."""
    assert spec.project_path is not None
    output_dir = spec.project_path / "output"
    output_dir.mkdir(exist_ok=True)
    for layer in spec.layers:
        doc = build_lyrx(layer, spec.project_path)
        out_path = output_dir / f"{layer.id}.lyrx"
        out_path.write_text(json.dumps(doc, indent=4))
        print(f"Wrote {out_path}")
