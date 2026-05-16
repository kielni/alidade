"""Render project.py → output/project.qgs."""

import importlib
import os
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

from pyproj import CRS as ProjCRS

from alidade.models import (
    GraduatedRenderer,
    Layer,
    PalettedRenderer,
    PrintLegend,
    PrintMapFrame,
    PrintNorthArrow,
    PrintPage,
    PrintScaleBar,
    Project,
    Renderer,
    SimpleFill,
    SimpleLine,
    SimpleMarker,
    SingleSymbol,
    SvgMarker,
    Symbol,
    SymbolLayer,
    RuleRenderer,
)

HERE = Path(__file__).parent  # alidade/

_QGS_DOCTYPE = "<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>\n"

# QGIS geometry attribute (display string) and wkbType (numeric code).
_GEOMETRY_ATTR: dict[str, str] = {
    "Point": "Point",
    "LineString": "Line",
    "Polygon": "Polygon",
    "MultiPoint": "Point",
    "MultiLineString": "Line",
    "MultiPolygon": "Polygon",
}
_WKB_TYPE: dict[str, str] = {
    "Point": "1",
    "LineString": "2",
    "Polygon": "3",
    "MultiPoint": "4",
    "MultiLineString": "5",
    "MultiPolygon": "6",
}


def _split_source_suffix(source: str) -> tuple[str, str]:
    """Split a source string into (path_part, suffix).

    Handles both OGR-style (|layername=...) and delimited-text-style
    (?type=csv&...) suffixes.  Returns (path, suffix_including_delimiter).
    """
    if "|" in source:
        path, tail = source.split("|", 1)
        return path, "|" + tail
    if "?" in source:
        path, tail = source.split("?", 1)
        return path, "?" + tail
    return source, ""


def _abs_source(source: str, project_dir: Path) -> str:
    """Resolve a source path to absolute.

    Paths starting with './' or 'data/' are project-dir-relative.
    All other relative paths are HERE-relative (source data alongside the repo).
    URIs and absolute paths are returned unchanged.
    """
    if source.startswith("/") or source.startswith("?") or ":" in source.split("/")[0]:
        return source
    path_part, geom_suffix = _split_source_suffix(source)
    if path_part.startswith("./") or path_part.startswith("data/"):
        return str((project_dir / path_part).resolve()) + geom_suffix
    return str((HERE / path_part).resolve()) + geom_suffix


def _rel_source(source: str, project_dir: Path) -> str:
    """Return datasource relative to project_dir/output/ for output/project.qgs.

    Local file paths are made relative to the output directory.
    Delimited-text sources (suffix starts with '?') get a 'file:' prefix,
    as required by the QGIS delimitedtext provider.
    Other URIs are returned unchanged.
    """
    abs_src = _abs_source(source, project_dir)
    path_part, geom_suffix = _split_source_suffix(abs_src)
    if path_part.startswith("/"):
        output_dir = project_dir / "output"
        rel = os.path.relpath(path_part, output_dir)
        prefix = "file:" if geom_suffix.startswith("?") else ""
        return prefix + rel + geom_suffix
    return abs_src


def _load_spec(project_dir: Path) -> Project:
    """Load project.py from project_dir and return its spec attribute."""
    spec_path = project_dir / "project.py"
    if not spec_path.exists():
        raise SystemExit(
            f"project.py not found in {project_dir} — run 'make dump' first"
        )
    repo_root = Path(__file__).parent.parent
    package = ".".join(project_dir.relative_to(repo_root).parts)
    return importlib.import_module(f"{package}.project").spec


def _update_extent(root: ET.Element, extent: tuple[float, float, float, float]) -> None:
    """Write xmin/ymin/xmax/ymax into the theMapCanvas extent element."""
    xmin, ymin, xmax, ymax = extent
    for canvas in root.findall("mapcanvas"):
        if canvas.get("name") == "theMapCanvas":
            ext = canvas.find("extent")
            if ext is None:
                ext = ET.SubElement(canvas, "extent")
            for tag, val in (
                ("xmin", xmin),
                ("ymin", ymin),
                ("xmax", xmax),
                ("ymax", ymax),
            ):
                el = ext.find(tag)
                if el is None:
                    el = ET.SubElement(ext, tag)
                el.text = repr(val)
            break


def _fill_spatialrefsys(srs_el: ET.Element, authid: str) -> None:
    """Populate an existing <spatialrefsys> element with CRS data from pyproj."""
    crs = ProjCRS(authid)
    epsg_code = authid.split(":")[-1]
    fields = [
        ("wkt", crs.to_wkt()),
        ("proj4", ""),
        ("srsid", "0"),
        ("srid", epsg_code),
        ("authid", authid),
        ("description", crs.name),
        ("projectionacronym", ""),
        ("ellipsoidacronym", ""),
        ("geographicflag", "true" if crs.is_geographic else "false"),
    ]
    for tag, val in fields:
        el = srs_el.find(tag)
        if el is None:
            el = ET.SubElement(srs_el, tag)
        el.text = val


def _update_crs(root: ET.Element, authid: str) -> None:
    """Populate projectCrs and theMapCanvas/destinationsrs with the project CRS."""
    srs = root.find("projectCrs/spatialrefsys")
    if srs is not None:
        _fill_spatialrefsys(srs, authid)
    for canvas in root.findall("mapcanvas"):
        if canvas.get("name") == "theMapCanvas":
            srs = canvas.find("destinationsrs/spatialrefsys")
            if srs is not None:
                _fill_spatialrefsys(srs, authid)
            break


def _update_title(root: ET.Element, title: str) -> None:
    """Set the project title text and projectname attribute in root."""
    el = root.find("title")
    if el is not None:
        el.text = title
    root.set("projectname", title)


def _rebuild_layer_tree(root: ET.Element, spec: Project, project_dir: Path) -> None:
    """Rebuild the <layer-tree-group> in root from spec layers."""
    ltg = root.find("layer-tree-group")
    if ltg is None:
        return

    for layer in spec.layers:
        checked = "Qt::Checked" if layer.visible else "Qt::Unchecked"
        ltl = ET.SubElement(
            ltg,
            "layer-tree-layer",
            checked=checked,
            legend_exp="",
            legend_split_behavior="0",
            providerKey=layer.provider,
            patch_size="-1,-1",
            id=layer.id,
            source=_rel_source(layer.source, project_dir),
            expanded="1",
            name=layer.name,
        )
        cp = ET.SubElement(ltl, "customproperties")
        ET.SubElement(cp, "Option")

    custom_order = ET.SubElement(ltg, "custom-order", enabled="0")
    for layer in spec.layers:
        item = ET.SubElement(custom_order, "item")
        item.text = layer.id


