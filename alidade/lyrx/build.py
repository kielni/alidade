"""Assemble CIMLayerDocument dicts for .lyrx output."""

import base64
import re
import warnings
from collections.abc import Callable
from pathlib import Path
from typing import Any

from alidade.color import Color
from alidade.lyrx.data_connection import build_data_connection
from alidade.lyrx.renderers import class_break, class_breaks_renderer, simple_renderer
from alidade.lyrx.symbols import _rgb_color, line_symbol, point_symbol, polygon_symbol
from alidade.models import (
    GraduatedRenderer,
    Label,
    Layer,
    PalettedRenderer,
    RuleRenderer,
    SimpleFill,
    SimpleLine,
    SimpleMarker,
    SingleSymbol,
    SvgMarker,
)

CIM_VERSION = "3.4.0"
CIM_BUILD = 55405

MM_TO_PT = 72 / 25.4


def _svg_data_uri(svg_path: Path, fill_color: Color) -> str:
    """Read SVG, substitute param(fill) with fill_color, return a data URI."""
    svg = svg_path.read_text(encoding="utf-8")
    svg = re.sub(r'param\(fill\)[^"]*', fill_color.hex, svg)
    b64 = base64.b64encode(svg.encode()).decode()
    return f"data:image/svg+xml;base64,{b64}"


def _build_label_class(label: Label) -> dict[str, Any]:
    """Return a CIMLabelClass dict for the given Label spec."""
    font_style = "Bold" if label.bold else "Regular"
    offset_pt = label.y_offset * MM_TO_PT
    return {
        "type": "CIMLabelClass",
        "expression": f"[{label.field}]",
        "expressionEngine": "VBScript",
        "featuresToLabel": "AllVisibleFeatures",
        "maplexLabelPlacementProperties": {
            "type": "CIMMaplexLabelPlacementProperties",
            "featureType": "Point",
            "primaryOffset": offset_pt,
            "primaryOffsetUnit": "Point",
            "pointPlacementMethod": "AroundPoint",
        },
        "standardLabelPlacementProperties": {
            "type": "CIMStandardLabelPlacementProperties",
            "featureType": "Point",
            "featureWeight": "None",
            "labelWeight": "High",
            "numLabelsOption": "OneLabelPerName",
            "pointPlacementMethod": "AroundPoint",
        },
        "textSymbol": {
            "type": "CIMSymbolReference",
            "symbol": {
                "type": "CIMTextSymbol",
                "fontFamilyName": label.font_family,
                "fontStyleName": font_style,
                "height": label.font_size,
                "symbol": {
                    "type": "CIMPolygonSymbol",
                    "symbolLayers": [
                        {
                            "type": "CIMSolidFill",
                            "enable": True,
                            "color": _rgb_color(label.color),
                        }
                    ],
                },
            },
        },
        "useCodedValue": True,
        "whereClause": "",
        "name": "Class 1",
        "priority": -1,
        "visibility": True,
        "iD": -1,
    }


def _build_simple_fill(first: SimpleFill, project_dir: Path) -> dict[str, Any]:
    return simple_renderer(
        polygon_symbol(first.color, first.outline_color, first.outline_width)
    )


def _build_simple_line(first: SimpleLine, project_dir: Path) -> dict[str, Any]:
    return simple_renderer(line_symbol(first.line_color, first.line_width))


def _build_svg_marker(first: SvgMarker, project_dir: Path) -> dict[str, Any]:
    svg_path = project_dir / first.name
    url = _svg_data_uri(svg_path, first.color)
    return simple_renderer(point_symbol(url, first.size * MM_TO_PT))


def _build_unsupported(first: Any, project_dir: Path) -> dict[str, Any] | None:
    warnings.warn(
        f"Layer {type(first).__name__!r}: symbol layer not yet supported for lyrx; "
        "ArcGIS Pro will apply a default symbol.",
        stacklevel=3,
    )
    return None


SYMBOL_LAYER_RENDERERS: dict[type, Callable[..., dict[str, Any] | None]] = {
    SimpleFill: _build_simple_fill,
    SimpleLine: _build_simple_line,
    SvgMarker: _build_svg_marker,
    SimpleMarker: _build_unsupported,
}


def _build_single_symbol_cim_renderer(
    layer: Layer, r: SingleSymbol, project_dir: Path
) -> dict[str, Any] | None:
    if not r.symbol.layers:
        return None
    first = r.symbol.layers[0]
    builder = SYMBOL_LAYER_RENDERERS.get(type(first))
    if builder is None:
        return None
    return builder(first, project_dir)


def _build_graduated_cim_renderer(
    layer: Layer, r: GraduatedRenderer, project_dir: Path
) -> dict[str, Any]:
    breaks = [
        class_break(
            polygon_symbol(gr.color, r.outline_color, r.outline_width),
            gr.label,
            gr.upper,
        )
        for gr in r.ranges
    ]
    return class_breaks_renderer(r.attr, breaks, r.ranges[0].lower)


def _build_unsupported_cim_renderer(
    layer: Layer, r: Any, project_dir: Path
) -> dict[str, Any] | None:
    warnings.warn(
        f"Layer {layer.id!r}: renderer {type(r).__name__!r} not supported for lyrx; "
        "ArcGIS Pro will apply a default symbol.",
        stacklevel=3,
    )
    return None


# ── Dispatch tables (importable by test_completeness) ─────────────────────────

RENDERERS: dict[type, Callable[..., dict[str, Any] | None]] = {
    SingleSymbol: _build_single_symbol_cim_renderer,
    GraduatedRenderer: _build_graduated_cim_renderer,
    RuleRenderer: _build_unsupported_cim_renderer,  # deferred
    PalettedRenderer: _build_unsupported_cim_renderer,  # deferred
}


def _build_renderer(layer: Layer, project_dir: Path) -> dict[str, Any] | None:
    """Return a CIM renderer dict for the layer, or None if unsupported."""
    r = layer.renderer
    if r is None:
        return None
    handler = RENDERERS.get(type(r))
    if handler is None:
        return None
    return handler(layer, r, project_dir)


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
    if layer.label is not None:
        doc["labelClasses"] = [_build_label_class(layer.label)]
        doc["labelVisibility"] = True
    return doc


def build_lyrx(layer: Layer, project_dir: Path) -> dict[str, Any]:
    """Assemble a full CIMLayerDocument dict ready to serialize as .lyrx."""
    cimpath = f"CIMPATH=layers/{layer.id}.json"
    return {
        "type": "CIMLayerDocument",
        "version": CIM_VERSION,
        "build": CIM_BUILD,
        "layers": [cimpath],
        "layerDefinitions": [_build_feature_layer(layer, project_dir)],
    }
