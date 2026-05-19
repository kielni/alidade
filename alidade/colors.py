"""QGIS color conversion utilities and common color constants.

Colors are stored as QGIS RGBA strings: "R,G,B,A" (0-255 integers).
Use to_qgis() to convert any CSS/X11 name or hex string to this format.
"""

import colour


def to_qgis(name: str, alpha: int = 255) -> str:
    """Return a QGIS RGBA string for a CSS/X11 color name or hex value."""
    c = colour.Color(name)
    r, g, b = (round(x * 255) for x in c.rgb)
    return f"{r},{g},{b},{alpha}"


BLACK = to_qgis("black")  # "0,0,0,255"
DARK_GRAY = to_qgis("#232323")  # "35,35,35,255" — default outline
WHITE = to_qgis("white")  # "255,255,255,255"
TRANSPARENT = "0,0,0,0"  # no CSS equivalent; pure transparent
LABEL_GRAY = to_qgis("#e1e1e1")  # "225,225,225,255" — default label