def _rebuild_legend(root: ET.Element, spec: Project) -> None:
    """Rebuild the <legend> in root from spec layers."""
    legend = root.find("legend")
    if legend is None:
        legend = ET.SubElement(root, "legend", updateDrawingOrder="true")

    for layer in spec.layers:
        checked = "Qt::Checked" if layer.visible else "Qt::Unchecked"
        vis = "1" if layer.visible else "0"
        ll = ET.SubElement(
            legend,
            "legendlayer",
            checked=checked,
            open="true",
            showFeatureCount="0",
            drawingOrder="-1",
            name=layer.name,
        )
        fg = ET.SubElement(ll, "filegroup", hidden="false", open="true")
        ET.SubElement(
            fg, "legendlayerfile", layerid=layer.id, visible=vis, isInOverview="0"
        )


def _rebuild_layerorder(root: ET.Element, spec: Project) -> None:
    """Rebuild the <layerorder> in root from spec layers."""
    lo = root.find("layerorder")
    if lo is None:
        lo = ET.SubElement(root, "layerorder")
    for layer in spec.layers:
        ET.SubElement(lo, "layer", id=layer.id)


# ── Renderer serialization ────────────────────────────────────────────────────

_SCALE = "3x:0,0,0,0,0,0"


def _ddp() -> ET.Element:
    """Return an empty <data_defined_properties> element used in symbol layers."""
    ddp = ET.Element("data_defined_properties")
    m = ET.SubElement(ddp, "Option", type="Map")
    ET.SubElement(m, "Option", name="name", value="", type="QString")
    ET.SubElement(m, "Option", name="properties")
    ET.SubElement(m, "Option", name="type", value="collection", type="QString")
    return ddp


def _color(c: str) -> str:
    """Upgrade R,G,B,A color string to QGIS 3.30+ extended format with rgb: suffix."""
    if any(tag in c for tag in ("rgb:", "hsv:", "hsl:")):
        return c
    parts = c.split(",")
    if len(parts) != 4:
        return c
    r, g, b, a = (int(p) for p in parts)
    return f"{c},rgb:{r/255:.7g},{g/255:.7g},{b/255:.7g},{a/255:.7g}"


def _opt_map(props: dict[str, str]) -> ET.Element:
    """Return an <Option type='Map'> element with the given name/value pairs."""
    el = ET.Element("Option", type="Map")
    for name, value in props.items():
        ET.SubElement(el, "Option", name=name, value=value, type="QString")
    return el


def _render_symbol_layer(sl: SymbolLayer) -> ET.Element:
    """Serialize a SymbolLayer model to its QGS <layer> element."""
    el = ET.Element(
        "layer",
        locked="0",
        enabled="1",
        **{  # type: ignore[arg-type]
            "class": sl.kind,
            "pass": "0",
            "id": "{" + str(uuid.uuid4()) + "}",
        },
    )
    if isinstance(sl, SimpleFill):
        props = {
            "border_width_map_unit_scale": _SCALE,
            "color": _color(sl.color),
            "joinstyle": sl.joinstyle,
            "offset": sl.offset,
            "offset_map_unit_scale": _SCALE,
            "offset_unit": "MM",
            "outline_color": _color(sl.outline_color),
            "outline_style": sl.outline_style,
            "outline_width": str(sl.outline_width),
            "outline_width_unit": sl.outline_width_unit,
            "style": sl.style,
        }
    elif isinstance(sl, SimpleLine):
        props = {
            "capstyle": sl.capstyle,
            "customdash": "5;2",
            "customdash_map_unit_scale": _SCALE,
            "customdash_unit": "MM",
            "draw_inside_polygon": "0",
            "joinstyle": sl.joinstyle,
            "line_color": _color(sl.line_color),
            "line_style": sl.line_style,
            "line_width": str(sl.line_width),
            "line_width_unit": sl.line_width_unit,
            "offset": sl.offset,
            "offset_map_unit_scale": _SCALE,
            "offset_unit": "MM",
            "ring_filter": "0",
            "use_custom_dash": "0",
            "width_map_unit_scale": _SCALE,
        }
    elif isinstance(sl, SvgMarker):
        props = {
            "angle": str(sl.angle),
            "color": _color(sl.color),
            "fixedAspectRatio": "0",
            "horizontal_anchor_point": "1",
            "name": sl.name,
            "offset": sl.offset,
            "offset_map_unit_scale": _SCALE,
            "offset_unit": sl.offset_unit,
            "outline_color": _color(sl.outline_color),
            "outline_width": str(sl.outline_width),
            "outline_width_map_unit_scale": _SCALE,
            "outline_width_unit": sl.outline_width_unit,
            "scale_method": "diameter",
            "size": str(sl.size),
            "size_map_unit_scale": _SCALE,
            "size_unit": sl.size_unit,
            "vertical_anchor_point": "1",
        }
    elif isinstance(sl, SimpleMarker):
        props = {
            "angle": f"{sl.angle:g}",
            "cap_style": sl.cap_style,
            "color": _color(sl.color),
            "horizontal_anchor_point": "1",
            "joinstyle": sl.joinstyle,
            "name": sl.name,
            "offset": sl.offset,
            "offset_map_unit_scale": _SCALE,
            "offset_unit": sl.offset_unit,
            "outline_color": _color(sl.outline_color),
            "outline_style": "solid",
            "outline_width": f"{sl.outline_width:g}",
            "outline_width_map_unit_scale": _SCALE,
            "outline_width_unit": sl.outline_width_unit,
            "scale_method": "diameter",
            "size": f"{sl.size:g}",
            "size_map_unit_scale": _SCALE,
            "size_unit": sl.size_unit,
            "vertical_anchor_point": "1",
        }
    else:
        props = {}
    el.append(_opt_map(props))
    el.append(_ddp())
    return el


def _render_symbol(sym: Symbol, name: str) -> ET.Element:
    """Serialize a Symbol model to its QGS <symbol> element."""
    el = ET.Element(
        "symbol",
        clip_to_extent="1",
        alpha=f"{sym.alpha:g}",
        type=sym.type,
        is_animated="0",
        frame_rate="10",
        force_rhr="0",
        name=name,
    )
    el.append(_ddp())
    for sl in sym.layers:
        el.append(_render_symbol_layer(sl))
    return el


