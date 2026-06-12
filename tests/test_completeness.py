"""Assert all union members are registered in each backend's dispatch dict."""

from typing import get_args

import alidade.dump_qgis as dump_qgis
import alidade.lyrx.build as lyrx_build
import alidade.publish_arcgis as publish_arcgis
import alidade.render_map as render_map
import alidade.render_qgis as render_qgis
from alidade.models import Renderer, RuleRenderer, SingleSymbol, SymbolLayer

SYMBOL_LAYER_TYPES = set(get_args(get_args(SymbolLayer)[0]))
RENDERER_TYPES = set(get_args(get_args(Renderer)[0]))


def test_dispatch_coverage():
    """Verify dispatch dicts for render targets.

    Every SymbolLayer and Renderer union member must have an entry in each
    backend's dispatch dict so that adding a new type to models.py causes an
    immediate failure rather than a silent runtime fall-through.
    """
    assert set(render_qgis.SYMBOL_LAYER_RENDERERS.keys()) == SYMBOL_LAYER_TYPES
    assert set(render_qgis.RENDERERS.keys()) == RENDERER_TYPES
    assert set(render_qgis.RASTER_RENDERERS.keys()) == RENDERER_TYPES

    assert set(lyrx_build.SYMBOL_LAYER_RENDERERS.keys()) == SYMBOL_LAYER_TYPES
    assert set(lyrx_build.RENDERERS.keys()) == RENDERER_TYPES

    assert set(publish_arcgis.SYMBOL_LAYER_RENDERERS.keys()) == SYMBOL_LAYER_TYPES
    assert set(publish_arcgis.RENDERERS.keys()) == RENDERER_TYPES

    assert set(render_map.SYMBOL_LAYER_RENDERERS.keys()) == SYMBOL_LAYER_TYPES
    assert set(render_map.RENDERERS.keys()) == RENDERER_TYPES

    # dump_qgis round-trips only singleSymbol and RuleRenderer;
    # GraduatedRenderer and PalettedRenderer are intentionally excluded.
    assert set(dump_qgis.RENDERER_GENERATORS.keys()) == {SingleSymbol, RuleRenderer}
