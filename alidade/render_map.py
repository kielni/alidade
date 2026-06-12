"""Render a Map spec to a static PNG using matplotlib and geopandas."""

import argparse
import re
import sys
from pathlib import Path

import rasterio

import geopandas as gpd
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from PIL import Image

from alidade.color import Color
from alidade.models import (
    BoundLayer,
    BoundMap,
    GraduatedRenderer,
    Label,
    Layer,
    PalettedRenderer,
    RuleRenderer,
    SimpleFill,
    SimpleLine,
    SimpleMarker,
    SingleSymbol,
    SvgMarker,
)
from alidade.util.helpers import bind_map, load_map_module

# ── Dispatch tables (importable by test_completeness) ─────────────────────────

RENDERERS: dict[type, None] = {
    SingleSymbol: None,
    GraduatedRenderer: None,
    RuleRenderer: None,
    PalettedRenderer: None,
}

SYMBOL_LAYER_RENDERERS: dict[type, None] = {
    SimpleFill: None,
    SimpleLine: None,
    SimpleMarker: None,
    SvgMarker: None,
}


def _raster_bounds(source: Path) -> tuple[float, float, float, float] | None:
    """Return (xmin, ymin, xmax, ymax) for a raster, or None."""
    try:
        with rasterio.open(source) as ds:
            b = ds.bounds
            return b.left, b.bottom, b.right, b.top
    except Exception:
        return None


def _plot_paletted_raster(
    ax: Axes, source: Path, renderer: PalettedRenderer, zorder: int = 1
) -> list[mpatches.Patch]:
    """Render a PalettedRenderer raster onto ax; return legend patches."""
    bounds = _raster_bounds(source)
    if bounds is None:
        return []
    xmin, ymin, xmax, ymax = bounds
    arr = np.array(Image.open(source))
    rgba = np.zeros((*arr.shape, 4), dtype=np.float32)
    handles: list[mpatches.Patch] = []
    for entry in renderer.entries:
        mask = arr == entry.value
        r, g, b, a = entry.color.matplotlib_rgba
        rgba[mask] = (r, g, b, a)
        handles.append(mpatches.Patch(facecolor=(r, g, b, 1.0), label=entry.label))
    ax.imshow(
        rgba,
        extent=(xmin, xmax, ymin, ymax),
        aspect="auto",
        origin="upper",
        zorder=zorder,
    )
    return handles


def _qgis_to_pandas_expr(expr: str) -> str:
    """Translate a QGIS filter expression string to a pandas eval() expression.

    Handles double-quoted field names, bare = equality, AND/OR keywords.
    """
    result = re.sub(r'"(\w+)"', r"\1", expr)
    result = re.sub(r"(?<![<>!])=(?!=)", "==", result)
    return result.replace(" AND ", " and ").replace(" OR ", " or ")


def _lw(mm: float) -> float:
    """Approximate QGIS outline width in MM to matplotlib linewidth in points."""
    return mm * 1.5


def _ms(mm: float) -> float:
    """Approximate QGIS marker size in MM to matplotlib scatter size in pt²."""
    return (mm * 2.8) ** 2


_LABEL_SCALE = 0.5  # QGIS pt → matplotlib pt; compensates for smaller figure size


def _font_available(family: str) -> bool:
    """Return True if matplotlib can resolve family without falling back."""
    path = fm.findfont(fm.FontProperties(family=family), fallback_to_default=True)
    return fm.FontProperties(fname=path).get_name().lower() == family.lower()


def _plot_labels(ax: Axes, gdf: gpd.GeoDataFrame, label: Label, zorder: int) -> None:
    """Annotate point features with text labels from a Layer's Label spec."""
    weight = "bold" if label.bold else "normal"
    offset_pt = label.y_offset * 2.8
    for _, row in gdf.iterrows():
        geom = row.geometry
        if geom is None:
            continue
        pt = geom.centroid
        text = str(row[label.field]) if label.field in row.index else ""
        if not text or text == "nan":
            continue
        kwargs: dict = {}
        if _font_available(label.font_family):
            kwargs["fontfamily"] = label.font_family
        ann = ax.annotate(
            text,
            xy=(pt.x, pt.y),
            xytext=(0, offset_pt),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=label.font_size * _LABEL_SCALE,
            fontweight=weight,
            color=label.color.matplotlib_rgba,
            zorder=zorder,
            **kwargs,
        )
        if label.halo_color is not None:
            ann.set_path_effects(
                [
                    pe.withStroke(
                        linewidth=label.halo_size,
                        foreground=label.halo_color.matplotlib_rgba,
                    )
                ]
            )