def _render_graduated_renderer(renderer: GraduatedRenderer) -> ET.Element:
    """Serialize a GraduatedRenderer to its QGS <renderer-v2> element."""
    base = dict(
        forceraster="0", referencescale="-1", symbollevels="0", enableorderby="0"
    )
    el = ET.Element(
        "renderer-v2",
        type="graduatedSymbol",
        attr=renderer.attr,
        graduatedMethod="GraduatedColor",
        **base,  # type: ignore[arg-type]
    )
    ranges_el = ET.SubElement(el, "ranges")
    symbols_el = ET.SubElement(el, "symbols")
    for i, r in enumerate(renderer.ranges):
        label = r.label or f"{r.lower:.0f} – {r.upper:.0f}"
        ET.SubElement(
            ranges_el,
            "range",
            lower=str(r.lower),
            upper=str(r.upper),
            label=label,
            symbol=str(i),
            render="true",
            uuid="{" + str(uuid.uuid4()) + "}",
        )
        sym = Symbol(
            type="fill",
            layers=[
                SimpleFill(
                    color=r.color,
                    outline_color=renderer.outline_color,
                    outline_width=renderer.outline_width,
                    outline_style=renderer.outline_style,
                )
            ],
        )
        symbols_el.append(_render_symbol(sym, str(i)))
    src_color = renderer.ranges[0].color if renderer.ranges else "200,200,200,180"
    src_syms = ET.SubElement(el, "source-symbol")
    src_syms.append(
        _render_symbol(
            Symbol(
                type="fill",
                layers=[
                    SimpleFill(
                        color=src_color,
                        outline_color=renderer.outline_color,
                        outline_width=renderer.outline_width,
                    )
                ],
            ),
            "0",
        )
    )
    c1 = renderer.ranges[0].color if renderer.ranges else "255,255,178,255"
    c2 = renderer.ranges[-1].color if renderer.ranges else "189,0,38,255"
    cr = ET.SubElement(el, "colorramp", type="gradient", name="[source]")
    cr_opts = ET.SubElement(cr, "Option", type="Map")
    for name, value in [
        ("color1", c1),
        ("color2", c2),
        ("direction", "ccw"),
        ("discrete", "0"),
        ("rampType", "gradient"),
    ]:
        ET.SubElement(cr_opts, "Option", name=name, value=value, type="QString")
    ET.SubElement(
        el,
        "labelformat",
        format="%1 - %2",
        labelprecision="0",
        trimtrailingzeroes="true",
    )
    ET.SubElement(el, "rotation")
    ET.SubElement(el, "sizescale")
    return el


def _render_renderer(renderer: Renderer) -> ET.Element:
    """Serialize a Renderer model to its QGS <renderer-v2> element."""
    base = dict(
        forceraster="0", referencescale="-1", symbollevels="0", enableorderby="0"
    )
    if isinstance(renderer, SingleSymbol):
        el = ET.Element(
            "renderer-v2", type="singleSymbol", **base  # type: ignore[arg-type]
        )
        syms = ET.SubElement(el, "symbols")
        syms.append(_render_symbol(renderer.symbol, "0"))
        ET.SubElement(el, "rotation")
        ET.SubElement(el, "sizescale")
        return el
    if isinstance(renderer, RuleRenderer):
        el = ET.Element(
            "renderer-v2", type="RuleRenderer", **base  # type: ignore[arg-type]
        )
        rules_el = ET.SubElement(el, "rules", key=renderer.rules_key)
        for rule in renderer.rules:
            attrs: dict[str, str] = {
                "key": rule.key,
                "label": rule.label,
                "filter": rule.filter,
                "symbol": str(rule.symbol_index),
            }
            if not rule.active:
                attrs["checkstate"] = "0"
            ET.SubElement(rules_el, "rule", **attrs)  # type: ignore[arg-type]
        syms = ET.SubElement(el, "symbols")
        for i, sym in enumerate(renderer.symbols):
            syms.append(_render_symbol(sym, str(i)))
        return el
    if isinstance(renderer, GraduatedRenderer):
        return _render_graduated_renderer(renderer)
    raise ValueError(f"Unknown renderer type: {type(renderer)}")


def _srs_element(authid: str) -> ET.Element:
    """Build a <srs> element for authid, using pyproj to supply WKT and metadata."""
    crs = ProjCRS(authid)
    epsg_code = authid.split(":")[-1]
    srs = ET.Element("srs")
    sys_el = ET.SubElement(srs, "spatialrefsys", nativeFormat="Wkt")
    ET.SubElement(sys_el, "wkt").text = crs.to_wkt()
    ET.SubElement(sys_el, "srsid").text = "0"
    ET.SubElement(sys_el, "srid").text = epsg_code
    ET.SubElement(sys_el, "authid").text = authid
    ET.SubElement(sys_el, "description").text = crs.name
    ET.SubElement(sys_el, "projectionacronym").text = ""
    ET.SubElement(sys_el, "ellipsoidacronym").text = ""
    ET.SubElement(sys_el, "geographicflag").text = (
        "true" if crs.is_geographic else "false"
    )
    return srs


def _build_vector_maplayer(layer: Layer) -> ET.Element:
    """Build a minimal <maplayer type='vector'> element for layer."""
    assert layer.geometry_type is not None
    geom_attr = _GEOMETRY_ATTR.get(layer.geometry_type, layer.geometry_type)
    wkb_type = _WKB_TYPE.get(layer.geometry_type, "0")
    ml = ET.Element(
        "maplayer",
        type="vector",
        geometry=geom_attr,
        wkbType=wkb_type,
        autoRefreshTime="0",
        autoRefreshMode="Disabled",
        styleCategories="AllStyleCategories",
        labelsEnabled="0",
        readOnly="0",
        refreshOnNotifyEnabled="0",
        refreshOnNotifyMessage="",
        maxScale="0",
        minScale="100000000",
        hasScaleBasedVisibilityFlag="0",
        simplifyDrawingHints="1",
        simplifyDrawingTol="1",
        simplifyMaxScale="1",
        simplifyAlgorithm="0",
        simplifyLocal="1",
        symbologyReferenceScale="-1",
        legendPlaceholderImage="",
    )
    ET.SubElement(ml, "id").text = layer.id
    ET.SubElement(ml, "datasource")
    ET.SubElement(ml, "layername").text = layer.name
    if layer.crs:
        ml.append(_srs_element(layer.crs))
    ET.SubElement(ml, "provider", encoding="UTF-8").text = layer.provider
    style_mgr = ET.SubElement(ml, "map-layer-style-manager", current="default")
    ET.SubElement(style_mgr, "map-layer-style", name="default")
    flags = ET.SubElement(ml, "flags")
    for flag, val in [
        ("Identifiable", "1"),
        ("Removable", "1"),
        ("Searchable", "1"),
        ("Private", "0"),
    ]:
        ET.SubElement(flags, flag).text = val
    ET.SubElement(ml, "fieldConfiguration")
    ET.SubElement(ml, "vectorjoins")
    ET.SubElement(ml, "layerDependencies")
    ET.SubElement(ml, "dataDependencies")
    ET.SubElement(ml, "expressionfields")
    return ml


