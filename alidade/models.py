from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# ── Symbol layers ─────────────────────────────────────────────────────────────


class SimpleFill(BaseModel):
    kind: Literal["SimpleFill"] = "SimpleFill"
    color: str = "0,0,0,255"
    style: str = "solid"
    outline_color: str = "35,35,35,255"
    outline_style: str = "solid"
    outline_width: float = 0.5
    outline_width_unit: str = "MM"
    joinstyle: str = "bevel"
    offset: str = "0,0"


class SimpleLine(BaseModel):
    kind: Literal["SimpleLine"] = "SimpleLine"
    line_color: str = "0,0,0,255"
    line_style: str = "solid"
    line_width: float = 0.5
    line_width_unit: str = "MM"
    capstyle: str = "square"
    joinstyle: str = "bevel"
    offset: str = "0"


class SvgMarker(BaseModel):
    kind: Literal["SvgMarker"] = "SvgMarker"
    name: str  # path to SVG file
    size: float = 6.0
    size_unit: str = "MM"
    color: str = "0,0,0,255"
    outline_color: str = "35,35,35,255"
    outline_width: float = 0.0
    outline_width_unit: str = "MM"
    angle: float = 0.0
    offset: str = "0,0"
    offset_unit: str = "MM"


class SimpleMarker(BaseModel):
    kind: Literal["SimpleMarker"] = "SimpleMarker"
    name: str = "circle"  # shape: circle, square, diamond, …
    size: float = 2.0
    size_unit: str = "MM"
    color: str = "0,0,0,255"
    outline_color: str = "35,35,35,255"
    outline_width: float = 0.0
    outline_width_unit: str = "MM"
    angle: float = 0.0
    offset: str = "0,0"
    offset_unit: str = "MM"
    joinstyle: str = "bevel"


SymbolLayer = Annotated[
    SimpleFill | SimpleLine | SvgMarker | SimpleMarker,
    Field(discriminator="kind"),
]

# ── Symbol ────────────────────────────────────────────────────────────────────


class Symbol(BaseModel):
    type: Literal["fill", "line", "marker"]
    alpha: float = 1.0
    layers: list[SymbolLayer]


# ── Renderers ─────────────────────────────────────────────────────────────────


class Rule(BaseModel):
    key: str
    label: str = ""
    filter: str = ""
    symbol_index: int
    active: bool = True


class SingleSymbol(BaseModel):
    kind: Literal["singleSymbol"] = "singleSymbol"
    symbol: Symbol


class RuleRenderer(BaseModel):
    kind: Literal["RuleRenderer"] = "RuleRenderer"
    rules_key: str
    rules: list[Rule]
    symbols: list[Symbol]


class PaletteEntry(BaseModel):
    value: int
    color: str  # "#rrggbb"
    alpha: int = 255
    label: str = ""


class PalettedRenderer(BaseModel):
    kind: Literal["paletted"] = "paletted"
    band: int = 1
    opacity: float = 1.0
    entries: list[PaletteEntry]


Renderer = Annotated[
    SingleSymbol | RuleRenderer | PalettedRenderer,
    Field(discriminator="kind"),
]

# ── Processing step ───────────────────────────────────────────────────────────


class ShellAction(BaseModel):
    kind: Literal["shell"] = "shell"
    command: str  # template, e.g. "gdaldem slope {input} {output}"


