"""Tests for render_map.py: verify _build_figure populates Figure correctly."""

from alidade.color import Color
from alidade.render_map import _build_figure


def _rgba_close(actual, expected_rgba, tol=0.01):
    """True if actual RGBA (0-1 floats) is close to expected_rgba."""
    return all(abs(a - e) < tol for a, e in zip(actual[:4], expected_rgba))


def test_build_figure_simple_fill(make_map, simple_fill_layer):
    spec = make_map([simple_fill_layer])
    fig, ax = _build_figure(spec)
    assert len(fig.get_axes()) == 1
    assert ax.get_title() == spec.title
    assert len(ax.collections) > 0
    expected = Color.from_hex("#ffffff").matplotlib_rgba
    fc = ax.collections[0].get_facecolor()
    assert len(fc) > 0
    assert _rgba_close(fc[0], expected)


def test_build_figure_simple_line(make_map, simple_line_layer):
    spec = make_map([simple_line_layer])
    _, ax = _build_figure(spec)
    assert len(ax.collections) > 0
    expected = Color.from_hex("#784828").matplotlib_rgba
    col = ax.collections[0]
    # geopandas may create PatchCollection or LineCollection for line geometry
    colors = col.get_edgecolor() if len(col.get_edgecolor()) else col.get_facecolor()
    assert len(colors) > 0
    assert _rgba_close(colors[0], expected)


def test_build_figure_rule_renderer(make_map, rule_renderer_layer):
    spec = make_map([rule_renderer_layer])
    _, ax = _build_figure(spec)
    assert len(ax.collections) >= 1
    legend = ax.get_legend()
    assert legend is not None
    labels = [t.get_text() for t in legend.get_texts()]
    assert "Best" in labels
    assert "Better" in labels
    assert "Good" in labels


def test_build_figure_graduated_renderer(make_map, graduated_layer):
    spec = make_map([graduated_layer])
    _, ax = _build_figure(spec)
    assert len(ax.collections) >= 1
    legend = ax.get_legend()
    assert legend is not None
    labels = [t.get_text() for t in legend.get_texts()]
    assert "Low" in labels
    assert "Medium" in labels
    assert "High" in labels


def test_build_figure_paletted_raster(make_map, paletted_layer):
    spec = make_map([paletted_layer])
    _, ax = _build_figure(spec)
    assert len(ax.images) > 0
    legend = ax.get_legend()
    assert legend is not None
    labels = [t.get_text() for t in legend.get_texts()]
    assert any("gentle" in lbl.lower() for lbl in labels)