def _build_paletted_pipe(renderer: PalettedRenderer) -> ET.Element:
    """Build the <pipe> element for a paletted raster renderer."""
    pipe = ET.Element("pipe")
    provider_el = ET.SubElement(pipe, "provider")
    ET.SubElement(
        provider_el,
        "resampling",
        maxOversampling="2",
        enabled="false",
        zoomedInResamplingMethod="nearestNeighbour",
        zoomedOutResamplingMethod="nearestNeighbour",
    )
    r = ET.SubElement(
        pipe,
        "rasterrenderer",
        type="paletted",
        band=str(renderer.band),
        alphaBand="-1",
        opacity=str(renderer.opacity),
        nodataColor="",
    )
    ET.SubElement(r, "rasterTransparency")
    mmo = ET.SubElement(r, "minMaxOrigin")
    for tag, val in [
        ("limits", "None"),
        ("extent", "WholeRaster"),
        ("statAccuracy", "Estimated"),
        ("cumulativeCutLower", "0.02"),
        ("cumulativeCutUpper", "0.98"),
        ("stdDevFactor", "2"),
    ]:
        ET.SubElement(mmo, tag).text = val
    palette = ET.SubElement(r, "colorPalette")
    for entry in renderer.entries:
        ET.SubElement(
            palette,
            "paletteEntry",
            value=str(entry.value),
            color=entry.color,
            alpha=str(entry.alpha),
            label=entry.label,
        )
    ET.SubElement(pipe, "brightnesscontrast", gamma="1", contrast="0", brightness="0")
    ET.SubElement(
        pipe,
        "huesaturation",
        colorizeRed="255",
        colorizeGreen="128",
        invertColors="0",
        colorizeOn="0",
        grayscaleMode="0",
        saturation="0",
        colorizeStrength="100",
        colorizeBlue="128",
    )
    ET.SubElement(pipe, "rasterresampler", maxOversampling="2")
    ET.SubElement(pipe, "resamplingStage").text = "resamplingFilter"
    return pipe


def _build_raster_maplayer(layer: Layer) -> ET.Element:
    """Build a minimal <maplayer type='raster'> element for layer."""
    ml = ET.Element(
        "maplayer",
        type="raster",
        autoRefreshTime="0",
        autoRefreshMode="Disabled",
        styleCategories="AllStyleCategories",
        refreshOnNotifyEnabled="0",
        refreshOnNotifyMessage="",
        maxScale="0",
        minScale="100000000",
        hasScaleBasedVisibilityFlag="0",
        legendPlaceholderImage="",
    )
    ET.SubElement(ml, "id").text = layer.id
    ET.SubElement(ml, "datasource")
    ET.SubElement(ml, "layername").text = layer.name
    if layer.crs:
        ml.append(_srs_element(layer.crs))
    ET.SubElement(ml, "provider").text = layer.provider
    style_mgr = ET.SubElement(ml, "map-layer-style-manager", current="default")
    ET.SubElement(style_mgr, "map-layer-style", name="default")
    flags = ET.SubElement(ml, "flags")
    for flag, val in [
        ("Identifiable", "1"),
        ("Removable", "1"),
        ("Searchable", "1"),
        ("Private", "0"),
    ]:
        ET.SubElement(flags, flag).text = val
    nodata = ET.SubElement(ml, "noData")
    ET.SubElement(nodata, "noDataList", useSrcNoData="1", bandNo="1")
    if isinstance(layer.renderer, PalettedRenderer):
        ml.append(_build_paletted_pipe(layer.renderer))
    else:
        pipe = ET.SubElement(ml, "pipe")
        provider_el = ET.SubElement(pipe, "provider")
        ET.SubElement(
            provider_el,
            "resampling",
            maxOversampling="2",
            enabled="false",
            zoomedInResamplingMethod="nearestNeighbour",
            zoomedOutResamplingMethod="nearestNeighbour",
        )
        r = ET.SubElement(
            pipe,
            "rasterrenderer",
            type="singlebandgray",
            grayBand="1",
            alphaBand=str(layer.alpha_band) if layer.alpha_band is not None else "-1",
            opacity="1",
            gradient="BlackToWhite",
            nodataColor="",
        )
        ET.SubElement(r, "rasterTransparency")
        mmo = ET.SubElement(r, "minMaxOrigin")
        for tag, val in [
            ("limits", "MinMax"),
            ("extent", "WholeRaster"),
            ("statAccuracy", "Estimated"),
            ("cumulativeCutLower", "0.02"),
            ("cumulativeCutUpper", "0.98"),
            ("stdDevFactor", "2"),
        ]:
            ET.SubElement(mmo, tag).text = val
        ce = ET.SubElement(r, "contrastEnhancement")
        ET.SubElement(ce, "minValue").text = "0"
        ET.SubElement(ce, "maxValue").text = "1"
        ET.SubElement(ce, "algorithm").text = "StretchToMinimumMaximum"
        ET.SubElement(
            pipe, "brightnesscontrast", gamma="1", contrast="0", brightness="0"
        )
        ET.SubElement(
            pipe,
            "huesaturation",
            colorizeRed="255",
            colorizeGreen="128",
            invertColors="0",
            colorizeOn="0",
            grayscaleMode="0",
            saturation="0",
            colorizeStrength="100",
            colorizeBlue="128",
        )
        ET.SubElement(pipe, "rasterresampler", maxOversampling="2")
        ET.SubElement(pipe, "resamplingStage").text = "resamplingFilter"
    ET.SubElement(ml, "blendMode").text = "0"
    return ml


def _inject_layers(root: ET.Element, spec: Project, project_dir: Path) -> None:
    """Insert all spec layers as <maplayer> elements into <projectlayers>."""
    pl = root.find("projectlayers")
    if pl is None:
        pl = ET.SubElement(root, "projectlayers")

    for layer in spec.layers:
        if layer.style_xml is None:
            if layer.type == "vector" and layer.geometry_type:
                ml = _build_vector_maplayer(layer)
            elif layer.type == "raster":
                ml = _build_raster_maplayer(layer)
            else:
                continue
        else:
            xml_path = project_dir / layer.style_xml
            if not xml_path.exists():
                print(f"  warning: {xml_path} not found, skipping {layer.name!r}")
                continue
            ml = ET.parse(xml_path).getroot()
        ml.set("id", layer.id)
        id_el = ml.find("id")
        if id_el is not None:
            id_el.text = layer.id
        ds = ml.find("datasource")
        if ds is not None:
            ds.text = _rel_source(layer.source, project_dir)
        nm = ml.find("layername")
        if nm is not None:
            nm.text = layer.name
        if layer.renderer is not None and layer.type == "vector":
            old = ml.find("renderer-v2")
            new = _render_renderer(layer.renderer)
            if old is not None:
                children = list(ml)
                ml.remove(old)
                ml.insert(children.index(old), new)
            else:
                ml.append(new)
        pl.append(ml)