def _plot_layer(
    ax: Axes, gdf: gpd.GeoDataFrame, layer: Layer, zorder: int = 1
) -> list[mpatches.Patch]:
    """Plot one layer onto ax; return legend patch handles for classified layers."""
    renderer = layer.renderer
    handles: list[mpatches.Patch] = []

    if renderer is None:
        gdf.plot(ax=ax, color=Color(128, 128, 128, 128).matplotlib_rgba, zorder=zorder)

    elif isinstance(renderer, SingleSymbol):
        sym = renderer.symbol.layers[0]
        if isinstance(sym, SimpleFill):
            gdf.plot(
                ax=ax,
                facecolor=sym.color.matplotlib_rgba,
                edgecolor=sym.outline_color.matplotlib_rgba,
                linewidth=_lw(sym.outline_width),
                zorder=zorder,
            )
        elif isinstance(sym, SimpleLine):
            gdf.plot(
                ax=ax,
                color=sym.line_color.matplotlib_rgba,
                linewidth=_lw(sym.line_width),
                zorder=zorder,
            )
        elif isinstance(sym, (SimpleMarker, SvgMarker)):
            gdf.plot(
                ax=ax,
                color=sym.color.matplotlib_rgba,
                markersize=_ms(sym.size),
                zorder=zorder,
            )

    elif isinstance(renderer, GraduatedRenderer):
        ec = renderer.outline_color.matplotlib_rgba
        lw = _lw(renderer.outline_width)
        col = renderer.attr
        assigned = pd.Series(False, index=gdf.index)
        for r in renderer.ranges:
            mask = (~assigned) & (gdf[col] >= r.lower) & (gdf[col] <= r.upper)
            fc = r.color.matplotlib_rgba
            subset = gdf[mask]
            if not subset.empty:
                subset.plot(
                    ax=ax, facecolor=fc, edgecolor=ec, linewidth=lw, zorder=zorder
                )
            handles.append(mpatches.Patch(facecolor=fc, edgecolor=ec, label=r.label))
            assigned = assigned | mask

    elif isinstance(renderer, RuleRenderer):
        matched = pd.Series(False, index=gdf.index)
        for rule in renderer.rules:
            if not rule.active:
                continue
            sym = renderer.symbols[rule.symbol_index].layers[0]
            if rule.filter == "ELSE":
                subset = gdf[~matched]  # type: ignore[assignment]
            elif rule.filter:
                try:
                    mask = gdf.eval(  # type: ignore[assignment]
                        _qgis_to_pandas_expr(rule.filter)
                    )
                    matched = matched | mask
                    subset = gdf[mask]  # type: ignore[assignment]
                except Exception as exc:
                    print(f"  rule filter {rule.filter!r} failed: {exc}")
                    continue
            else:
                subset = gdf
            if subset.empty:
                continue
            if isinstance(sym, SimpleFill):
                fc = sym.color.matplotlib_rgba
                ec = sym.outline_color.matplotlib_rgba
                subset.plot(
                    ax=ax,
                    facecolor=fc,
                    edgecolor=ec,
                    linewidth=_lw(sym.outline_width),
                    zorder=zorder,
                )
                handles.append(
                    mpatches.Patch(facecolor=fc, edgecolor=ec, label=rule.label)
                )
            elif isinstance(sym, SimpleLine):
                subset.plot(
                    ax=ax,
                    color=sym.line_color.matplotlib_rgba,
                    linewidth=_lw(sym.line_width),
                    zorder=zorder,
                )
            elif isinstance(sym, (SimpleMarker, SvgMarker)):
                subset.plot(
                    ax=ax,
                    color=sym.color.matplotlib_rgba,
                    markersize=_ms(sym.size),
                    zorder=zorder,
                )
                handles.append(
                    mpatches.Patch(
                        facecolor=sym.color.matplotlib_rgba, label=rule.label
                    )
                )

    if layer.label is not None:
        _plot_labels(ax, gdf, layer.label, zorder=zorder + 1)

    return handles


