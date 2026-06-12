"""Publish alidade map layers to ArcGIS Online."""

import argparse
import importlib
import json
import re
import subprocess
import sys
import uuid
import zipfile
from pathlib import Path
from typing import Any

import geopandas as gpd
import rasterio
import rasterio.features
from arcgis.apps.storymap import StoryMap
from pyproj import Transformer
from arcgis.apps.storymap import _utils as _sm_utils
from arcgis.features import FeatureLayerCollection
from arcgis.gis import GIS, ItemProperties, ItemTypeEnum
from arcgis.raster.analytics import copy_raster

from alidade.color import Color
from alidade.models import (
    BoundLayer,
    BoundMap,
    Extent,
    GraduatedRenderer,
    Label,
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


def _color_to_arcgis(color: Color) -> list[int]:
    """Convert a Color to [R, G, B, A].

    Stays here rather than on Color: the [R, G, B, A] list is the
    ArcGIS REST API color format, not a generic representation.
    """
    return [color.r, color.g, color.b, color.a]


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
    if not filter_expr or filter_expr.strip().upper() == "ELSE":
        return "catchall", []
    parts = re.split(r"\s+OR\s+", filter_expr.strip(), flags=re.IGNORECASE)
    pairs = [_parse_equality(p) for p in parts]
    if all(p is not None for p in pairs):
        kind = "equality" if len(pairs) == 1 else "or"
        return kind, [p for p in pairs if p is not None]
    if _CMP_RE.search(filter_expr):
        return "catchall", []
    return "unknown", []


# ── Label translation ────────────────────────────────────────────────────────


def _build_labeling_info(label: Label) -> dict[str, Any]:
    """Build an ArcGIS REST labelingInfo entry for a Label spec."""
    weight = "bold" if label.bold else "normal"
    return {
        "labelExpression": f"[{label.field}]",
        "labelExpressionInfo": {"expression": f'$feature["{label.field}"]'},
        "useCodedValues": True,
        "maxScale": 0,
        "minScale": 0,
        "where": None,
        "labelPlacement": "esriServerPointLabelPlacementAboveRight",
        "symbol": {
            "type": "esriTS",
            "color": _color_to_arcgis(label.color),
            "haloColor": (
                _color_to_arcgis(label.halo_color)
                if label.halo_color is not None
                else None
            ),
            "haloSize": label.halo_size if label.halo_color is not None else None,
            "font": {
                "family": label.font_family,
                "size": label.font_size,
                "style": "normal",
                "weight": weight,
                "decoration": "none",
            },
        },
    }


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
        uv_infos = []
        for entry in renderer.entries:
            entry_sym: dict[str, Any] = {
                "type": "esriSFS",
                "style": "esriSFSSolid",
                "color": _color_to_arcgis(entry.color),
                "outline": {
                    "type": "esriSLS",
                    "style": "esriSLSNull",
                    "color": [0, 0, 0, 0],
                    "width": 0,
                },
            }
            uv_infos.append(
                {
                    "value": str(entry.value),
                    "label": entry.label,
                    "symbol": entry_sym,
                }
            )
        return {
            "type": "uniqueValue",
            "field1": "value",
            "uniqueValueInfos": uv_infos,
        }

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


def _vectorize_raster(layer: BoundLayer, publish_dir: Path) -> Path:
    """Polygonize a PalettedRenderer raster; return a GeoJSON in EPSG:4326.

    Uses rasterio.features.shapes so GDAL polygonize is not required.  Adjacent
    pixels of the same class value are dissolved into single multipolygons.
    """
    publish_dir.mkdir(parents=True, exist_ok=True)
    with rasterio.open(layer.path) as src:
        data = src.read(1)
        transform = src.transform
        crs = src.crs
        nodata = int(src.nodata or 0)
    mask = (data != nodata).astype("uint8")
    features = [
        {"type": "Feature", "geometry": geom, "properties": {"value": int(val)}}
        for geom, val in rasterio.features.shapes(data, mask=mask, transform=transform)
        if int(val) != nodata
    ]
    gdf = gpd.GeoDataFrame.from_features(features, crs=crs)
    gdf = gdf.dissolve(by="value", as_index=False).to_crs(4326)
    dst = publish_dir / f"{layer.id}.geojson"
    gdf.to_file(dst, driver="GeoJSON")
    return dst


def _prepare_raster(layer: BoundLayer, publish_dir: Path) -> Path:
    """Reproject to Web Mercator and build overviews; return path to the .tif."""
    publish_dir.mkdir(parents=True, exist_ok=True)
    dst = publish_dir / f"{layer.id}_3857.tif"
    subprocess.run(
        ["gdalwarp", "-overwrite", "-t_srs", "EPSG:3857", str(layer.path), str(dst)],
        check=True,
    )
    subprocess.run(
        ["gdaladdo", "-r", "nearest", str(dst), "2", "4", "8", "16", "32"],
        check=True,
    )
    return dst


# ── Upload helpers ────────────────────────────────────────────────────────────


def _delete_service(item: Any) -> None:
    """Rename a feature service to a hex-suffixed title before deleting it.

    ArcGIS Online does not immediately release a service name on delete; the
    name stays reserved until the item is renamed away from it first.  Using
    the original title plus a unique suffix (rather than a fixed prefix) keeps
    the reserved name distinct from new publishes, which also use
    {layer_id}_{hex} naming.
    """
    item.update(item_properties={"title": f"{item.title}_{uuid.uuid4().hex[:8]}"})
    item.delete()


def _publish_src_item(src_item: Any, layer_id: str, layer_name: str) -> Any:
    """Publish a source item using a UUID-suffixed service name, then rename the
    item title to the human-readable layer name.

    A unique service name avoids conflicts with stale names reserved by
    ArcGIS Online's soft-delete behaviour (delete does not immediately release
    the service name).
    """
    service_name = f"{layer_id}_{uuid.uuid4().hex[:8]}"
    pub_item = src_item.publish(publish_parameters={"name": service_name})
    if pub_item.title != layer_name:
        pub_item.update(item_properties={"title": layer_name})
    return pub_item


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
    """Prepare and publish one layer. Returns MB of upload file."""
    if layer.provider == "wms" or layer.datasource.startswith("http"):
        print(f"  {layer.id}: skip (tile service)")
        return 0.0

    if not layer.path.exists():
        print(f"  {layer.id}: skip (not built — run make build first)")
        return 0.0

    # Paletted rasters are published as polygon feature layers so that the
    # legend can show class labels instead of a 256-entry color table.
    is_raster = layer.type == "raster" and not isinstance(
        layer.renderer, PalettedRenderer
    )
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
        if is_raster:
            upload_path = _prepare_raster(layer, publish_dir)
        elif layer.type == "raster":
            upload_path = _vectorize_raster(layer, publish_dir)
        else:
            upload_path = _prepare_vector(layer, publish_dir)
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
            # layers cannot be updated in-place, only replaced.  Also search by
            # title to catch items the registry no longer tracks (e.g. manually
            # deleted and re-attempted, or registry entry cleared).
            known_id = ids.get("feature_item_id")
            if known_id:
                old = gis.content.get(known_id)
                if old:
                    _delete_service(old)
                    print(f"    Deleted existing item {known_id}")
            else:
                hits = gis.content.search(
                    f'title:"{layer.name}" type:"Image Service"',
                    max_items=10,
                )
                for hit in hits:
                    if hit.title == layer.name:
                        _delete_service(hit)
                        print(f"    Deleted stale image service {hit.id}")
            raster_context: dict[str, Any] | None = None
            if isinstance(layer.renderer, PalettedRenderer):
                # Single-band: value 0 is nodata (transparent).
                raster_context = {"noData": "0"}
            service_name = f"{layer.id}_{uuid.uuid4().hex[:8]}"
            pub_result = copy_raster(
                input_raster=str(upload_path),
                output_name=service_name,
                context=raster_context,
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
            # copy_raster uses output_name as the service name and item title;
            # rename the item to the human-readable layer name.
            raster_item = gis.content.get(feature_item_id)
            if raster_item and raster_item.title != layer.name:
                raster_item.update(item_properties={"title": layer.name})
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
            if item and "Feature" not in item.type:
                # Registered item is an image service (e.g. previous raster
                # publish); delete it so we can replace with a feature layer.
                _delete_service(item)
                print(f"    Deleted old {item.type} (replacing with feature layer)")
                ids = {}
                item = None
            if item:
                try:
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
                except Exception as exc:
                    if "name and extension" not in str(exc):
                        raise
                    # File format changed (e.g. shapefile → GeoJSON); delete
                    # the existing item and fall through to re-publish below.
                    print(
                        f"    Format mismatch; deleting "
                        f"{ids['feature_item_id']} and re-publishing"
                    )
                    src_id = ids.get("source_item_id")
                    if src_id:
                        old_src = gis.content.get(src_id)
                        if old_src:
                            old_src.delete()
                    _delete_service(item)
                    ids = {}
            elif ids.get("feature_item_id"):
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
            pub_item = _publish_src_item(src_item, layer.id, layer.name)
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
        drawing_info: dict[str, Any] = {"renderer": arcgis_renderer}
        layer_def: dict[str, Any] = {"drawingInfo": drawing_info}
        if layer.label is not None:
            drawing_info["labelingInfo"] = [_build_labeling_info(layer.label)]
            layer_def["showLabels"] = True
        flc.layers[0].manager.update_definition(layer_def)
        print(f"    Applied {layer.renderer.kind} renderer")

    return size_mb


# ── Web map creation ─────────────────────────────────────────────────────────


def _layer_item_ids_for_map(
    bound: "BoundMap",
    item_registry: dict[str, dict],
) -> list[str]:
    """Return feature_item_ids for all publishable, registered layers in a map."""
    ids = []
    for layer in bound.bound_layers:
        if layer.provider == "wms" or layer.datasource.startswith("http"):
            continue
        fid = item_registry.get(layer.id, {}).get("feature_item_id")
        if fid:
            ids.append(fid)
        else:
            print(f"    {layer.id}: no feature_item_id; omitting from web map")
    return ids


def _reproject_extent(
    extent: Extent,
    src_crs: str,
    dst_crs: str = "EPSG:4326",
) -> tuple[float, float, float, float]:
    """Reproject an Extent from src_crs to dst_crs."""
    tf = Transformer.from_crs(src_crs, dst_crs, always_xy=True)
    xmin, ymin = tf.transform(extent.xmin, extent.ymin)
    xmax, ymax = tf.transform(extent.xmax, extent.ymax)
    return (xmin, ymin, xmax, ymax)


def _build_webmap_json(
    layer_items: list[Any],
    extent_3857: tuple[float, float, float, float] | None = None,
) -> dict[str, Any]:
    """Build minimal ArcGIS web map JSON from a list of hosted layer items."""
    operational_layers = []
    # ArcGIS renders operationalLayers[0] at the bottom; reverse so that
    # project layers[0] (topmost in the legend) ends up on top.
    for item in reversed(layer_items):
        item_url = (item.url or "").rstrip("/")
        if item.type in ("Feature Service",):
            operational_layers.append(
                {
                    "id": item.id,
                    "title": item.title,
                    "url": item_url + "/0",
                    "layerType": "ArcGISFeatureLayer",
                    "visibility": True,
                    "opacity": 1,
                }
            )
        elif "Image" in item.type:
            operational_layers.append(
                {
                    "id": item.id,
                    "title": item.title,
                    "url": item_url,
                    "layerType": "ArcGISTiledImageServiceLayer",
                    "visibility": True,
                    "opacity": 1,
                }
            )
        else:
            print(
                f"    Warning: unknown item type {item.type!r} for "
                f"{item.title!r}; skipping"
            )
    result: dict[str, Any] = {
        "operationalLayers": operational_layers,
        "baseMap": {
            "baseMapLayers": [
                {
                    "id": "World_Light_Gray_Base",
                    "layerType": "ArcGISTiledMapServiceLayer",
                    "url": (
                        "https://services.arcgisonline.com/ArcGIS/rest/"
                        "services/Canvas/World_Light_Gray_Base/MapServer"
                    ),
                    "visibility": True,
                    "opacity": 1,
                    "title": "Light Gray Canvas Base",
                },
                {
                    "id": "World_Light_Gray_Reference",
                    "layerType": "ArcGISTiledMapServiceLayer",
                    "url": (
                        "https://services.arcgisonline.com/ArcGIS/rest/"
                        "services/Canvas/World_Light_Gray_Reference/MapServer"
                    ),
                    "visibility": True,
                    "opacity": 1,
                    "title": "Light Gray Canvas Reference",
                    "isReference": True,
                },
            ],
            "title": "Light Gray Canvas",
        },
        "spatialReference": {"wkid": 102100, "latestWkid": 3857},
        "version": "2.28",
    }
    if extent_3857:
        xmin, ymin, xmax, ymax = extent_3857
        extent_obj = {
            "xmin": round(xmin, 2),
            "ymin": round(ymin, 2),
            "xmax": round(xmax, 2),
            "ymax": round(ymax, 2),
            "spatialReference": {"wkid": 102100, "latestWkid": 3857},
        }
        result["extent"] = extent_obj
        result["initialState"] = {"viewpoint": {"targetGeometry": extent_obj}}
    return result


def _create_web_map(
    map_spec: Any,
    gis: GIS | None,
    item_registry: dict[str, dict],
    map_path: Path,
    *,
    dry_run: bool,
) -> bool:
    """Create or update a web map for one map spec. Returns True if newly created."""
    map_key = f"map:{map_spec.id}"
    bound = BoundMap(**map_spec.model_dump(mode="python"), map_path=map_path)
    layer_ids = _layer_item_ids_for_map(bound, item_registry)

    if not layer_ids:
        print(f"  {map_spec.id}: skip (no published layers)")
        return False

    if dry_run:
        existing_id = item_registry.get(map_key, {}).get("webmap_item_id", "new")
        print(
            f"  {map_spec.id}: would update web map "
            f"({len(layer_ids)} layers, id={existing_id})"
        )
        return False

    assert gis is not None

    layer_items = [gis.content.get(fid) for fid in layer_ids]
    layer_items = [it for it in layer_items if it is not None]

    extent_3857 = None
    if map_spec.extent and map_spec.crs:
        try:
            extent_3857 = _reproject_extent(
                map_spec.extent, map_spec.crs, dst_crs="EPSG:3857"
            )
        except Exception as exc:
            print(f"    Warning: could not reproject extent: {exc}")

    webmap_text = json.dumps(_build_webmap_json(layer_items, extent_3857=extent_3857))

    existing = item_registry.get(map_key, {})
    existing_item = (
        gis.content.get(existing["webmap_item_id"])
        if existing.get("webmap_item_id")
        else None
    )
    if existing_item:
        existing_item.update(item_properties={"text": webmap_text})
        _save_registry(_ARCGIS_JSON, item_registry)
        print(f"    Updated {map_spec.id} (webmap_item_id={existing_item.id})")
        return False  # not new — existing story map link still valid

    root_folder = gis.content.folders.get()
    props = ItemProperties(
        title=map_spec.title,
        item_type=ItemTypeEnum.WEB_MAP,
        tags=_ARCGIS_TAG,
        snippet=f"Web map: {map_spec.title}",
    )
    wm_item = root_folder.add(item_properties=props, text=webmap_text).result()
    item_registry[map_key] = {
        "webmap_item_id": wm_item.id,
        "added_to_story_maps": [],
    }
    _save_registry(_ARCGIS_JSON, item_registry)
    print(f"    Created web map (webmap_item_id={wm_item.id})")
    return True


# ── Story map ─────────────────────────────────────────────────────────────────


def _story_map_resource(
    wm_id: str,
    map_spec: Any,
    gis: GIS,
) -> dict[str, Any]:
    """Build the story map resource data block for one web map."""
    # Extent and viewpoint in web mercator (wkid 102100) for the story viewer.
    extent_dict: dict[str, Any] = {}
    center_dict: dict[str, Any] | None = None
    viewpoint: dict[str, Any] = {"rotation": 0, "scale": -1, "targetGeometry": {}}

    if map_spec.extent and map_spec.crs:
        try:
            xmin, ymin, xmax, ymax = _reproject_extent(
                map_spec.extent, map_spec.crs, dst_crs="EPSG:3857"
            )
            sr = {"wkid": 102100, "latestWkid": 3857}
            extent_dict = {
                "xmin": xmin,
                "ymin": ymin,
                "xmax": xmax,
                "ymax": ymax,
                "spatialReference": sr,
            }
            center_dict = {
                "spatialReference": sr,
                "x": (xmin + xmax) / 2,
                "y": (ymin + ymax) / 2,
            }
            viewpoint = {"rotation": 0, "scale": -1, "targetGeometry": center_dict}
        except Exception as exc:
            print(f"    Warning: could not compute story map extent: {exc}")

    # mapLayers drives per-story layer visibility; must match the web map's
    # operational layers with visible:true or the story viewer hides them all.
    map_layers: list[dict[str, Any]] = []
    wm_item = gis.content.get(wm_id)
    if wm_item:
        try:
            wm_data = wm_item.get_data() or {}
            for layer in wm_data.get("operationalLayers", []):
                map_layers.append(
                    {
                        "id": layer["id"],
                        "title": layer.get("title", ""),
                        "visible": layer.get("visibility", True),
                    }
                )
        except Exception as exc:
            print(f"    Warning: could not read web map layers: {exc}")

    return {
        "extent": extent_dict,
        "center": center_dict,
        "zoom": 2,
        "mapLayers": map_layers,
        "viewpoint": viewpoint,
        "itemId": wm_id,
        "itemType": "Web Map",
        "type": "minimal",
    }


def _add_maps_to_story(
    maps: list[Any],
    story_map_id: str,
    gis: GIS | None,
    item_registry: dict[str, dict],
    *,
    dry_run: bool,
) -> None:
    """Add new web maps to the story and refresh resource data for existing ones."""
    candidates = []
    for map_spec in maps:
        map_key = f"map:{map_spec.id}"
        entry = item_registry.get(map_key, {})
        wm_id = entry.get("webmap_item_id")
        if not wm_id:
            print(f"  {map_spec.id}: no web map registered; skipping")
            continue
        already_added = story_map_id in entry.get("added_to_story_maps", [])
        candidates.append((map_key, wm_id, map_spec, already_added))

    if not candidates:
        print("  No web maps registered.")
        return

    if dry_run:
        for _, wm_id, map_spec, already_added in candidates:
            action = "update" if already_added else "add"
            print(f"  {map_spec.id}: would {action} in story map {story_map_id!r}")
        return

    assert gis is not None

    story_item = gis.content.get(story_map_id)
    if not story_item:
        print(
            f"Error: story map item {story_map_id!r} not found",
            file=sys.stderr,
        )
        return

    sm = StoryMap(item=story_item, gis=gis)
    for map_key, wm_id, map_spec, already_added in candidates:
        resource_node = f"r-{wm_id}"
        resource_data = _story_map_resource(wm_id, map_spec, gis)

        if already_added and resource_node in sm._properties.get("resources", {}):
            # Update extent/visibility on the existing node without adding a duplicate.
            sm._properties["resources"][resource_node]["data"] = resource_data
            print(f"  {map_spec.id}: updated")
        else:
            # Write the webmap node directly, bypassing story_content.Map which
            # requires the optional arcgis.map package.
            node_id = _sm_utils.create_unique_id()
            sm._properties["nodes"][node_id] = {
                "type": "webmap",
                "data": {"map": resource_node, "caption": "", "alt": ""},
                "config": {"size": None},
            }
            sm._properties["resources"][resource_node] = {
                "type": "webmap",
                "data": resource_data,
            }
            _sm_utils.add_child(sm, node_id=node_id)
            added = item_registry[map_key].setdefault("added_to_story_maps", [])
            if story_map_id not in added:
                added.append(story_map_id)
            _save_registry(_ARCGIS_JSON, item_registry)
            print(f"  {map_spec.id}: added")

    sm.save(title=story_item.title)
    print(f"  Story map saved ({story_map_id})")


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Publish alidade map layers to ArcGIS Online."
    )
    parser.add_argument(
        "map_dir",
        help="Map directory, e.g. projects/goats",
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
    parser.add_argument(
        "--create-maps",
        action="store_true",
        help=(
            "After publishing layers, create ArcGIS web maps from the "
            "map's maps list. Maps whose layer set is unchanged are skipped."
        ),
    )
    parser.add_argument(
        "--story-map-id",
        default=None,
        metavar="ITEM_ID",
        help=(
            "ArcGIS Online item ID of the Story Map to update. Implies "
            "--create-maps. New web maps (those not yet recorded as added) "
            "are appended to the story. Can also be set as "
            "ARCGIS_STORY_MAP_ID in local.env."
        ),
    )
    args = parser.parse_args()

    # Load map — same resolution as bind_map / alidade-build
    map_path = (Path.cwd() / args.map_dir).resolve()
    try:
        rel_parts = map_path.relative_to(_REPO_ROOT).parts
    except ValueError:
        # map_path resolved through a symlink; find matching entry in projects/
        for _c in (_REPO_ROOT / "projects").glob("*"):
            if _c.is_symlink() and _c.resolve() == map_path:
                rel_parts = _c.relative_to(_REPO_ROOT).parts
                break
        else:
            raise
    package = ".".join(rel_parts)
    module = importlib.import_module(f"{package}.main")

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
    bound = BoundMap(**spec.model_dump(mode="python"), map_path=map_path)
    publish_dir = map_path / "publish"

    print(f"Map: {spec.title!r}  ({len(spec.layers)} layers)")
    if args.dry_run:
        print("Dry run — preparing files only, no ArcGIS API calls")

    # Item registry
    item_registry = _load_item_registry(_ARCGIS_JSON)
    print(
        f"Item registry ({_ARCGIS_JSON.name}): "
        f"{len(item_registry)} layer(s) registered"
    )

    # Authenticate (skipped in dry_run)
    env = _read_local_env(_LOCAL_ENV)
    story_map_id: str | None = args.story_map_id or env.get("ARCGIS_STORY_MAP_ID")

    gis: GIS | None = None
    if not args.dry_run:
        client_id = env.get("ARCGIS_CLIENT_ID")
        url = env.get("ARGIS_URL", "https://www.arcgis.com")
        if not client_id:
            print(
                "Error: ARCGIS_CLIENT_ID not set in local.env. "
                "Add: ARCGIS_CLIENT_ID := <your-app-id>",
                file=sys.stderr,
            )
            sys.exit(1)
        profile = env.get("ARCGIS_PROFILE", "arcgis_alidade")
        print(f"Authenticating (profile={profile!r})…")
        gis = GIS(url, client_id=client_id, profile=profile)
        me = gis.users.me
        print(f"  OK — signed in as {me.username} ({me.fullName})")

        # Verify registered item IDs
        if item_registry:
            print("Verifying registered items:")
            for layer_id, ids in item_registry.items():
                fid = ids.get("feature_item_id", "")
                if not fid:
                    continue
                item = gis.content.get(fid)
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

    # Create web maps (--create-maps or implied by --story-map-id)
    map_specs = getattr(module, "maps", [])
    do_create_maps = args.create_maps or bool(story_map_id)
    if do_create_maps:
        if not map_specs:
            print("\nNo maps defined in map module; skipping web map creation.")
        else:
            print(f"\nCreating web maps ({len(map_specs)} map(s)):")
            for map_spec in map_specs:
                try:
                    _create_web_map(
                        map_spec,
                        gis,
                        item_registry,
                        map_path,
                        dry_run=args.dry_run,
                    )
                except Exception as exc:
                    print(f"  {map_spec.id}: ERROR — {exc}")

    # Add new web maps to story map
    if story_map_id and map_specs:
        print(f"\nUpdating story map {story_map_id!r}:")
        _add_maps_to_story(
            map_specs,
            story_map_id,
            gis,
            item_registry,
            dry_run=args.dry_run,
        )

    if not args.dry_run:
        print("Done." if not layer_errors else "Done (with errors above).")

    if layer_errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
