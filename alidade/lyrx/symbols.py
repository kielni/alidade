"""CIM symbol factories."""

from typing import Any


def _rgb_color(color_str: str) -> dict[str, Any]:
    """Return a CIMRGBColor dict from 'R,G,B,A' string. Alpha is 0-255 → 0-100."""
    parts = color_str.split(",")
    r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
    a_100 = round(int(parts[3]) / 255 * 100) if len(parts) > 3 else 100
    return {"type": "CIMRGBColor", "values": [r, g, b, a_100]}


def _solid_stroke(color_str: str, width: float) -> dict[str, Any]:
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
        "color": _rgb_color(color_str),
    }


def polygon_symbol(
    fill_color: str, outline_color: str, outline_width: float
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


def line_symbol(color: str, width: float) -> dict[str, Any]:
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
