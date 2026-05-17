"""Reusable scratch-exploration helpers for Claude sessions."""

import xml.etree.ElementTree as ET
from collections.abc import Callable
from pathlib import Path

import geopandas as gpd
import mapclassify  # type: ignore[import-untyped]


def inspect_shapefile(path: str | Path, sample_rows: int = 0) -> None:
    """Read a shapefile; print CRS, count, geometry types, and column samples."""
    gdf = gpd.read_file(path)
    print(f"Path:   {path}")
    print(f"CRS:    {gdf.crs}")
    print(f"Count:  {len(gdf)}")
    print(f"Geom:   {gdf.geom_type.value_counts().to_dict()}")
    print(f"Bounds: {gdf.total_bounds.round(1).tolist()}")
    print(f"Cols:   {list(gdf.columns)}")
    for col in gdf.columns:
        if col == "geometry":
            continue
        samples = gdf[col].dropna().unique()[:6]
        print(f"  {col}: {list(samples)}")
    if sample_rows:
        print(f"\nFirst {sample_rows} rows:")
        print(gdf.head(sample_rows).to_string())


def find_qgs_layer(
    path: str | Path,
    *,
    layer_id: str | None = None,
    datasource_contains: str | None = None,
    datasource_excludes: tuple[str, ...] = (),
    layername: str | None = None,
) -> ET.Element | None:
    """Find the first matching <maplayer> element in a QGS file.

    All supplied criteria must match (AND logic).
    """
    tree = ET.parse(path)
    for ml in tree.findall(".//maplayer"):
        if layer_id is not None and ml.findtext("id") != layer_id:
            continue
        if layername is not None and ml.findtext("layername") != layername:
            continue
        ds = ml.findtext("datasource") or ""
        if datasource_contains is not None and datasource_contains not in ds:
            continue
        if any(exc in ds for exc in datasource_excludes):
            continue
        return ml
    return None


def flatten_xml(el: ET.Element, prefix: str = "") -> dict[str, str]:
    """Flatten an XML subtree to {xpath: value} dict for diffing."""
    result: dict[str, str] = {}
    tag = f"{prefix}/{el.tag}" if prefix else el.tag
    if el.attrib:
        result[f"{tag}@"] = str(sorted(el.attrib.items()))
    if el.text and el.text.strip():
        result[tag] = el.text.strip()
    for child in el:
        result.update(flatten_xml(child, tag))
    return result


def dump_qgs_layer(
    path: str | Path,
    *,
    layer_id: str | None = None,
    datasource_contains: str | None = None,
    datasource_excludes: tuple[str, ...] = (),
    layername: str | None = None,
    subtree: str | None = None,
    max_chars: int | None = None,
) -> None:
    """Pretty-print maplayer XML (or a named child element) from a QGS file."""
    ml = find_qgs_layer(
        path,
        layer_id=layer_id,
        datasource_contains=datasource_contains,
        datasource_excludes=datasource_excludes,
        layername=layername,
    )
    if ml is None:
        print("Layer not found")
        return
    el = ml.find(subtree) if subtree else ml
    if el is None:
        print(f"Subtree {subtree!r} not found in layer")
        return
    ET.indent(el, space="  ")
    text = ET.tostring(el, encoding="unicode")
    print(text[:max_chars] if max_chars else text)


def diff_qgs_layers(
    path_a: str | Path,
    path_b: str | Path,
    *,
    layer_id: str | None = None,
    datasource_contains: str | None = None,
    datasource_excludes: tuple[str, ...] = (),
    layername: str | None = None,
    subtree: str | None = None,
) -> None:
    """Diff maplayer XML (or a named subtree) between two QGS files."""
    ml_a = find_qgs_layer(
        path_a,
        layer_id=layer_id,
        datasource_contains=datasource_contains,
        datasource_excludes=datasource_excludes,
        layername=layername,
    )
    ml_b = find_qgs_layer(
        path_b,
        layer_id=layer_id,
        datasource_contains=datasource_contains,
        datasource_excludes=datasource_excludes,
        layername=layername,
    )
    if ml_a is None or ml_b is None:
        print(f"  {Path(path_a).name}: {'found' if ml_a else 'NOT FOUND'}")
        print(f"  {Path(path_b).name}: {'found' if ml_b else 'NOT FOUND'}")
        return
    el_a = ml_a.find(subtree) if subtree else ml_a
    el_b = ml_b.find(subtree) if subtree else ml_b
    if el_a is None or el_b is None:
        missing = Path(path_a).name if el_a is None else Path(path_b).name
        print(f"Subtree {subtree!r} not found in {missing}")
        return
    flat_a = flatten_xml(el_a)
    flat_b = flatten_xml(el_b)
    all_keys = sorted(set(flat_a) | set(flat_b))
    diffs = [k for k in all_keys if flat_a.get(k) != flat_b.get(k)]
    label_a = Path(path_a).name
    label_b = Path(path_b).name
    print(f"Differing paths: {len(diffs)}\n")
    for k in diffs:
        a_val = flat_a.get(k, "<missing>")
        b_val = flat_b.get(k, "<missing>")
        print(f"PATH: {k}")
        print(f"  {label_a}: {a_val[:200]}")
        print(f"  {label_b}: {b_val[:200]}")
        print()


