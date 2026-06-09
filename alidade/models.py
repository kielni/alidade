import uuid
import warnings
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from alidade.color import BLACK, DARK_GRAY, LABEL_GRAY, Color

# Styling

# ── Symbol layers ─────────────────────────────────────────────────────────────


class SimpleFill(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    kind: Literal["SimpleFill"] = "SimpleFill"
    color: Color = BLACK
    style: str = "solid"
    outline_color: Color = DARK_GRAY
    outline_style: str = "solid"
    outline_width: float = 0.5
    outline_width_unit: str = "MM"
    joinstyle: str = "bevel"
    offset: str = "0,0"


class SimpleLine(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    kind: Literal["SimpleLine"] = "SimpleLine"
    line_color: Color = BLACK
    line_style: str = "solid"
    line_width: float = 0.5
    line_width_unit: str = "MM"
    capstyle: str = "square"
    joinstyle: str = "bevel"
    offset: str = "0"


class SvgMarker(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    kind: Literal["SvgMarker"] = "SvgMarker"
    name: str  # path to SVG file
    size: float = 6.0
    size_unit: str = "MM"
    color: Color = BLACK
    outline_color: Color = DARK_GRAY
    outline_width: float = 0.0
    outline_width_unit: str = "MM"
    angle: float = 0.0
    offset: str = "0,0"
    offset_unit: str = "MM"


class SimpleMarker(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    kind: Literal["SimpleMarker"] = "SimpleMarker"
    name: str = "circle"  # shape: circle, square, diamond, …
    size: float = 2.0
    size_unit: str = "MM"
    color: Color = BLACK
    outline_color: Color = DARK_GRAY
    outline_width: float = 0.0
    outline_width_unit: str = "MM"
    angle: float = 0.0
    cap_style: str = "square"
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
    model_config = ConfigDict(arbitrary_types_allowed=True)
    value: int
    color: Color
    label: str = ""


class PalettedRenderer(BaseModel):
    kind: Literal["paletted"] = "paletted"
    band: int = 1
    opacity: float = 1.0
    entries: list[PaletteEntry]


class GraduatedRange(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    lower: float
    upper: float
    label: str = ""
    color: Color


class GraduatedRenderer(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    kind: Literal["graduated"] = "graduated"
    attr: str  # field name to classify on
    ranges: list[GraduatedRange]
    outline_color: Color = DARK_GRAY
    outline_width: float = 0.26
    outline_style: str = "solid"


Renderer = Annotated[
    SingleSymbol | RuleRenderer | PalettedRenderer | GraduatedRenderer,
    Field(discriminator="kind"),
]

# ── Label ─────────────────────────────────────────────────────────────────────


class Label(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    field: str  # shapefile field name to display as label text
    font_family: str = "Open Sans"
    font_size: float = 10.0
    bold: bool = True
    color: Color = LABEL_GRAY
    y_offset: float = 2.0  # MM offset above the point symbol


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
    """Page dimensions and output resolution. Defaults to US Letter landscape."""

    width_mm: float = 279.4
    height_mm: float = 215.9
    resolution_dpi: int = 300


class PrintMapFrame(BaseModel):
    """The rendered QGIS canvas, filling the page below the title strip.

    x_mm/y_mm is the top-left corner; width_mm/height_mm is the item size.
    scale sets the map scale denominator (e.g. 600000 for 1:600,000).
    """

    x_mm: float = 4.764
    y_mm: float = 15.186
    width_mm: float = 269.774
    height_mm: float = 197.12
    scale: int | None = None


class PrintNorthArrow(BaseModel):
    """SVG north arrow, overlaid on the top-left corner of the map frame.

    svg accepts any QGIS resource path (:/images/...) or an absolute file path.
    """

    x_mm: float = 6.253
    y_mm: float = 17.270
    width_mm: float = 8.933
    height_mm: float = 9.826
    svg: str = ":/images/north_arrows/layout_default_north_arrow.svg"


class PrintScaleBar(BaseModel):
    """Scale bar drawn below the map, roughly centered horizontally.

    unit_type is a QGIS unit string: "mi", "km", "m", "ft", etc.
    style is a QGIS scale bar style name, e.g. "Single Box" or "Line Ticks Up".
    """

    x_mm: float = 124.139
    y_mm: float = 199.209
    unit_type: str = "mi"
    num_segments: int = 2
    num_units_per_segment: float = 250.0
    style: str = "Single Box"


class PrintLegend(BaseModel):
    """Auto-sized legend drawn in the bottom-left.

    Only the anchor position is configurable; the box grows downward/rightward
    with the number of layers.
    """

    x_mm: float = 4.764
    y_mm: float = 188.823


class PrintLayout(BaseModel):
    """Complete print layout.

    title_text is a 30 pt header across the top of the page; credits_text is a
    10 pt label at the bottom right (attribution, data source, date, etc.).
    make build writes this to output/print.qpt.

    orientation="portrait" swaps the default US Letter page to 215.9x279.4 mm
    and render_print_layout auto-computes map frame size and item y-positions
    from the page dimensions. Explicit field values always win over auto.
    """

    name: str = "print"
    orientation: Literal["landscape", "portrait"] = "landscape"
    page: PrintPage = Field(default_factory=PrintPage)
    title_text: str
    credits_text: str
    map_frame: PrintMapFrame = Field(default_factory=PrintMapFrame)
    north_arrow: PrintNorthArrow = Field(default_factory=PrintNorthArrow)
    scale_bar: PrintScaleBar = Field(default_factory=PrintScaleBar)
    legend: PrintLegend = Field(default_factory=PrintLegend)

    @model_validator(mode="after")
    def _page_from_orientation(self) -> "PrintLayout":
        if "page" not in self.model_fields_set and self.orientation == "portrait":
            self.page = PrintPage(width_mm=215.9, height_mm=279.4)
        return self


# Data

# ── Project ───────────────────────────────────────────────────────────────────


class Project(BaseModel):
    """Project spec; renders to QGIS or ArcGIS Pro lyrx depending on output_format."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    model_config = ConfigDict(extra="allow")
    output_format: Literal["qgis", "lyrx"] = "qgis"
    title: str
    crs: str
    layers: list[Layer]
    extent: tuple[float, float, float, float] | None = None
    print_layout: PrintLayout | None = None
    extra: dict[str, Any] = {}


class BoundProject(Project):
    project_path: Path

    @property
    def bound_layers(self) -> list[BoundLayer]:
        """Return all layers in this project with project_path set on them."""
        return [
            BoundLayer(
                **{f: getattr(layer, f) for f in Layer.model_fields if f != "inputs"},
                project_path=self.project_path,
            )
            for layer in self.layers
        ]

    @property
    def output_path(self) -> Path:
        return self.project_path / "output"


# ── Processing step ───────────────────────────────────────────────────────────


class ShellAction(BaseModel):
    kind: Literal["shell"] = "shell"
    command: str  # template, e.g. "gdaldem slope {input} {output}"


class PythonAction(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    kind: Literal["python"] = "python"
    fn: Any  # callable(*inputs: Path, output: Path) -> None


StepAction = Annotated[
    ShellAction | PythonAction,
    Field(discriminator="kind"),
]

# ── Layer ─────────────────────────────────────────────────────────────────────


class Layer(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    name: str
    type: Literal["vector", "raster"]
    # relative path for use in GIS
    datasource: str
    # "ogr" for files (shapefile/GeoJSON/CSV); "wms" for XYZ/WMS tile services.
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
    label: Label | None = None
    # this layer uses these other layers as inputs
    inputs: list["Layer"] = []
    action: StepAction | None = None
    # data specific to this layer, e.g. raw source file to process in action
    raw_file: str | None = None
    # human-readable description of what the raw data file contains
    source_description: str | None = None
    # provenance of the raw data (dataset name, agency, download source)
    source_origin: str | None = None
    extra: dict[str, Any] = {}

    def path_for(self, project_path: Path) -> Path:
        """Resolve datasource to an absolute path against project_path.

        Strips OGR/CSV suffixes (|layername=…, ?type=csv&…) before resolving.
        """
        part = self.datasource.split("|")[0].split("?")[0].lstrip("./")
        return (project_path / part).resolve()

    @field_validator("id")
    @classmethod
    def _pad_short_id(cls, v: str) -> str:
        # QGIS silently drops layers whose <id> is 10 characters or shorter.
        if len(v) > 10:
            return v
        padded = f"{v}_{uuid.uuid5(uuid.NAMESPACE_DNS, v).hex[:8]}"
        warnings.warn(
            f"Layer id {v!r} is <=10 chars and will be dropped by QGIS; "
            f"padded to {padded!r}",
            stacklevel=2,
        )
        return padded


# resolve the self-referential inputs: list["Layer"] forward ref
Layer.model_rebuild()


class BoundLayer(Layer):
    project_path: Path
    inputs: list["BoundLayer"] = []  # type: ignore[assignment]

    @property
    def path(self) -> Path:
        """Resolved file this layer represents."""
        return self.path_for(self.project_path)

    @property
    def raw_path(self) -> Path:
        """Resolved path to raw_file."""
        assert self.raw_file is not None, f"raw_file not set on layer {self.id!r}"
        return (self.project_path / self.raw_file).resolve()

    @property
    def output_path(self) -> Path:
        return self.project_path / "output"
