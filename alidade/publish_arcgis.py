"""Publish alidade project layers to ArcGIS Online."""

import argparse
import importlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

import geopandas as gpd
from arcgis.features import FeatureLayerCollection
from arcgis.gis import GIS, ItemProperties, ItemTypeEnum
from arcgis.raster.analytics import copy_raster

from alidade.models import (
    BoundLayer,
    BoundProject,
    GraduatedRenderer,
    PalettedRenderer,
    RuleRenderer,
    SimpleFill,
    SimpleLine,
    SimpleMarker,
    SingleSymbol,
    SvgMarker,
    Symbol,
)

_REPO_ROOT = Path(__file__).parent.parent
_LOCAL_ENV = _REPO_ROOT / "local.env"
_ARCGIS_JSON = _REPO_ROOT / "local.arcgis.json"
_ARCGIS_TAG = "alidade"
_MM_TO_PT = 2.835

# ── Config ────────────────────────────────────────────────────────────────────


def _read_local_env(path: Path) -> dict[str, str]:
    """Parse Makefile-style env file (KEY := VALUE or KEY = VALUE)."""
    result: dict[str, str] = {}
    if not path.exists():
        return result
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:?=\s*(.*)", line)
        if m:
            result[m.group(1)] = m.group(2).strip()
    return result


def _load_item_registry(path: Path) -> dict[str, dict]:
    """Load layer-to-item-ID mapping from local.arcgis.json."""
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_registry(path: Path, registry: dict[str, dict]) -> None:
    """Write registry atomically via a temp file."""
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(registry, indent=2))
    tmp.rename(path)


# ── Color / size ──────────────────────────────────────────────────────────────


def _color_to_arcgis(color_str: str) -> list[int]:
    """Convert 'R,G,B[,A]' or '#rrggbb' to [R, G, B, A]."""
    s = color_str.strip()
    if s.startswith("#"):
        h = s.lstrip("#")
        return [int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255]
    parts = [int(x.strip()) for x in s.split(",")]
    return parts if len(parts) == 4 else parts + [255]


def _mm_to_pt(mm: float) -> float:
    return round(mm * _MM_TO_PT, 1)


# ── Symbol translation ────────────────────────────────────────────────────────

_MARKER_STYLES: dict[str, str] = {
    "circle": "esriSMSCircle",
    "square": "esriSMSSquare",
    "diamond": "esriSMSDiamond",
    "triangle": "esriSMSTriangle",
    "cross": "esriSMSCross",
    "x": "esriSMSX",
}


def _sym_layer_to_arcgis(sym_layer: Any) -> dict[str, Any]:
    if isinstance(sym_layer, SimpleFill):
        return {
            "type": "esriSFS",
            "style": "esriSFSSolid",
            "color": _color_to_arcgis(sym_layer.color),
            "outline": {
                "type": "esriSLS",
                "style": "esriSLSSolid",
                "color": _color_to_arcgis(sym_layer.outline_color),
                "width": _mm_to_pt(sym_layer.outline_width),
            },
        }
    if isinstance(sym_layer, SimpleLine):
        return {
            "type": "esriSLS",
            "style": "esriSLSSolid",
            "color": _color_to_arcgis(sym_layer.line_color),
            "width": _mm_to_pt(sym_layer.line_width),
        }
    if isinstance(sym_layer, SimpleMarker):
        style = _MARKER_STYLES.get(sym_layer.name)
        if style is None:
            print(
                f"  Warning: unknown marker shape {sym_layer.name!r}, " "using circle"
            )
            style = "esriSMSCircle"
        return {
            "type": "esriSMS",
            "style": style,
            "color": _color_to_arcgis(sym_layer.color),
            "size": _mm_to_pt(sym_layer.size),
            "outline": {
                "type": "esriSLS",
                "style": "esriSLSSolid",
                "color": _color_to_arcgis(sym_layer.outline_color),
                "width": _mm_to_pt(sym_layer.outline_width),
            },
        }
    if isinstance(sym_layer, SvgMarker):
        print(
            f"  Warning: SvgMarker {sym_layer.name!r} not portable to ArcGIS; "
            "using circle fallback"
        )
        return {
            "type": "esriSMS",
            "style": "esriSMSCircle",
            "color": _color_to_arcgis(sym_layer.color),
            "size": _mm_to_pt(sym_layer.size),
            "outline": {
                "type": "esriSLS",
                "style": "esriSLSSolid",
                "color": _color_to_arcgis(sym_layer.outline_color),
                "width": _mm_to_pt(sym_layer.outline_width),
            },
        }
    raise TypeError(f"Unknown symbol layer type: {type(sym_layer).__name__}")


