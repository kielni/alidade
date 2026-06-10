"""Canonical color type and palette helpers for alidade.

Authors specify colors as Color objects constructed from hex strings.
Conversions to other formats (.qgis, .matplotlib_rgba) happen only at output boundaries.
"""

from dataclasses import dataclass

import palettable.colorbrewer


@dataclass(frozen=True)
class Color:
    r: int
    g: int
    b: int
    a: int = 255

    @classmethod
    def from_hex(cls, hex_str: str, alpha: int = 255) -> "Color":
        """Construct from a '#rrggbb' hex string with optional alpha (0-255)."""
        h = hex_str.lstrip("#")
        return cls(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)

    @classmethod
    def from_qgis(cls, qgis_str: str) -> "Color":
        """Parse a QGIS 'R,G,B,A' string. Use only at QGIS XML parse boundaries."""
        parts = qgis_str.split(",")
        r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
        a = int(parts[3]) if len(parts) >= 4 else 255
        return cls(r, g, b, a)

    def with_alpha(self, alpha: int) -> "Color":
        """Return a copy of this color at a different alpha."""
        return Color(self.r, self.g, self.b, alpha)

    @property
    def qgis(self) -> str:
        """QGIS 'R,G,B,A' string. Use only when writing QGIS XML."""
        return f"{self.r},{self.g},{self.b},{self.a}"

    @property
    def matplotlib_rgba(self) -> tuple[float, float, float, float]:
        """Matplotlib RGBA tuple (0-1). Use only in render_map.py."""
        return (self.r / 255, self.g / 255, self.b / 255, self.a / 255)

    @property
    def hex(self) -> str:
        """'#rrggbb' hex string (no alpha)."""
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"


def brewer(palette_name: str, n: int, alpha: int = 255) -> list[Color]:
    """Return n Color objects from a ColorBrewer palette at the given alpha.

    palette_name is the dotted palettable path without the count suffix,
    e.g. 'sequential.Purples' or 'diverging.RdYlBu'.
    """
    namespace, name = palette_name.split(".")
    module = getattr(palettable.colorbrewer, namespace)
    palette = getattr(module, f"{name}_{n}")
    return [Color.from_hex(h, alpha) for h in palette.hex_colors]


# Project-agnostic constants — use in model defaults and generic rendering code.
# Project-specific colors belong in projects/<name>/palette.py.
BLACK = Color(0, 0, 0)
DARK_GRAY = Color(35, 35, 35)
WHITE = Color(255, 255, 255)
TRANSPARENT = Color(0, 0, 0, 0)
