"""CIM symbol factories."""

from typing import Any

from alidade.color import Color


def _rgb_color(color: Color) -> dict[str, Any]:
    """Return a CIMRGBColor dict. Alpha is 0-255 → 0-100.

    Stays here rather than on Color: encodes ArcGIS CIM specifics
    (type name, 0-100 alpha) that color.py should not know about.
    """
    a_100 = round(color.a / 255 * 100)
    return {"type": "CIMRGBColor", "values": [color.r, color.g, color.b, a_100]}


def _solid_stroke(color: Color, width: float) -> dict[str, Any]:
    return {
        "type": "CIMSolidStroke",
        "enable": True,
        "anchor3D": "Center",
        "capStyle": "Round",
        "joinStyle": "Round",
        "lineStyle3D": "Strip",
        "miterLimit": 10,
        "height3D": 1,
        "width": width,
        "color": _rgb_color(color),
    }


def polygon_symbol(
    fill_color: Color, outline_color: Color, outline_width: float
) -> dict[str, Any]:
    """Return a CIMSymbolReference for a simple filled polygon.

    symbolLayers order: CIMSolidStroke first, CIMSolidFill second
    (confirmed from round-tripped .lyrx; opposite of QML layer order).
    """
    return {
        "type": "CIMSymbolReference",
        "symbol": {
            "type": "CIMPolygonSymbol",
            "angleAlignment": "Map",
            "symbolLayers": [
                _solid_stroke(outline_color, outline_width),
                {
                    "type": "CIMSolidFill",
                    "enable": True,
                    "color": _rgb_color(fill_color),
                },
            ],
        },
    }


def line_symbol(color: Color, width: float) -> dict[str, Any]:
    """Return a CIMSymbolReference for a simple line."""
    return {
        "type": "CIMSymbolReference",
        "symbol": {
            "type": "CIMLineSymbol",
            "symbolLayers": [_solid_stroke(color, width)],
        },
    }


def point_symbol(url: str, size_pt: float) -> dict[str, Any]:
    """Return a CIMSymbolReference for a CIMPictureMarker (SVG or raster).

    url should be a data URI: data:image/svg+xml;base64,... or data:image/png;base64,...
    size_pt is the marker height in points (dominantSizeAxis=Y).
    """
    return {
        "type": "CIMSymbolReference",
        "symbol": {
            "type": "CIMPointSymbol",
            "symbolLayers": [
                {
                    "type": "CIMPictureMarker",
                    "enable": True,
                    "anchorPointUnits": "Relative",
                    "dominantSizeAxis": "Y",
                    "size": size_pt,
                    "scaleX": 1,
                    "textureFilter": "Draft",
                    "url": url,
                }
            ],
            "angleAlignment": "Map",
        },
    }
