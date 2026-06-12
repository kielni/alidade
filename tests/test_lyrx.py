"""Tests for lyrx/build.py: verify CIMLayerDocument structure and color encoding."""

import warnings

import pytest

from alidade.lyrx.build import build_lyrx


@pytest.mark.parametrize(
    "layer_fixture, expected_renderer_type",
    [
        ("simple_fill_layer", "CIMSimpleRenderer"),
        ("simple_line_layer", "CIMSimpleRenderer"),
        ("svg_marker_layer", "CIMSimpleRenderer"),
        ("graduated_layer", "CIMClassBreaksRenderer"),
    ],
)
def test_lyrx_supported_renderer(
    request, map_root, layer_fixture, expected_renderer_type
):
    layer = request.getfixturevalue(layer_fixture)
    doc = build_lyrx(layer, map_root)

    assert doc["type"] == "CIMLayerDocument"
    renderer = doc["layerDefinitions"][0].get("renderer")
    assert renderer is not None, "renderer key missing from layerDefinition"
    assert renderer["type"] == expected_renderer_type


@pytest.mark.parametrize("layer_fixture", ["rule_renderer_layer", "paletted_layer"])
def test_lyrx_unsupported_renderer_no_renderer_key(request, map_root, layer_fixture):
    layer = request.getfixturevalue(layer_fixture)
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        doc = build_lyrx(layer, map_root)
    assert doc["type"] == "CIMLayerDocument"
    assert "renderer" not in doc["layerDefinitions"][0]


def test_lyrx_alpha_range(map_root, simple_fill_layer):
    doc = build_lyrx(simple_fill_layer, map_root)
    stack = [doc]
    while stack:
        obj = stack.pop()
        if isinstance(obj, dict):
            if obj.get("type") == "CIMRGBColor":
                alpha = obj["values"][3]
                assert 0 <= alpha <= 100, f"CIMRGBColor alpha {alpha} not in [0, 100]"
            stack.extend(obj.values())
        elif isinstance(obj, list):
            stack.extend(obj)