def _build_figure(spec: BoundMap) -> tuple[plt.Figure, Axes]:
    """Construct and return a (Figure, Axes) for spec without saving or closing.

    Layers are drawn bottom-to-top (spec.layers reversed). WMS/raster layers
    and PrintLayout are ignored. Extent and figsize are derived from the data
    bounds so all visible features fit without clipping.
    """
    layers_data: list[tuple[BoundLayer, gpd.GeoDataFrame | Path]] = []
    xmins, ymins, xmaxs, ymaxs = [], [], [], []
    for layer in reversed(spec.bound_layers):
        if not layer.visible:
            continue
        if layer.provider == "wms":
            continue
        source = layer.path
        if layer.type == "raster":
            bounds = _raster_bounds(source)
            if bounds is None:
                print(f"  skip {layer.name!r}: could not read raster bounds")
                continue
            xmins.append(bounds[0])
            ymins.append(bounds[1])
            xmaxs.append(bounds[2])
            ymaxs.append(bounds[3])
            layers_data.append((layer, source))
        else:
            try:
                gdf = gpd.read_file(source)
            except Exception as exc:
                print(f"  skip {layer.name!r}: {exc}")
                continue
            if gdf.crs is not None:
                gdf = gdf.to_crs(spec.crs)
            b = gdf.total_bounds  # [xmin, ymin, xmax, ymax]
            xmins.append(b[0])
            ymins.append(b[1])
            xmaxs.append(b[2])
            ymaxs.append(b[3])
            layers_data.append((layer, gdf))

    if xmins:
        xmin, ymin = min(xmins), min(ymins)
        xmax, ymax = max(xmaxs), max(ymaxs)
        pad_x = (xmax - xmin) * 0.05
        pad_y = (ymax - ymin) * 0.05
        xmin -= pad_x
        xmax += pad_x
        ymin -= pad_y
        ymax += pad_y
    elif spec.extent:
        xmin, ymin, xmax, ymax = spec.extent.as_tuple()
    else:
        xmin, ymin, xmax, ymax = 0.0, 0.0, 1.0, 1.0

    data_w, data_h = xmax - xmin, ymax - ymin
    aspect = data_w / data_h
    figsize: tuple[float, float] = (
        (10.0, 10.0 / aspect) if aspect >= 1 else (10.0 * aspect, 10.0)
    )

    fig, ax = plt.subplots(figsize=figsize)
    ax.axis("off")
    ax.patch.set_visible(True)
    legend_handles: list[mpatches.Patch] = []

    for i, (layer, data) in enumerate(layers_data):
        zorder = i + 1
        if layer.type == "raster" and isinstance(layer.renderer, PalettedRenderer):
            assert isinstance(data, Path)
            legend_handles.extend(
                _plot_paletted_raster(ax, data, layer.renderer, zorder=zorder)
            )
        elif isinstance(data, gpd.GeoDataFrame):
            legend_handles.extend(_plot_layer(ax, data, layer, zorder=zorder))

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_title(spec.title, fontsize=14, pad=10)
    if legend_handles:
        ax.legend(handles=legend_handles, loc="upper left", fontsize=8)

    return fig, ax


def render(
    spec: BoundMap,
    name: str = "map",
    dpi: int = 150,
) -> None:
    """Render spec to spec.output_path/<name>.png."""
    fig, _ = _build_figure(spec)
    output_path = spec.output_path / f"{name}.png"
    output_path.parent.mkdir(exist_ok=True, parents=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {output_path}")


def main() -> None:
    """CLI entry point: render map PNG(s) for a map directory."""
    parser = argparse.ArgumentParser(description="Render map PNG(s) for a map.")
    parser.add_argument("map_dir", help="Path to map directory")
    parser.add_argument(
        "--map",
        dest="map_id",
        default=None,
        help="Render one named map by ID (default: render all maps)",
    )
    args = parser.parse_args()
    map_path = (Path.cwd() / args.map_dir).resolve()
    module = load_map_module(map_path)

    map_specs = getattr(module, "maps", [])
    if args.map_id:
        map_specs = [m for m in map_specs if m.id == args.map_id]
        if not map_specs:
            print(f"Map {args.map_id!r} not found", file=sys.stderr)
            sys.exit(1)

    if map_specs:
        for spec in map_specs:
            bound = BoundMap(**spec.model_dump(mode="python"), map_path=map_path)
            render(bound, f"map_{spec.id}")
    else:
        render(bind_map(map_path))
