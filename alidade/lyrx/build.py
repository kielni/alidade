"""Assemble CIMLayerDocument dicts for .lyrx output."""

import base64
import re
import warnings
from pathlib import Path
from typing import Any

from alidade.color import Color
from alidade.lyrx.data_connection import build_data_connection
from alidade.lyrx.renderers import class_break, class_breaks_renderer, simple_renderer
from alidade.lyrx.symbols import line_symbol, point_symbol, polygon_symbol
from alidade.models import (
    GraduatedRenderer,
    Layer,
    SimpleFill,
    SimpleLine,
    SingleSymbol,
    SvgMarker,
)

_CIM_VERSION = "3.4.0"
_CIM_BUILD = 55405

_MM_TO_PT = 72 / 25.4


def _svg_data_uri(svg_path: Path, fill_color: Color) -> str:
    """Read SVG, substitute param(fill) with fill_color, return a data URI."""
    svg = svg_path.read_text(encoding="utf-8")
    svg = re.sub(r'param\(fill\)[^"]*', fill_color.hex, svg)
    b64 = base64.b64encode(svg.encode()).decode()
    return f"data:image/svg+xml;base64,{b64}"


def _build_renderer(layer: Layer, project_dir: Path) -> dict[str, Any] | None:
    """Return a CIM renderer dict for the layer, or None if unsupported."""
    r = layer.renderer
    if r is None:
        return None

    if isinstance(r, SingleSymbol) and r.symbol.layers:
        first = r.symbol.layers[0]
        if isinstance(first, SimpleFill):
            return simple_renderer(
                polygon_symbol(first.color, first.outline_color, first.outline_width)
            )
        if isinstance(first, SimpleLine):
            return simple_renderer(line_symbol(first.line_color, first.line_width))
        if isinstance(first, SvgMarker):
            svg_path = project_dir / first.name
            url = _svg_data_uri(svg_path, first.color)
            return simple_renderer(point_symbol(url, first.size * _MM_TO_PT))

    if isinstance(r, GraduatedRenderer):
        breaks = [
            class_break(
                polygon_symbol(gr.color, r.outline_color, r.outline_width),
                gr.label,
                gr.upper,
            )
            for gr in r.ranges
        ]
        return class_breaks_renderer(r.attr, breaks, r.ranges[0].lower)

    warnings.warn(
        f"Layer {layer.id!r}: renderer {type(r).__name__!r} not supported for lyrx; "
        "ArcGIS Pro will apply a default symbol.",
        stacklevel=3,
    )
    return None


def _build_feature_layer(layer: Layer, project_dir: Path) -> dict[str, Any]:
    cimpath = f"CIMPATH=layers/{layer.id}.json"
    doc: dict[str, Any] = {
        "type": "CIMFeatureLayer",
        "name": layer.name,
        "uRI": cimpath,
        "sourceModifiedTime": {"type": "TimeInstant"},
        "useSourceMetadata": True,
        "description": layer.name,
        "layerType": "Operational",
        "showLegends": True,
        "visibility": layer.visible,
        "displayCacheType": "Permanent",
        "maxDisplayCacheAge": 5,
        "showPopups": True,
        "serviceLayerID": -1,
        "refreshRate": -1,
        "refreshRateUnit": "esriTimeUnitsSeconds",
        "blendingMode": "Alpha",
        "featureTable": {
            "type": "CIMFeatureTable",
            "displayField": "OBJECTID",
            "editable": True,
            "dataConnection": build_data_connection(layer, project_dir),
            "studyAreaSpatialRel": "esriSpatialRelUndefined",
            "searchOrder": "esriSearchOrderSpatial",
        },
    }
    renderer = _build_renderer(layer, project_dir)
    if renderer is not None:
        doc["renderer"] = renderer
    return doc


def build_lyrx(layer: Layer, project_dir: Path) -> dict[str, Any]:
    """Assemble a full CIMLayerDocument dict ready to serialize as .lyrx."""
    cimpath = f"CIMPATH=layers/{layer.id}.json"
    return {
        "type": "CIMLayerDocument",
        "version": _CIM_VERSION,
        "build": _CIM_BUILD,
        "layers": [cimpath],
        "layerDefinitions": [_build_feature_layer(layer, project_dir)],
    }
