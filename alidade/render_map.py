"""Render a Project spec to a static PNG using matplotlib and geopandas."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from PIL import Image

from alidade.models import (
    BoundLayer,
    BoundProject,
    GraduatedRenderer,
    Layer,
    PalettedRenderer,
    RuleRenderer,
    SimpleFill,
    SimpleLine,
    SimpleMarker,
    SingleSymbol,
    SvgMarker,
)
from alidade.util.helpers import bind_project


def _hex_to_rgba(hex_color: str, alpha: int = 255) -> tuple[float, float, float, float]:
    """Convert '#rrggbb' palette hex to matplotlib RGBA tuple (0–1)."""
    h = hex_color.lstrip("#")
    return (
        int(h[0:2], 16) / 255,
        int(h[2:4], 16) / 255,
        int(h[4:6], 16) / 255,
        alpha / 255,
    )


def _raster_bounds(source: Path) -> tuple[float, float, float, float] | None:
    """Return (xmin, ymin, xmax, ymax) for a raster via gdalinfo, or None."""
    try:
        result = subprocess.run(
            ["gdalinfo", "-json", str(source)],
            capture_output=True,
            text=True,
            check=True,
        )
        cc = json.loads(result.stdout)["cornerCoordinates"]
        ul, lr = cc["upperLeft"], cc["lowerRight"]
        return ul[0], lr[1], lr[0], ul[1]
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
        r, g, b, a = _hex_to_rgba(entry.color, entry.alpha)
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


def _rgba(color_str: str) -> tuple[float, float, float, float]:
    """Convert 'R,G,B,A' alidade color string to matplotlib RGBA tuple (0–1)."""
    parts = color_str.split(",")[:4]
    r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
    a = int(parts[3]) if len(parts) >= 4 else 255
    return r / 255, g / 255, b / 255, a / 255


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


def _plot_layer(
    ax: Axes, gdf: gpd.GeoDataFrame, layer: Layer, zorder: int = 1
) -> list[mpatches.Patch]:
    """Plot one layer onto ax; return legend patch handles for classified layers."""
    renderer = layer.renderer
    if renderer is None:
        gdf.plot(ax=ax, color=(0.5, 0.5, 0.5, 0.5), zorder=zorder)
        return []

    if isinstance(renderer, SingleSymbol):
        sym = renderer.symbol.layers[0]
        if isinstance(sym, SimpleFill):
            gdf.plot(
                ax=ax,
                facecolor=_rgba(sym.color),
                edgecolor=_rgba(sym.outline_color),
                linewidth=_lw(sym.outline_width),
                zorder=zorder,
            )
        elif isinstance(sym, SimpleLine):
            gdf.plot(
                ax=ax,
                color=_rgba(sym.line_color),
                linewidth=_lw(sym.line_width),
                zorder=zorder,
            )
        elif isinstance(sym, (SimpleMarker, SvgMarker)):
            gdf.plot(
                ax=ax, color=_rgba(sym.color), markersize=_ms(sym.size), zorder=zorder
            )
        return []

    if isinstance(renderer, GraduatedRenderer):
        ec = _rgba(renderer.outline_color)
        lw = _lw(renderer.outline_width)
        col = renderer.attr
        handles: list[mpatches.Patch] = []
        assigned = pd.Series(False, index=gdf.index)
        for r in renderer.ranges:
            mask = (~assigned) & (gdf[col] >= r.lower) & (gdf[col] <= r.upper)
            fc = _rgba(r.color)
            subset = gdf[mask]
            if not subset.empty:
                subset.plot(
                    ax=ax, facecolor=fc, edgecolor=ec, linewidth=lw, zorder=zorder
                )
            handles.append(mpatches.Patch(facecolor=fc, edgecolor=ec, label=r.label))
            assigned = assigned | mask
        return handles

    if isinstance(renderer, RuleRenderer):
        handles = []
        for rule in renderer.rules:
            if not rule.active:
                continue
            sym = renderer.symbols[rule.symbol_index].layers[0]
            if rule.filter:
                try:
                    subset = gdf[  # type: ignore[assignment]
                        gdf.eval(_qgis_to_pandas_expr(rule.filter))
                    ]
                except Exception as exc:
                    print(f"  rule filter {rule.filter!r} failed: {exc}")
                    continue
            else:
                subset = gdf
            if subset.empty:
                continue
            if isinstance(sym, SimpleFill):
                fc = _rgba(sym.color)
                ec = _rgba(sym.outline_color)
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
                    color=_rgba(sym.line_color),
                    linewidth=_lw(sym.line_width),
                    zorder=zorder,
                )
            elif isinstance(sym, (SimpleMarker, SvgMarker)):
                subset.plot(
                    ax=ax,
                    color=_rgba(sym.color),
                    markersize=_ms(sym.size),
                    zorder=zorder,
                )
                handles.append(
                    mpatches.Patch(facecolor=_rgba(sym.color), label=rule.label)
                )
        return handles

    return []


def render(
    spec: BoundProject,
    name: str = "map",
    dpi: int = 150,
) -> None:
    """Render spec to spec.output_path/<name>.png.

    Layers are drawn bottom-to-top (spec.layers reversed). WMS/raster layers
    and PrintLayout are ignored. Extent and figsize are derived from the data
    bounds so all visible features fit without clipping.
    """
    # Read all visible layers to compute the combined data extent.
    # Each entry is (layer, gdf) for vector or (layer, Path) for raster.
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
        xmin, ymin, xmax, ymax = spec.extent
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

    output_path = spec.output_path / f"{name}.png"
    output_path.parent.mkdir(exist_ok=True, parents=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {output_path}")


def main() -> None:
    """CLI entry point: render map.png for a project directory."""
    parser = argparse.ArgumentParser(description="Render map.png for a project.")
    parser.add_argument("project_dir", help="Path to project directory")
    args = parser.parse_args()
    project_dir = (Path.cwd() / args.project_dir).resolve()
    if not (project_dir / "project.py").exists():
        print(f"project.py not found in {project_dir}")
        sys.exit(1)
    render(bind_project(project_dir))
