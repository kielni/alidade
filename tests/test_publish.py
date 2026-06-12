"""Tests for publish_arcgis.py: renderer translation to ArcGIS REST API format."""

from alidade.color import Color
from alidade.models import (
    GraduatedRange,
    GraduatedRenderer,
    PaletteEntry,
    PalettedRenderer,
    Rule,
    RuleRenderer,
    SimpleFill,
    SimpleLine,
    SimpleMarker,
    SingleSymbol,
    SvgMarker,
    Symbol,
)
from alidade.publish_arcgis import _renderer_to_arcgis


def _make_single_symbol(sym_layer):
    return SingleSymbol(symbol=Symbol(type="fill", layers=[sym_layer]))


def test_single_symbol_simple_fill():
    renderer = _make_single_symbol(
        SimpleFill(color=Color.from_hex("#aabbcc"), outline_color=Color(0, 0, 0))
    )
    result = _renderer_to_arcgis(renderer, "Polygon")
    assert result is not None
    assert result["type"] == "simple"
    sym = result["symbol"]
    assert sym["type"] == "esriSFS"
    assert sym["color"][:3] == [0xAA, 0xBB, 0xCC]


def test_single_symbol_simple_line():
    renderer = _make_single_symbol(SimpleLine(line_color=Color.from_hex("#112233")))
    result = _renderer_to_arcgis(renderer, "LineString")
    assert result is not None
    assert result["type"] == "simple"
    sym = result["symbol"]
    assert sym["type"] == "esriSLS"
    assert sym["color"][:3] == [0x11, 0x22, 0x33]


def test_single_symbol_simple_marker():
    renderer = _make_single_symbol(
        SimpleMarker(name="circle", color=Color.from_hex("#ff0000"), size=3.0)
    )
    result = _renderer_to_arcgis(renderer, "Point")
    assert result is not None
    assert result["type"] == "simple"
    sym = result["symbol"]
    assert sym["type"] == "esriSMS"
    assert sym["style"] == "esriSMSCircle"
    assert sym["color"][:3] == [255, 0, 0]


def test_single_symbol_svg_marker_fallback():
    renderer = _make_single_symbol(
        SvgMarker(name="test.svg", color=Color.from_hex("#0000ff"), size=5.0)
    )
    result = _renderer_to_arcgis(renderer, "Point")
    assert result is not None
    assert result["type"] == "simple"
    sym = result["symbol"]
    assert sym["type"] == "esriSMS"
    assert sym["color"][:3] == [0, 0, 255]


def test_graduated_renderer():
    renderer = GraduatedRenderer(
        attr="score",
        ranges=[
            GraduatedRange(
                lower=0.0, upper=0.5, label="Low", color=Color.from_hex("#ffff00")
            ),
            GraduatedRange(
                lower=0.5, upper=1.0, label="High", color=Color.from_hex("#ff0000")
            ),
        ],
    )
    result = _renderer_to_arcgis(renderer, "Polygon")
    assert result is not None
    assert result["type"] == "classBreaks"
    assert result["field"] == "score"
    infos = result["classBreakInfos"]
    assert len(infos) == 2
    assert infos[0]["label"] == "Low"
    assert infos[1]["label"] == "High"


def test_rule_renderer_equality_filters():
    renderer = RuleRenderer(
        rules_key="rank",
        rules=[
            Rule(key="r1", label="Best", filter='"rank" = 1', symbol_index=0),
            Rule(key="r2", label="Other", filter="ELSE", symbol_index=1),
        ],
        symbols=[
            Symbol(
                type="marker", layers=[SimpleMarker(color=Color(0, 200, 0), size=3.0)]
            ),
            Symbol(
                type="marker",
                layers=[SimpleMarker(color=Color(200, 200, 200), size=3.0)],
            ),
        ],
    )
    result = _renderer_to_arcgis(renderer, "Point")
    assert result is not None
    assert result["type"] == "uniqueValue"
    assert result["field1"] == "rank"
    uv_infos = result["uniqueValueInfos"]
    assert any(uv["label"] == "Best" for uv in uv_infos)
    assert result.get("defaultSymbol") is not None
    assert result.get("defaultLabel") == "Other"


def test_paletted_renderer():
    renderer = PalettedRenderer(
        entries=[
            PaletteEntry(value=1, color=Color.from_hex("#1a9641"), label="Gentle"),
            PaletteEntry(value=2, color=Color.from_hex("#fdae61"), label="Steep"),
        ]
    )
    result = _renderer_to_arcgis(renderer, None)
    assert result is not None
    assert result["type"] == "uniqueValue"
    uv_infos = result["uniqueValueInfos"]
    assert len(uv_infos) == 2
    assert uv_infos[0]["label"] == "Gentle"
    assert uv_infos[1]["label"] == "Steep"


def test_none_renderer_returns_none():
    assert _renderer_to_arcgis(None, "Polygon") is None
