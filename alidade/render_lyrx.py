"""Render a map project → output/{layer.id}.lyrx (one file per layer)."""

import json
from alidade.lyrx.build import build_lyrx
from alidade.models import BoundMap


def render_lyrx(spec: BoundMap) -> None:
    """Write output/{layer.id}.lyrx for each layer in spec."""
    spec.output_path.mkdir(exist_ok=True)
    for layer in spec.layers:
        doc = build_lyrx(layer, spec.map_path)
        out_path = spec.output_path / f"{layer.id}.lyrx"
        out_path.write_text(json.dumps(doc, indent=4))
        print(f"Wrote {out_path}")