class PythonAction(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    kind: Literal["python"] = "python"
    fn: Any  # callable(inputs: list[Path], output: Path) -> None


StepAction = Annotated[
    ShellAction | PythonAction,
    Field(discriminator="kind"),
]


class ProcessingStep(BaseModel):
    description: str
    action: StepAction
    depends_on: list[str]
    output: Path


# ── Layer ─────────────────────────────────────────────────────────────────────


class Layer(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    name: str
    type: Literal["vector", "raster"]
    source: str
    provider: str = "ogr"
    style_xml: Path | None = None  # styles/{layer_id}.xml — full <maplayer> element
    crs: str | None = None
    geometry_type: str | None = (
        None  # "Polygon", "LineString", or "Point" — enables XML-free vector layers
    )
    alpha_band: int | None = (
        None  # raster alpha band (e.g. 2 when created with gdalwarp -dstalpha)
    )
    visible: bool = True
    renderer: Renderer | None = None
    processing_step: ProcessingStep | None = None
    extra: dict[str, Any] = {}


# ── Print layout ──────────────────────────────────────────────────────────────
#
# Default US Letter landscape layout (279.4 × 215.9 mm, 300 DPI):
#
#   ┌──────────────────────────────────────────────────┐
#   │  title — 30 pt, centered, full-width strip       │
#   │ ┌──────────────────────────────────────────────┐ │
#   │ │↑N  map frame (rendered QGIS canvas)          │ │
#   │ │                                              │ │
#   │ └──────────────────────────────────────────────┘ │
#   │  legend          scale bar          credits 10pt  │
#   └──────────────────────────────────────────────────┘
#
# Add a print layout in project.py:
#
#   print_layout=PrintLayout(
#       title_text="My Map",
#       credits_text="Data: © OpenStreetMap contributors",
#   )
#
# Override any sub-item using keyword arguments; all fields have defaults:
#
#   print_layout=PrintLayout(
#       title_text="My Map",
#       credits_text="Source: USGS",
#       scale_bar=PrintScaleBar(unit_type="km", num_units_per_segment=10.0),
#       page=PrintPage(resolution_dpi=150),
#   )
#
# make build writes the result to output/print.qpt.


class PrintPage(BaseModel):
    # Page dimensions and output resolution. Defaults to US Letter landscape.
    width_mm: float = 279.4
    height_mm: float = 215.9
    resolution_dpi: int = 300


class PrintMapFrame(BaseModel):
    # The rendered QGIS canvas, filling the page below the title strip.
    # x_mm/y_mm is the top-left corner; width_mm/height_mm is the item size.
    x_mm: float = 4.764
    y_mm: float = 15.186
    width_mm: float = 269.774
    height_mm: float = 197.12


class PrintNorthArrow(BaseModel):
    # SVG north arrow, overlaid on the top-left corner of the map frame.
    # svg accepts any QGIS resource path (:/images/…) or an absolute file path.
    x_mm: float = 6.253
    y_mm: float = 17.270
    width_mm: float = 8.933
    height_mm: float = 9.826
    svg: str = ":/images/north_arrows/layout_default_north_arrow.svg"


class PrintScaleBar(BaseModel):
    # Scale bar drawn below the map, roughly centered horizontally.
    # unit_type is a QGIS unit string: "mi", "km", "m", "ft", etc.
    # style is a QGIS scale bar style name, e.g. "Single Box" or "Line Ticks Up".
    x_mm: float = 124.139
    y_mm: float = 199.209
    unit_type: str = "mi"
    num_segments: int = 2
    num_units_per_segment: float = 250.0
    style: str = "Single Box"


class PrintLegend(BaseModel):
    # Auto-sized legend drawn in the bottom-left. Only the anchor position is
    # configurable; the box grows downward/rightward with the number of layers.
    x_mm: float = 4.764
    y_mm: float = 188.823


class PrintLayout(BaseModel):
    # Complete print layout. title_text is a 30 pt header across the top of the
    # page; credits_text is a 10 pt label at the bottom right (attribution,
    # data source, date, etc.).  make build writes this to output/print.qpt.
    name: str = "print"
    page: PrintPage = Field(default_factory=PrintPage)
    title_text: str
    credits_text: str
    map_frame: PrintMapFrame = Field(default_factory=PrintMapFrame)
    north_arrow: PrintNorthArrow = Field(default_factory=PrintNorthArrow)
    scale_bar: PrintScaleBar = Field(default_factory=PrintScaleBar)
    legend: PrintLegend = Field(default_factory=PrintLegend)


# ── Project ───────────────────────────────────────────────────────────────────


class Project(BaseModel):
    model_config = ConfigDict(extra="allow")
    title: str
    crs: str
    layers: list[Layer]
    extent: tuple[float, float, float, float] | None = None
    extra: dict[str, Any] = {}
    print_layout: PrintLayout | None = None