def _symbol_to_arcgis(symbol: Symbol) -> dict[str, Any]:
    if len(symbol.layers) > 1:
        print(
            f"  Warning: symbol has {len(symbol.layers)} layers; "
            "only the first is translated"
        )
    return _sym_layer_to_arcgis(symbol.layers[0])


# ── Filter parsing ────────────────────────────────────────────────────────────

_EQ_RE = re.compile(r'^"([^"]+)"\s*=\s*(?:\'([^\']*)\'|(\S+))$')
_CMP_RE = re.compile(r"[><!]")


def _parse_equality(expr: str) -> tuple[str, str] | None:
    """Parse '"field" = value' → (field, value_str), or None."""
    m = _EQ_RE.match(expr.strip())
    if not m:
        return None
    return m.group(1), m.group(2) if m.group(2) is not None else m.group(3)


def _classify_filter(
    filter_expr: str,
) -> tuple[str, list[tuple[str, str]]]:
    """
    Classify a QGIS rule filter expression.

    Returns (kind, pairs) where kind is one of:
      'equality' — single "field" = value
      'or'       — two or more "field" = value joined by OR
      'catchall' — comparison operator (>=, <=, >, <, !=) or empty
      'unknown'  — unrecognised pattern; caller should warn and skip
    """
    if not filter_expr or not filter_expr.strip():
        return "catchall", []
    parts = re.split(r"\s+OR\s+", filter_expr.strip(), flags=re.IGNORECASE)
    pairs = [_parse_equality(p) for p in parts]
    if all(p is not None for p in pairs):
        kind = "equality" if len(pairs) == 1 else "or"
        return kind, [p for p in pairs if p is not None]
    if _CMP_RE.search(filter_expr):
        return "catchall", []
    return "unknown", []


# ── Renderer translation ──────────────────────────────────────────────────────


def _renderer_to_arcgis(
    renderer: Any, geometry_type: str | None
) -> dict[str, Any] | None:
    """Translate an alidade renderer to an ArcGIS REST drawingInfo renderer."""
    if isinstance(renderer, SingleSymbol):
        return {"type": "simple", "symbol": _symbol_to_arcgis(renderer.symbol)}

    if isinstance(renderer, GraduatedRenderer):
        is_line = geometry_type in ("LineString", "MultiLineString")
        outline = {
            "type": "esriSLS",
            "style": "esriSLSSolid",
            "color": _color_to_arcgis(renderer.outline_color),
            "width": _mm_to_pt(renderer.outline_width),
        }
        infos = []
        for rng in renderer.ranges:
            sym: dict[str, Any] = {
                "type": "esriSLS" if is_line else "esriSFS",
                "style": "esriSLSSolid" if is_line else "esriSFSSolid",
                "color": _color_to_arcgis(rng.color),
            }
            if not is_line:
                sym["outline"] = outline
            infos.append(
                {
                    "classMinValue": rng.lower,
                    "classMaxValue": rng.upper,
                    "label": rng.label,
                    "symbol": sym,
                }
            )
        return {
            "type": "classBreaks",
            "field": renderer.attr,
            "classificationMethod": "esriClassifyManual",
            "classBreakInfos": infos,
        }

    if isinstance(renderer, RuleRenderer):
        field1: str | None = None
        uv_infos: list[dict[str, Any]] = []
        default_symbol: dict[str, Any] | None = None
        default_label = ""

        for rule in renderer.rules:
            if not rule.active:
                continue
            sym = _symbol_to_arcgis(renderer.symbols[rule.symbol_index])
            kind, pairs = _classify_filter(rule.filter)

            if kind in ("equality", "or"):
                if field1 is None and pairs:
                    field1 = pairs[0][0]
                for _, value in pairs:
                    uv_infos.append(
                        {"value": value, "label": rule.label, "symbol": sym}
                    )
            elif kind == "catchall":
                if default_symbol is not None:
                    print(
                        f"  Warning: multiple catch-all rules in "
                        f"{renderer.rules_key!r}; using last"
                    )
                default_symbol = sym
                default_label = rule.label
            else:
                print(
                    f"  Warning: skipping rule with unparseable filter: "
                    f"{rule.filter!r}"
                )

        result: dict[str, Any] = {
            "type": "uniqueValue",
            "field1": field1 or renderer.rules_key,
            "uniqueValueInfos": uv_infos,
        }
        if default_symbol is not None:
            result["defaultSymbol"] = default_symbol
            result["defaultLabel"] = default_label
        return result

    if isinstance(renderer, PalettedRenderer):
        print(
            "  Note: PalettedRenderer (raster) — "
            "set symbology manually in Map Viewer"
        )
        return None

    return None