def render(spec: Project, project_dir: Path) -> None:
    """Render project spec to output/project.qgs inside project_dir."""
    base_path = project_dir / "styles" / "base.qgs"
    if not base_path.exists():
        base_path = HERE / "util" / "base.qgs"

    content = base_path.read_text()
    if content.startswith("<!DOCTYPE"):
        content = content[content.index(">") + 1 :].lstrip()

    root = ET.fromstring(content)

    if spec.extent:
        _update_extent(root, spec.extent)
    _update_crs(root, spec.crs)
    _update_title(root, spec.title)
    _inject_layers(root, spec, project_dir)
    _rebuild_layer_tree(root, spec, project_dir)
    _rebuild_legend(root, spec)
    _rebuild_layerorder(root, spec)

    output_dir = project_dir / "output"
    output_dir.mkdir(exist_ok=True)
    out = output_dir / "project.qgs"
    out.write_text(_QGS_DOCTYPE + ET.tostring(root, encoding="unicode"))
    print(f"Wrote {out}")

    if spec.print_layout is not None:
        render_print_layout(spec, project_dir)


# ── QPT print layout rendering ────────────────────────────────────────────────


def _qpt_uuid() -> str:
    """Return a QGIS-style UUID string wrapped in braces."""
    return "{" + str(uuid.uuid4()) + "}"


def _pos(x: float, y: float) -> str:
    """Return a QGIS position string 'x,y,mm'."""
    return f"{x},{y},mm"


def _sz(w: float, h: float) -> str:
    """Return a QGIS size string 'w,h,mm'."""
    return f"{w},{h},mm"


def _layout_object() -> ET.Element:
    """Return a <LayoutObject> element with empty data-defined properties."""
    lo = ET.Element("LayoutObject")
    ddp = ET.SubElement(lo, "dataDefinedProperties")
    m = ET.SubElement(ddp, "Option", type="Map")
    ET.SubElement(m, "Option", name="name", value="", type="QString")
    ET.SubElement(m, "Option", name="properties")
    ET.SubElement(m, "Option", name="type", value="collection", type="QString")
    cp = ET.SubElement(lo, "customproperties")
    ET.SubElement(cp, "Option")
    return lo


def _frame_bg(el: ET.Element) -> None:
    """Append FrameColor and BackgroundColor child elements to el."""
    ET.SubElement(el, "FrameColor", alpha="255", blue="0", red="0", green="0")
    ET.SubElement(
        el, "BackgroundColor", alpha="255", blue="255", red="255", green="255"
    )


def _dd_props() -> ET.Element:
    """Return a <dd_properties> element with an empty data-defined property Map."""
    el = ET.Element("dd_properties")
    m = ET.SubElement(el, "Option", type="Map")
    ET.SubElement(m, "Option", name="name", value="", type="QString")
    ET.SubElement(m, "Option", name="properties")
    ET.SubElement(m, "Option", name="type", value="collection", type="QString")
    return el


def _text_bg() -> ET.Element:
    """Return a <background> element for text style with a white SimpleFill."""
    bg = ET.Element(
        "background",
        shapeRadiiX="0",
        shapeRadiiY="0",
        shapeOffsetMapUnitScale=_SCALE,
        shapeOpacity="1",
        shapeRotationType="0",
        shapeJoinStyle="64",
        shapeDraw="0",
        shapeSizeUnit="MM",
        shapeSizeType="0",
        shapeRadiiMapUnitScale=_SCALE,
        shapeBorderWidthUnit="MM",
        shapeRadiiUnit="MM",
        shapeSizeX="0",
        shapeOffsetUnit="MM",
        shapeSizeY="0",
        shapeSVGFile="",
        shapeBorderWidth="0",
        shapeBlendMode="0",
        shapeFillColor="255,255,255,255,rgb:1,1,1,1",
        shapeType="0",
        shapeRotation="0",
        shapeSizeMapUnitScale=_SCALE,
        shapeOffsetX="0",
        shapeBorderColor="128,128,128,255,rgb:0.5019608,0.5019608,0.5019608,1",
        shapeOffsetY="0",
        shapeBorderWidthMapUnitScale=_SCALE,
    )
    sym = ET.SubElement(
        bg,
        "symbol",
        alpha="1",
        type="fill",
        is_animated="0",
        name="fillSymbol",
        clip_to_extent="1",
        frame_rate="10",
        force_rhr="0",
    )
    sym.append(_ddp())
    lay = ET.SubElement(
        sym,
        "layer",
        locked="0",
        enabled="1",
        id="",
        **{"class": "SimpleFill", "pass": "0"},  # type: ignore[arg-type]
    )
    lay.append(
        _opt_map(
            {
                "border_width_map_unit_scale": _SCALE,
                "color": "255,255,255,255,rgb:1,1,1,1",
                "joinstyle": "bevel",
                "offset": "0,0",
                "offset_map_unit_scale": _SCALE,
                "offset_unit": "MM",
                "outline_color": (
                    "128,128,128,255,rgb:0.5019608,0.5019608,0.5019608,1"
                ),
                "outline_style": "no",
                "outline_width": "0",
                "outline_width_unit": "MM",
                "style": "solid",
            }
        )
    )
    lay.append(_ddp())
    return bg


def _text_style(
    font_size: int, named_style: str = "", multiline_height: float = 1.0
) -> ET.Element:
    """Return a <text-style> element with the given font size and named style."""
    ts = ET.Element(
        "text-style",
        allowHtml="0",
        capitalization="0",
        tabStopDistanceMapUnitScale=_SCALE,
        tabStopDistanceUnit="Percentage",
        forcedItalic="0",
        fontLetterSpacing="0",
        textColor="0,0,0,255,rgb:0,0,0,1",
        textOrientation="horizontal",
        fontSize=str(font_size),
        textOpacity="1",
        fontStrikeout="0",
        fontItalic="0",
        namedStyle=named_style,
        fontWordSpacing="0",
        fontFamily=".AppleSystemUIFont",
        fontSizeMapUnitScale=_SCALE,
        previewBkgrdColor="255,255,255,255,rgb:1,1,1,1",
        multilineHeightUnit="Percentage",
        fontUnderline="0",
        fontWeight="50",
        forcedBold="0",
        fontKerning="1",
        fontSizeUnit="Point",
        blendMode="0",
        multilineHeight=str(multiline_height),
        tabStopDistance="6",
    )
    ET.SubElement(ts, "families")
    ET.SubElement(
        ts,
        "text-buffer",
        bufferColor="255,255,255,255,rgb:1,1,1,1",
        bufferSizeMapUnitScale=_SCALE,
        bufferBlendMode="0",
        bufferSizeUnits="MM",
        bufferNoFill="1",
        bufferOpacity="1",
        bufferJoinStyle="128",
        bufferSize="1",
        bufferDraw="0",
    )
    ET.SubElement(
        ts,
        "text-mask",
        maskSizeMapUnitScale=_SCALE,
        maskedSymbolLayers="",
        maskSize="1.5",
        maskSizeUnits="MM",
        maskJoinStyle="128",
        maskOpacity="1",
        maskSize2="1.5",
        maskEnabled="0",
        maskType="0",
    )
    ts.append(_text_bg())
    ET.SubElement(
        ts,
        "shadow",
        shadowRadiusMapUnitScale=_SCALE,
        shadowRadiusAlphaOnly="0",
        shadowOpacity="0.69999999999999996",
        shadowOffsetGlobal="1",
        shadowOffsetDist="1",
        shadowOffsetMapUnitScale=_SCALE,
        shadowUnder="0",
        shadowRadius="1.5",
        shadowRadiusUnit="MM",
        shadowBlendMode="6",
        shadowColor="0,0,0,255,rgb:0,0,0,1",
        shadowOffsetUnit="MM",
        shadowOffsetAngle="135",
        shadowScale="100",
        shadowDraw="0",
    )
    ts.append(_dd_props())
    return ts


