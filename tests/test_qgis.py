"""Tests for render_qgis.py: verify .qgs output is well-formed XML with correct
renderers."""

import xml.etree.ElementTree as ET

import pytest

import alidade.render_qgis as render_qgis
from alidade.color import Color


@pytest.mark.parametrize(
    "layer_fixture, expected_renderer_type",
    [
        ("simple_fill_layer", "singleSymbol"),
        ("simple_line_layer", "singleSymbol"),
        ("svg_marker_layer", "singleSymbol"),
        ("rule_renderer_layer", "RuleRenderer"),
        ("graduated_layer", "graduatedSymbol"),
    ],
)
def test_qgis_vector_renderer_type(
    request, make_map, layer_fixture, expected_renderer_type
):
    layer = request.getfixturevalue(layer_fixture)
    spec = make_map([layer])
    render_qgis.render(spec)

    qgs_path = spec.map_path / "output" / "project.qgs"
    assert qgs_path.exists(), "project.qgs was not written"

    root = ET.parse(str(qgs_path)).getroot()
    maplayers = root.findall(".//maplayer")
    assert len(maplayers) == 1, f"expected 1 maplayer, got {len(maplayers)}"

    renderer = maplayers[0].find("renderer-v2")
    assert renderer is not None, "no renderer-v2 element"
    assert renderer.attrib.get("type") == expected_renderer_type


def test_qgis_raster_paletted_renderer(make_map, paletted_layer):
    spec = make_map([paletted_layer])
    render_qgis.render(spec)

    qgs_path = spec.map_path / "output" / "project.qgs"
    assert qgs_path.exists()

    root = ET.parse(str(qgs_path)).getroot()
    maplayers = root.findall(".//maplayer")
    assert len(maplayers) == 1

    raster_renderer = maplayers[0].find(".//rasterrenderer[@type='paletted']")
    assert raster_renderer is not None, "no rasterrenderer type='paletted' found"


def test_qgis_simple_fill_color(make_map, simple_fill_layer):
    expected = Color.from_hex("#ffffff")
    spec = make_map([simple_fill_layer])
    render_qgis.render(spec)

    qgs_path = spec.map_path / "output" / "project.qgs"
    root = ET.parse(str(qgs_path)).getroot()

    color_opt = root.find(
        ".//maplayer/renderer-v2/symbols/symbol/layer/Option/Option[@name='color']"
    )
    assert color_opt is not None, "color option element not found"
    color_str = color_opt.attrib.get("value", "")
    parts = [int(x) for x in color_str.split(",")[:4]]
    assert parts[:3] == [expected.r, expected.g, expected.b]


def test_qgis_multiple_layers(make_map, simple_fill_layer, simple_line_layer):
    spec = make_map([simple_fill_layer, simple_line_layer])
    render_qgis.render(spec)

    qgs_path = spec.map_path / "output" / "project.qgs"
    root = ET.parse(str(qgs_path)).getroot()
    maplayers = root.findall(".//maplayer")
    assert len(maplayers) == 2