# ── Data preparation ──────────────────────────────────────────────────────────


def _zip_shp(shp_path: Path) -> Path:
    """Zip .shp and sidecar files; return path to the .zip."""
    base = shp_path.with_suffix("")
    zip_path = base.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w") as z:
        for ext in (".shp", ".shx", ".dbf", ".prj", ".cpg"):
            candidate = base.with_suffix(ext)
            if candidate.exists():
                z.write(candidate, candidate.name)
    return zip_path


# Polygon/MultiPolygon etc. are the same "family" for type filtering.
_GEOM_FAMILIES: dict[str, set[str]] = {
    "Polygon": {"Polygon", "MultiPolygon"},
    "MultiPolygon": {"Polygon", "MultiPolygon"},
    "LineString": {"LineString", "MultiLineString"},
    "MultiLineString": {"LineString", "MultiLineString"},
    "Point": {"Point", "MultiPoint"},
    "MultiPoint": {"Point", "MultiPoint"},
}


def _filter_geometry_type(
    gdf: gpd.GeoDataFrame, geometry_type: str, layer_id: str
) -> gpd.GeoDataFrame:
    """Drop features whose geometry type doesn't belong to the expected family."""
    allowed = _GEOM_FAMILIES.get(geometry_type, {geometry_type})
    before = len(gdf)
    gdf = gdf[gdf.geom_type.isin(allowed)].copy()
    dropped = before - len(gdf)
    if dropped:
        print(
            f"    {layer_id}: dropped {dropped} non-{geometry_type} "
            "feature(s) (mixed geometry from clip/dissolve)"
        )
    return gdf


def _prepare_vector(layer: BoundLayer, publish_dir: Path) -> Path:
    """Reproject layer to EPSG:4326, write to publish_dir, return upload path."""
    publish_dir.mkdir(parents=True, exist_ok=True)
    read_kwargs: dict[str, Any] = {}
    if "|layername=" in layer.datasource:
        read_kwargs["layer"] = layer.datasource.split("|layername=", 1)[1]
    gdf = gpd.read_file(layer.path, **read_kwargs).to_crs(4326)

    if layer.geometry_type:
        gdf = _filter_geometry_type(gdf, layer.geometry_type, layer.id)

    # .shp sources already have ≤10-char field names — keep as shapefile.
    # .gpkg and .geojson sources use GeoJSON to preserve full field names
    # (shapefile's 10-char limit would break renderer field references).
    if layer.path.suffix.lower() == ".shp":
        out_shp = publish_dir / f"{layer.id}.shp"
        gdf.to_file(out_shp)
        return _zip_shp(out_shp)

    out = publish_dir / f"{layer.id}.geojson"
    gdf.to_file(out, driver="GeoJSON")
    return out


def _prepare_raster(layer: BoundLayer, publish_dir: Path) -> Path:
    """Reproject to Web Mercator and build overviews; return path to the .tif."""
    publish_dir.mkdir(parents=True, exist_ok=True)
    dst = publish_dir / f"{layer.id}_3857.tif"
    subprocess.run(
        ["gdalwarp", "-t_srs", "EPSG:3857", str(layer.path), str(dst)],
        check=True,
    )
    subprocess.run(
        ["gdaladdo", "-r", "average", str(dst), "2", "4", "8", "16", "32"],
        check=True,
    )
    return dst


# ── Upload helpers ────────────────────────────────────────────────────────────


def _upload_item(
    root_folder: Any,
    gis: "GIS",
    *,
    title: str,
    item_type: Any,
    upload_path: Path,
) -> Any:
    """Upload a file item, deleting any orphaned duplicate and retrying once.

    ArcGIS returns 409 CONT_0027 when a previous upload with the same filename
    was never deleted (e.g. a crashed run).  Extract the conflicting item ID
    from the error message, delete it, and retry.
    """
    props = ItemProperties(title=title, item_type=item_type, tags=_ARCGIS_TAG)
    try:
        return root_folder.add(item_properties=props, file=str(upload_path)).result()
    except Exception as exc:
        msg = str(exc)
        m = re.search(r"\[itemId=([a-f0-9]{32})\]", msg)
        if "409" not in msg or not m:
            raise
        orphan = gis.content.get(m.group(1))
        if orphan:
            orphan.delete()
            print(f"    Deleted orphaned upload item {m.group(1)}")
        return root_folder.add(item_properties=props, file=str(upload_path)).result()