def _white_fill_sym(name: str = "") -> ET.Element:
    """Return a white SimpleFill <symbol> element."""
    sym = ET.Element(
        "symbol",
        alpha="1",
        type="fill",
        is_animated="0",
        name=name,
        clip_to_extent="1",
        frame_rate="10",
        force_rhr="0",
    )
    sym.append(_ddp())
    lay = ET.SubElement(
        sym,
        "layer",
        locked="0",
        enabled="1",
        id="",
        **{"class": "SimpleFill", "pass": "0"},  # type: ignore[arg-type]
    )
    lay.append(
        _opt_map(
            {
                "border_width_map_unit_scale": _SCALE,
                "color": "255,255,255,255,rgb:1,1,1,1",
                "joinstyle": "miter",
                "offset": "0,0",
                "offset_map_unit_scale": _SCALE,
                "offset_unit": "MM",
                "outline_color": ("35,35,35,255,rgb:0.1372549,0.1372549,0.1372549,1"),
                "outline_style": "no",
                "outline_width": "0.26",
                "outline_width_unit": "MM",
                "style": "solid",
            }
        )
    )
    lay.append(_ddp())
    return sym


def _solid_fill_sym(color: str, name: str = "") -> ET.Element:
    """Return a solid-color SimpleFill <symbol> element."""
    sym = ET.Element(
        "symbol",
        alpha="1",
        type="fill",
        is_animated="0",
        name=name,
        clip_to_extent="1",
        frame_rate="10",
        force_rhr="0",
    )
    sym.append(_ddp())
    lay = ET.SubElement(
        sym,
        "layer",
        locked="0",
        enabled="1",
        id="",
        **{"class": "SimpleFill", "pass": "0"},  # type: ignore[arg-type]
    )
    lay.append(
        _opt_map(
            {
                "border_width_map_unit_scale": _SCALE,
                "color": color,
                "joinstyle": "bevel",
                "offset": "0,0",
                "offset_map_unit_scale": _SCALE,
                "offset_unit": "MM",
                "outline_color": ("35,35,35,255,rgb:0.1372549,0.1372549,0.1372549,1"),
                "outline_style": "no",
                "outline_width": "0.26",
                "outline_width_unit": "MM",
                "style": "solid",
            }
        )
    )
    lay.append(_ddp())
    return sym


def _simple_line_sym(name: str = "") -> ET.Element:
    """Return a thin black SimpleLine <symbol> element."""
    sym = ET.Element(
        "symbol",
        alpha="1",
        type="line",
        is_animated="0",
        name=name,
        clip_to_extent="1",
        frame_rate="10",
        force_rhr="0",
    )
    sym.append(_ddp())
    lay = ET.SubElement(
        sym,
        "layer",
        locked="0",
        enabled="1",
        id="",
        **{"class": "SimpleLine", "pass": "0"},  # type: ignore[arg-type]
    )
    lay.append(
        _opt_map(
            {
                "align_dash_pattern": "0",
                "capstyle": "square",
                "customdash": "5;2",
                "customdash_map_unit_scale": _SCALE,
                "customdash_unit": "MM",
                "dash_pattern_offset": "0",
                "dash_pattern_offset_map_unit_scale": _SCALE,
                "dash_pattern_offset_unit": "MM",
                "draw_inside_polygon": "0",
                "joinstyle": "miter",
                "line_color": "0,0,0,255,rgb:0,0,0,1",
                "line_style": "solid",
                "line_width": "0.3",
                "line_width_unit": "MM",
                "offset": "0",
                "offset_map_unit_scale": _SCALE,
                "offset_unit": "MM",
                "ring_filter": "0",
                "trim_distance_end": "0",
                "trim_distance_end_map_unit_scale": _SCALE,
                "trim_distance_end_unit": "MM",
                "trim_distance_start": "0",
                "trim_distance_start_map_unit_scale": _SCALE,
                "trim_distance_start_unit": "MM",
                "tweak_dash_pattern_on_corners": "0",
                "use_custom_dash": "0",
                "width_map_unit_scale": _SCALE,
            }
        )
    )
    lay.append(_ddp())
    return sym


# ── QPT item builders ─────────────────────────────────────────────────────────


def _qpt_page_collection(page: PrintPage) -> ET.Element:
    """Return a <PageCollection> element for the print layout page."""
    pc = ET.Element("PageCollection")
    pc.append(_white_fill_sym())
    page_uuid = _qpt_uuid()
    pi = ET.SubElement(
        pc,
        "LayoutItem",
        position=_pos(0, 0),
        size=_sz(page.width_mm, page.height_mm),
        uuid=page_uuid,
        templateUuid=page_uuid,
        type="65638",
        positionOnPage=_pos(0, 0),
        zValue="0",
        frame="false",
        visibility="1",
        background="true",
        outlineWidthM="0.3,mm",
        referencePoint="0",
        itemRotation="0",
        positionLock="false",
        opacity="1",
        blendMode="0",
        frameJoinStyle="miter",
        excludeFromExports="0",
        groupUuid="",
        id="",
    )
    _frame_bg(pi)
    pi.append(_layout_object())
    pi.append(_white_fill_sym())
    ET.SubElement(pc, "GuideCollection", visible="1")
    return pc


def _qpt_label(
    text: str,
    x: float,
    y: float,
    w: float,
    h: float,
    font_size: int,
    halign: int,
    valign: int,
    z: int,
    named_style: str = "",
) -> ET.Element:
    """Return a <LayoutItem> text label positioned at (x, y) with size (w, h)."""
    item_uuid = _qpt_uuid()
    el = ET.Element(
        "LayoutItem",
        type="65641",
        position=_pos(x, y),
        size=_sz(w, h),
        uuid=item_uuid,
        templateUuid=item_uuid,
        positionOnPage=_pos(x, y),
        zValue=str(z),
        frame="false",
        visibility="1",
        background="false",
        outlineWidthM="0.3,mm",
        referencePoint="0",
        itemRotation="0",
        positionLock="false",
        opacity="1",
        blendMode="0",
        frameJoinStyle="miter",
        excludeFromExports="0",
        groupUuid="",
        id="",
        labelText=text,
        halign=str(halign),
        valign=str(valign),
        htmlState="0",
        marginX="0",
        marginY="0",
    )
    _frame_bg(el)
    el.append(_layout_object())
    el.append(_text_style(font_size, named_style=named_style))
    return el