def compute_jenks_breaks(
    shapefile_path: str | Path,
    field: str,
    k: int = 5,
    filter_fn: Callable | None = None,
) -> None:
    """Compute k-class Jenks natural breaks on a shapefile field and print results."""
    gdf = gpd.read_file(shapefile_path)
    if filter_fn is not None:
        gdf = gdf[gdf.apply(filter_fn, axis=1)]
    values = gdf[field].dropna()
    print(f"n={len(values)}, min={values.min():.4g}, max={values.max():.4g}")
    classifier = mapclassify.NaturalBreaks(values, k=k)
    print(f"bins:   {classifier.bins.tolist()}")
    print(f"counts: {classifier.counts.tolist()}")


def compute_layer_extent(
    shapefile_path: str | Path, pad_pct: float = 0.05
) -> tuple[float, float, float, float]:
    """Print and return the padded bounding box for a shapefile."""
    gdf = gpd.read_file(shapefile_path)
    minx, miny, maxx, maxy = gdf.total_bounds
    pad_x = (maxx - minx) * pad_pct
    pad_y = (maxy - miny) * pad_pct
    result = (minx - pad_x, miny - pad_y, maxx + pad_x, maxy + pad_y)
    print(f"minx: {result[0]}")
    print(f"miny: {result[1]}")
    print(f"maxx: {result[2]}")
    print(f"maxy: {result[3]}")
    return result


def audit_project_crs(project_dir: str | Path) -> None:
    """Audit CRS consistency across shapefiles, project.qgs, and transform context."""
    base = Path(project_dir)
    qgs_path = base / "output" / "project.qgs"

    print("=== Shapefile CRS ===")
    shapefiles = sorted(
        list((base / "data").glob("*.shp")) + list((base / "output").glob("*.shp"))
    )
    for shp in shapefiles:
        gdf = gpd.read_file(shp)
        epsg = gdf.crs.to_epsg() if gdf.crs else None
        name = gdf.crs.name if gdf.crs else "None"
        rel = shp.relative_to(base)
        print(f"  {rel}: {name}  (EPSG:{epsg})")

    if not qgs_path.exists():
        print(f"\n{qgs_path} not found")
        return

    tree = ET.parse(qgs_path)

    print("\n=== Transform context ===")
    pairs = []
    for sd in tree.findall(".//transformContext/srcDest"):
        src_el = sd.find(".//src//authid")
        dst_el = sd.find(".//dest//authid")
        fallback = sd.get("allowFallback", "?")
        pairs.append(
            (
                src_el.text if src_el is not None else "?",
                dst_el.text if dst_el is not None else "?",
                fallback,
            )
        )
    if pairs:
        for src, dst, fb in pairs:
            print(f"  {src} → {dst}  fallback={fb}")
    else:
        print("  (empty — QGIS will ask on open)")

    print("\n=== Layer CRS in project.qgs ===")
    for ml in tree.findall(".//maplayer"):
        lid = ml.findtext("id")
        authid_el = ml.find(".//srs//spatialrefsys//authid")
        authid = authid_el.text if authid_el is not None else "?"
        provider = ml.findtext("provider")
        print(f"  {lid}: crs={authid}  provider={provider}")

    print("\n=== Project CRS ===")
    pcrs = tree.find(".//projectCrs//spatialrefsys//authid")
    print(f"  {pcrs.text if pcrs is not None else '?'}")