# ── Publish one layer ─────────────────────────────────────────────────────────


def _publish_layer(
    layer: BoundLayer,
    gis: GIS | None,
    item_registry: dict[str, dict],
    publish_dir: Path,
    *,
    renderer_only: bool,
    dry_run: bool,
) -> float:
    """Prepare and publish one layer. Returns MB of upload file (0 in dry_run)."""
    if layer.provider == "wms" or layer.datasource.startswith("http"):
        print(f"  {layer.id}: skip (tile service)")
        return 0.0

    if not layer.path.exists():
        print(f"  {layer.id}: skip (not built — run make build first)")
        return 0.0

    is_raster = layer.type == "raster"
    ids = item_registry.get(layer.id, {})
    stat = layer.path.stat()

    if (
        not renderer_only
        and ids.get("feature_item_id")
        and ids.get("src_mtime") == stat.st_mtime
        and ids.get("src_size") == stat.st_size
    ):
        print(f"  {layer.id}: skip (unchanged)")
        return 0.0

    upload_path: Path | None = None
    size_mb = 0.0
    if not renderer_only:
        upload_path = (
            _prepare_raster(layer, publish_dir)
            if is_raster
            else _prepare_vector(layer, publish_dir)
        )
        size_mb = upload_path.stat().st_size / 1_048_576
        print(f"  {layer.id}: {upload_path.name}  {size_mb:.2f} MB")

    if dry_run:
        return size_mb

    # ── Upload / overwrite ─────────────────────────────────────────────────
    assert gis is not None
    root_folder = gis.content.folders.get()

    if not renderer_only and upload_path is not None:
        if is_raster:
            # Delete existing imagery layer before replacing — tiled imagery
            # layers cannot be updated in-place, only replaced.
            if ids.get("feature_item_id"):
                old = gis.content.get(ids["feature_item_id"])
                if old:
                    old.delete()
            pub_result = copy_raster(
                input_raster=str(upload_path),
                output_name=layer.name,
                gis=gis,
            )
            # copy_raster returns an Item (arcgis >= 2.x) or ImageryLayer;
            # try both attribute names.
            feature_item_id = getattr(pub_result, "id", None) or getattr(
                pub_result, "itemid", None
            )
            if not feature_item_id:
                raise RuntimeError(
                    f"copy_raster did not return an identifiable item "
                    f"for {layer.name!r}: {pub_result!r}"
                )
            item_registry[layer.id] = {
                "feature_item_id": feature_item_id,
                "src_mtime": stat.st_mtime,
                "src_size": stat.st_size,
            }
            _save_registry(_ARCGIS_JSON, item_registry)
            print(f"    Imagery layer published (feature_item_id={feature_item_id})")
            return size_mb

        # Vector: overwrite existing or publish new
        if ids.get("feature_item_id"):
            item = gis.content.get(ids["feature_item_id"])
            if item:
                FeatureLayerCollection.fromitem(item).manager.overwrite(
                    str(upload_path)
                )
                item_registry[layer.id] = {
                    **ids,
                    "src_mtime": stat.st_mtime,
                    "src_size": stat.st_size,
                }
                _save_registry(_ARCGIS_JSON, item_registry)
                print(f"    Overwrote {ids['feature_item_id']}")
            else:
                print(
                    f"  Warning: feature_item_id={ids['feature_item_id']!r} "
                    "not found in ArcGIS; re-publishing"
                )
                ids = {}

        if not ids.get("feature_item_id"):
            item_type = (
                ItemTypeEnum.SHAPEFILE
                if str(upload_path).endswith(".zip")
                else ItemTypeEnum.GEOJSON
            )
            src_item = _upload_item(
                root_folder,
                gis,
                title=layer.name,
                item_type=item_type,
                upload_path=upload_path,
            )
            pub_item = src_item.publish()
            item_registry[layer.id] = {
                "source_item_id": src_item.id,
                "feature_item_id": pub_item.id,
                "src_mtime": stat.st_mtime,
                "src_size": stat.st_size,
            }
            _save_registry(_ARCGIS_JSON, item_registry)
            print(f"    Published (feature_item_id={pub_item.id})")

    # ── Apply renderer ─────────────────────────────────────────────────────
    if is_raster or layer.renderer is None:
        return size_mb

    fid = item_registry.get(layer.id, {}).get("feature_item_id")
    if not fid:
        return size_mb

    arcgis_renderer = _renderer_to_arcgis(layer.renderer, layer.geometry_type)
    if arcgis_renderer is None:
        return size_mb

    item = gis.content.get(fid)  # type: ignore[union-attr]
    if item:
        flc = FeatureLayerCollection.fromitem(item)
        flc.layers[0].manager.update_definition(
            {"drawingInfo": {"renderer": arcgis_renderer}}
        )
        print(f"    Applied {layer.renderer.kind} renderer")

    return size_mb


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Publish alidade project layers to ArcGIS Online."
    )
    parser.add_argument(
        "project_dir",
        help="Project directory, e.g. projects/goats",
    )
    parser.add_argument(
        "--map",
        dest="map_name",
        default=None,
        help="Map name from the module's maps list (default: spec)",
    )
    parser.add_argument(
        "--renderer-only",
        action="store_true",
        help="Skip data upload; only re-apply renderers to registered layers",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Prepare data files and print what would be uploaded; "
            "skip authentication and all ArcGIS API calls"
        ),
    )
    args = parser.parse_args()

    # Load project — same resolution as bind_project / alidade-build
    project_path = (Path.cwd() / args.project_dir).resolve()
    package = ".".join(project_path.relative_to(_REPO_ROOT).parts)
    module = importlib.import_module(f"{package}.project")

    if args.map_name:
        maps = {m.id: m for m in module.maps}
        if args.map_name not in maps:
            avail = ", ".join(maps)
            print(
                f"Error: map {args.map_name!r} not found. Available: {avail}",
                file=sys.stderr,
            )
            sys.exit(1)
        spec = maps[args.map_name]
    else:
        spec = module.spec
    bound = BoundProject(**spec.model_dump(mode="python"), project_path=project_path)
    publish_dir = project_path / "publish"

    print(f"Project: {spec.title!r}  ({len(spec.layers)} layers)")
    if args.dry_run:
        print("Dry run — preparing files only, no ArcGIS API calls")

    # Item registry
    item_registry = _load_item_registry(_ARCGIS_JSON)
    print(
        f"Item registry ({_ARCGIS_JSON.name}): "
        f"{len(item_registry)} layer(s) registered"
    )

    # Authenticate (skipped in dry_run)
    gis: GIS | None = None
    if not args.dry_run:
        env = _read_local_env(_LOCAL_ENV)
        client_id = env.get("ARCGIS_CLIENT_ID")
        url = env.get("ARGIS_URL", "https://www.arcgis.com")
        if not client_id:
            print(
                "Error: ARCGIS_CLIENT_ID not set in local.env. "
                "Add: ARCGIS_CLIENT_ID := <your-app-id>",
                file=sys.stderr,
            )
            sys.exit(1)
        print("Authenticating…")
        gis = GIS(url, client_id=client_id)
        me = gis.users.me
        print(f"  OK — signed in as {me.username} ({me.fullName})")

        # Verify registered item IDs
        if item_registry:
            print("Verifying registered items:")
            for layer_id, ids in item_registry.items():
                fid = ids.get("feature_item_id", "")
                item = gis.content.get(fid) if fid else None
                if item:
                    print(f"  {layer_id}: OK ({item.title})")
                else:
                    print(f"  {layer_id}: NOT FOUND (feature_item_id={fid!r})")

    # Publish layers
    total_mb = 0.0
    layer_errors: list[tuple[str, str]] = []
    for layer in bound.bound_layers:
        try:
            total_mb += _publish_layer(
                layer,
                gis,
                item_registry,
                publish_dir,
                renderer_only=args.renderer_only,
                dry_run=args.dry_run,
            )
        except Exception as exc:
            layer_errors.append((layer.id, str(exc)))
            print(f"  {layer.id}: ERROR — {exc}")

    if total_mb:
        print(f"Total upload size: {total_mb:.2f} MB")

    if layer_errors:
        print(f"\n{len(layer_errors)} layer(s) failed:")
        for layer_id, msg in layer_errors:
            print(f"  {layer_id}: {msg}")

    if not args.dry_run:
        print("Done." if not layer_errors else "Done (with errors above).")

    if layer_errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