def _qpt_north_arrow(na: PrintNorthArrow, map_uuid: str, z: int) -> ET.Element:
    """Return a <LayoutItem> north arrow element linked to map_uuid."""
    item_uuid = _qpt_uuid()
    el = ET.Element(
        "LayoutItem",
        type="65640",
        position=_pos(na.x_mm, na.y_mm),
        size=_sz(na.width_mm, na.height_mm),
        uuid=item_uuid,
        templateUuid=item_uuid,
        positionOnPage=_pos(na.x_mm, na.y_mm),
        zValue=str(z),
        frame="false",
        visibility="1",
        background="false",
        outlineWidthM="0.3,mm",
        referencePoint="0",
        itemRotation="0",
        positionLock="false",
        opacity="1",
        blendMode="0",
        frameJoinStyle="miter",
        excludeFromExports="0",
        groupUuid="",
        id="North Arrow",
        file=na.svg,
        mapUuid=map_uuid,
        northMode="0",
        northOffset="0",
        pictureRotation="0",
        pictureWidth="7.7844",
        pictureHeight="9.82621",
        svgBorderWidth="0.2",
        svgFillColor="255,255,255,255,rgb:1,1,1,1",
        svgBorderColor="0,0,0,255,rgb:0,0,0,1",
        anchorPoint="0",
        resizeMode="0",
        mode="2",
    )
    _frame_bg(el)
    el.append(_layout_object())
    return el


def _qpt_scale_bar(sb: PrintScaleBar, map_uuid: str, z: int) -> ET.Element:
    """Return a <LayoutItem> scale bar element linked to map_uuid."""
    item_uuid = _qpt_uuid()
    el = ET.Element(
        "LayoutItem",
        type="65646",
        position=_pos(sb.x_mm, sb.y_mm),
        size=_sz(45.5859, 13.0962),
        uuid=item_uuid,
        templateUuid=item_uuid,
        positionOnPage=_pos(sb.x_mm, sb.y_mm),
        zValue=str(z),
        frame="false",
        visibility="1",
        background="false",
        outlineWidthM="0.3,mm",
        outlineWidth="0.3",
        referencePoint="0",
        itemRotation="0",
        positionLock="false",
        opacity="1",
        blendMode="0",
        frameJoinStyle="miter",
        lineJoinStyle="miter",
        lineCapStyle="square",
        excludeFromExports="0",
        groupUuid="",
        id="",
        mapUuid=map_uuid,
        unitType=sb.unit_type,
        unitLabel=sb.unit_type,
        numUnitsPerSegment=str(sb.num_units_per_segment),
        numSegments=str(sb.num_segments),
        numSegmentsLeft="0",
        numSubdivisions="1",
        style=sb.style,
        boxContentSpace="1",
        minBarWidth="50",
        maxBarWidth="150",
        segmentSizeMode="0",
        labelHorizontalPlacement="0",
        labelVerticalPlacement="0",
        labelBarSpace="3",
        subdivisionsHeight="1.5",
        height="3",
        method="HorizontalMiddle",
        numMapUnitsPerScaleBarUnit="1",
        segmentMillimeters="0",
        alignment="0",
    )
    _frame_bg(el)
    el.append(_layout_object())
    el.append(_text_style(12))
    ET.SubElement(el, "strokeColor", alpha="255", blue="0", red="0", green="0")
    nf = ET.SubElement(el, "numericFormat", id="basic")
    nf_opt = ET.SubElement(nf, "Option", type="Map")
    ET.SubElement(nf_opt, "Option", type="invalid", name="decimal_separator")
    ET.SubElement(nf_opt, "Option", type="int", value="6", name="decimals")
    ET.SubElement(nf_opt, "Option", type="int", value="0", name="rounding_type")
    ET.SubElement(nf_opt, "Option", type="bool", value="false", name="show_plus")
    ET.SubElement(
        nf_opt, "Option", type="bool", value="true", name="show_thousand_separator"
    )
    ET.SubElement(
        nf_opt, "Option", type="bool", value="false", name="show_trailing_zeros"
    )
    ET.SubElement(nf_opt, "Option", type="invalid", name="thousand_separator")
    ET.SubElement(el, "fillColor", alpha="255", blue="0", red="0", green="0")
    ET.SubElement(el, "fillColor2", alpha="255", blue="255", red="255", green="255")
    for tag in ("lineSymbol", "divisionLineSymbol", "subdivisionLineSymbol"):
        wrapper = ET.SubElement(el, tag)
        wrapper.append(_simple_line_sym())
    fs1 = ET.SubElement(el, "fillSymbol1")
    fs1.append(_solid_fill_sym("0,0,0,255,rgb:0,0,0,1"))
    fs2 = ET.SubElement(el, "fillSymbol2")
    fs2.append(_solid_fill_sym("255,255,255,255,rgb:1,1,1,1"))
    return el


def _qpt_legend(leg: PrintLegend, spec: Project, map_uuid: str, z: int) -> ET.Element:
    """Return a <LayoutItem> legend element linked to map_uuid."""
    item_uuid = _qpt_uuid()
    el = ET.Element(
        "LayoutItem",
        type="65642",
        position=_pos(leg.x_mm, leg.y_mm),
        size=_sz(52.8029, 23.4825),
        uuid=item_uuid,
        templateUuid=item_uuid,
        positionOnPage=_pos(leg.x_mm, leg.y_mm),
        zValue=str(z),
        frame="false",
        visibility="1",
        background="true",
        outlineWidthM="0.3,mm",
        referencePoint="0",
        itemRotation="0",
        positionLock="false",
        opacity="1",
        blendMode="0",
        frameJoinStyle="miter",
        excludeFromExports="0",
        groupUuid="",
        id="",
        map_uuid=map_uuid,
        resizeToContents="1",
        title="",
        wmsLegendHeight="25",
        wmsLegendWidth="50",
        wrapChar="",
        columnCount="1",
        columnSpace="2",
        boxSpace="2",
        symbolWidth="7",
        symbolHeight="4",
        minSymbolSize="0",
        maxSymbolSize="0",
        rasterBorder="1",
        rasterBorderWidth="0",
        rasterBorderColor="0,0,0,255,rgb:0,0,0,1",
        equalColumnWidth="0",
        splitLayer="0",
        legendFilterByAtlas="0",
        symbolAlignment="1",
        titleAlignment="1",
    )
    _frame_bg(el)
    el.append(_layout_object())

    styles = ET.SubElement(el, "styles")
    legend_styles = [
        ("title", 16, {"marginBottom": "3.5"}, 1.1),
        ("group", 14, {"marginTop": "3"}, 1.1),
        ("subgroup", 12, {"marginTop": "3"}, 1.1),
        ("symbol", 10, {"marginTop": "2.5"}, 1.0),
        ("symbolLabel", 12, {"marginTop": "2", "marginLeft": "2"}, 1.1),
    ]
    for name, size, margins, mh in legend_styles:
        style_el = ET.SubElement(
            styles,
            "style",
            name=name,
            alignment="1",
            indent="0",
            **margins,  # type: ignore[arg-type]
        )
        style_el.append(_text_style(size, multiline_height=mh))

    ltg = ET.SubElement(el, "layer-tree-group")
    cp_el = ET.SubElement(ltg, "customproperties")
    ET.SubElement(cp_el, "Option")

    for layer in spec.layers:
        ltl = ET.SubElement(
            ltg,
            "layer-tree-layer",
            providerKey=layer.provider,
            legend_split_behavior="0",
            checked="Qt::Checked",
            patch_size="-1,-1",
            name=layer.name,
            source=layer.source,
            expanded="1",
            id=layer.id,
            legend_exp="",
        )
        cp2 = ET.SubElement(ltl, "customproperties")
        opt = ET.SubElement(cp2, "Option", type="Map")
        ET.SubElement(
            opt, "Option", name="cached_name", value=layer.name, type="QString"
        )
        if layer.provider == "wms":
            ET.SubElement(
                opt, "Option", name="legend/title-style", value="hidden", type="QString"
            )

    custom_order = ET.SubElement(ltg, "custom-order", enabled="0")
    for layer in spec.layers:
        item = ET.SubElement(custom_order, "item")
        item.text = layer.id

    return el


def _qpt_map_frame(
    mf: PrintMapFrame, spec: Project, map_uuid: str, z: int
) -> ET.Element:
    """Return a <LayoutItem> map frame element containing spec's extent."""
    attrs: dict[str, str] = dict(
        type="65639",
        position=_pos(mf.x_mm, mf.y_mm),
        size=_sz(mf.width_mm, mf.height_mm),
        uuid=map_uuid,
        templateUuid=map_uuid,
        positionOnPage=_pos(mf.x_mm, mf.y_mm),
        zValue=str(z),
        frame="false",
        visibility="1",
        background="true",
        outlineWidthM="0.3,mm",
        referencePoint="0",
        itemRotation="0",
        positionLock="false",
        opacity="1",
        blendMode="0",
        frameJoinStyle="miter",
        excludeFromExports="0",
        groupUuid="",
        id="Map 1",
        mapFlags="0",
        enableZRange="0",
        drawCanvasItems="true",
        mapRotation="0",
        followPresetName="",
        keepLayerSet="false",
        followPreset="false",
        isTemporal="0",
        labelMargin="0,mm",
    )
    if mf.scale is not None:
        attrs["scale"] = str(mf.scale)
    el = ET.Element("LayoutItem", **attrs)  # type: ignore[arg-type]
    _frame_bg(el)
    el.append(_layout_object())
    if spec.extent:
        xmin, ymin, xmax, ymax = spec.extent
        ET.SubElement(
            el,
            "Extent",
            xmin=str(xmin),
            xmax=str(xmax),
            ymin=str(ymin),
            ymax=str(ymax),
        )
    ET.SubElement(el, "LayerSet")
    ET.SubElement(
        el, "AtlasMap", margin="0.10000000000000001", atlasDriven="0", scalingMode="2"
    )
    ET.SubElement(el, "labelBlockingItems")
    acs = ET.SubElement(
        el,
        "atlasClippingSettings",
        forceLabelsInside="0",
        enabled="0",
        restrictLayers="0",
        clippingType="1",
    )
    ET.SubElement(acs, "layersToClip")
    ET.SubElement(
        el,
        "itemClippingSettings",
        clipSource="",
        forceLabelsInside="0",
        enabled="0",
        clippingType="1",
    )
    return el


def render_print_layout(spec: Project, project_dir: Path) -> None:
    """Render spec's print_layout to output/print.qpt inside project_dir."""
    assert spec.print_layout is not None
    pl = spec.print_layout
    map_uuid = _qpt_uuid()

    root = ET.Element(
        "Layout",
        units="mm",
        printResolution=str(pl.page.resolution_dpi),
        name=pl.name,
        worldFileMap=map_uuid,
    )
    ET.SubElement(
        root,
        "Snapper",
        tolerance="5",
        snapToGrid="0",
        snapToGuides="1",
        snapToItems="1",
    )
    ET.SubElement(
        root,
        "Grid",
        offsetX="0",
        offsetY="0",
        resolution="10",
        resUnits="mm",
        offsetUnits="mm",
    )
    root.append(_qpt_page_collection(pl.page))

    # z order: credits=6, scale bar=5, north=4, legend=3, title=2, map=1
    root.append(
        _qpt_label(
            text=pl.credits_text,
            x=194.142,
            y=204.269,
            w=80.3963,
            h=8.03694,
            font_size=10,
            halign=1,
            valign=32,
            z=6,
        )
    )
    root.append(_qpt_scale_bar(pl.scale_bar, map_uuid, z=5))
    root.append(_qpt_north_arrow(pl.north_arrow, map_uuid, z=4))
    root.append(_qpt_legend(pl.legend, spec, map_uuid, z=3))
    root.append(
        _qpt_label(
            text=pl.title_text,
            x=1.764,
            y=2.382,
            w=265.774,
            h=10.422,
            font_size=30,
            halign=4,
            valign=128,
            z=2,
            named_style="Regular",
        )
    )
    root.append(_qpt_map_frame(pl.map_frame, spec, map_uuid, z=1))

    cp = ET.SubElement(root, "customproperties")
    m = ET.SubElement(cp, "Option", type="Map")
    ET.SubElement(m, "Option", name="atlasRasterFormat", value="png", type="QString")
    ET.SubElement(m, "Option", name="singleFile", value="true", type="bool")
    ET.SubElement(
        root,
        "Atlas",
        sortFeatures="0",
        pageNameExpression="",
        filenamePattern="'output_'||@atlas_featurenumber",
        enabled="0",
        hideCoverage="0",
        coverageLayer="",
        filterFeatures="0",
    )

    ET.indent(root, space=" ")
    output_dir = project_dir / "output"
    output_dir.mkdir(exist_ok=True)
    out = output_dir / f"{pl.name}.qpt"
    out.write_text(ET.tostring(root, encoding="unicode"))
    print(f"Wrote {out}")
