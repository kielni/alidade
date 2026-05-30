"""Render project.py → output/project.aprx (ArcGIS Pro CIM v3.4.0 ZIP archive).

DocumentInfo.xml and Metadata/*.xml are real XML.
All other CIM documents (map, layers, Ground) are JSON with .json extension.
"""

import json
import uuid
import warnings
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any

from pyproj import CRS as ProjCRS

from alidade.models import (
    ArcGISProject,
    GraduatedRenderer,
    Layer,
    SimpleFill,
    SimpleLine,
    SingleSymbol,
)

# Esri legacy wkid aliases where wkid != latestWkid (latestWkid → wkid).
_ESRI_WKID_ALIASES: dict[int, int] = {
    2227: 102643,  # NAD83 / California zone 3 (US survey feet)
    3857: 102100,  # Web Mercator
    3785: 102113,  # Web Mercator (deprecated)
}

# Extended spatial reference fields for known wkids (from ArcGIS Pro CIM export).
_SR_EXTRA: dict[int, dict[str, Any]] = {
    102643: {
        "xyTolerance": 0.0032808333333333331,
        "zTolerance": 0.001,
        "mTolerance": 0.001,
        "falseX": -115860600,
        "falseY": -93269500,
        "xyUnits": 3048.00609601219185,
        "falseZ": -100000,
        "zUnits": 10000,
        "falseM": -100000,
        "mUnits": 10000,
    },
}

# WGS84/NAD83 datum transforms added by ArcGIS Pro for projected CRS maps.
_NAD83_DATUM_TRANSFORMS = [
    {
        "type": "CIMDatumTransform",
        "forward": True,
        "geoTransformation": {
            "geoTransforms": [
                {
                    "wkid": 108190,
                    "latestWkid": 108190,
                    "transformForward": True,
                    "name": "WGS_1984_(ITRF00)_To_NAD_1983",
                }
            ]
        },
    },
    {
        "type": "CIMDatumTransform",
        "forward": False,
        "geoTransformation": {
            "geoTransforms": [
                {
                    "wkid": 108190,
                    "latestWkid": 108190,
                    "transformForward": True,
                    "name": "WGS_1984_(ITRF00)_To_NAD_1983",
                }
            ]
        },
    },
]


def _rgb_color(color_str: str) -> dict[str, Any]:
    """Return a CIMRGBColor dict from 'R,G,B,A'. A is 0-255 → 0-100."""
    parts = color_str.split(",")
    r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
    a_100 = round(int(parts[3]) / 255 * 100) if len(parts) > 3 else 100
    return {"type": "CIMRGBColor", "values": [r, g, b, a_100]}


def _sr_dict(crs_str: str) -> dict[str, Any]:
    """Return a WKID-based spatialReference dict from a CRS string."""
    crs = ProjCRS.from_user_input(crs_str)
    epsg = crs.to_epsg()
    if epsg is None:
        raise ValueError(
            f"Cannot determine EPSG WKID for {crs_str!r}; "
            "use an EPSG-registered CRS for ArcGIS Pro output."
        )
    wkid = _ESRI_WKID_ALIASES.get(epsg, epsg)
    result: dict[str, Any] = {"wkid": wkid, "latestWkid": epsg}
    result.update(_SR_EXTRA.get(wkid, {}))
    return result


def _cim_source(layer: Layer, project_dir: Path) -> tuple[str, str, str] | None:
    """Return (ws_conn, ws_factory, dataset) tuple or None for tile layers."""
    if layer.provider == "wms":
        return None

    path_part = layer.source.split("|")[0].split("?")[0]
    p = Path(path_part)
    if not p.is_absolute():
        p = (project_dir / p).resolve()

    if layer.arcgispro_workspace is not None:
        return layer.arcgispro_workspace, "Shapefile", p.stem

    if ".gdb" in str(p):
        parts = p.parts
        gdb_idx = next((i for i, pt in enumerate(parts) if pt.endswith(".gdb")), None)
        if gdb_idx is not None:
            gdb_path = Path(*parts[: gdb_idx + 1])
            dataset = parts[gdb_idx + 1] if gdb_idx + 1 < len(parts) else p.stem
            try:
                conn = f"DATABASE=.\\{gdb_path.relative_to(project_dir)}"
            except ValueError:
                conn = f"DATABASE={gdb_path}"
            return conn, "FileGDB", dataset

    if p.suffix.lower() == ".shp" or ".shp|" in layer.source:
        try:
            conn = f"DATABASE=.\\{p.parent.relative_to(project_dir)}"
        except ValueError:
            conn = f"DATABASE={p.parent}"
        return conn, "Shapefile", p.stem

    warnings.warn(
        f"Layer {layer.id!r}: cannot translate source {layer.source!r} to "
        "ArcGIS Pro data connection; set arcgispro_workspace or use .shp / .gdb.",
        stacklevel=3,
    )
    return None


def _solid_stroke(color_str: str, width: float) -> dict[str, Any]:
    return {
        "type": "CIMSolidStroke",
        "enable": True,
        "capStyle": "Round",
        "joinStyle": "Round",
        "miterLimit": 10,
        "width": width,
        "color": _rgb_color(color_str),
    }


def _cim_simple_renderer(layer: Layer) -> dict[str, Any] | None:
    """Build CIMSimpleRenderer for SingleSymbol+SimpleFill/Line; None otherwise."""
    if not isinstance(layer.renderer, SingleSymbol) or not layer.renderer.symbol.layers:
        return None
    first = layer.renderer.symbol.layers[0]

    if isinstance(first, SimpleFill):
        return {
            "type": "CIMSimpleRenderer",
            "patch": "Default",
            "symbol": {
                "type": "CIMSymbolReference",
                "symbol": {
                    "type": "CIMPolygonSymbol",
                    "symbolLayers": [
                        {
                            "type": "CIMSolidFill",
                            "enable": True,
                            "color": _rgb_color(first.color),
                        },
                        _solid_stroke(first.outline_color, first.outline_width),
                    ],
                },
            },
        }

    if isinstance(first, SimpleLine):
        return {
            "type": "CIMSimpleRenderer",
            "patch": "Default",
            "symbol": {
                "type": "CIMSymbolReference",
                "symbol": {
                    "type": "CIMLineSymbol",
                    "symbolLayers": [
                        _solid_stroke(first.line_color, first.line_width),
                    ],
                },
            },
        }

    return None


def _cim_graduated_renderer(layer: Layer) -> dict[str, Any] | None:
    """Build CIMClassBreaksRenderer for GraduatedRenderer; None otherwise."""
    if not isinstance(layer.renderer, GraduatedRenderer):
        return None
    r = layer.renderer
    breaks = []
    for gr in r.ranges:
        breaks.append(
            {
                "type": "CIMClassBreak",
                "label": gr.label,
                "patch": "Default",
                "symbol": {
                    "type": "CIMSymbolReference",
                    "symbol": {
                        "type": "CIMPolygonSymbol",
                        "symbolLayers": [
                            {
                                "type": "CIMSolidFill",
                                "enable": True,
                                "color": _rgb_color(gr.color),
                            },
                            _solid_stroke(r.outline_color, r.outline_width),
                        ],
                    },
                },
                "upperBound": gr.upper,
            }
        )
    return {
        "type": "CIMClassBreaksRenderer",
        "classBreakType": "GraduatedColor",
        "field": r.attr,
        "minimumBreak": r.ranges[0].lower,
        "breaks": breaks,
    }


_CIM_TYPENS = "http://www.esri.com/schemas/ArcGIS/3.4.0"
_CIM_VERSION = "3.4.0"
_CIM_BUILD = "55405"


def _build_document_info() -> bytes:
    """Return DocumentInfo.xml bytes with full namespace declarations."""
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        "<CIMDocumentInfo"
        " xsi:type='typens:CIMDocumentInfo'"
        " xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'"
        " xmlns:xs='http://www.w3.org/2001/XMLSchema'"
        f" xmlns:typens='{_CIM_TYPENS}'>"
        f"<Version>{_CIM_VERSION}</Version>"
        f"<Build>{_CIM_BUILD}</Build>"
        "<DocumentTitle>alidade-generated.aprx</DocumentTitle>"
        "<SavePreview>false</SavePreview>"
        "<UseRelativePath>true</UseRelativePath>"
        "<Antialiasing>esriBGLAntialiasingNone</Antialiasing>"
        "<TextAntialiasing>esriBGLTextAAliasForce</TextAntialiasing>"
        "</CIMDocumentInfo>"
    ).encode("utf-8")


def _build_gis_project(map_cimpath: str) -> dict[str, Any]:
    return {
        "type": "CIMGISProject",
        "views": [
            {
                "type": "CIMMapView",
                "viewableObjectPath": map_cimpath,
                "viewType": "esri_mapping_mapPane",
                "instanceID": 1,
                "viewingMode": "Map",
            }
        ],
    }


def _build_ground_json() -> dict[str, Any]:
    return {
        "type": "CIMElevationSurfaceLayer",
        "name": "Ground",
        "uRI": "CIMPATH=map/Ground.json",
        "sourceModifiedTime": {"type": "TimeInstant"},
        "useSourceMetadata": True,
        "description": "Ground",
        "layerType": "Operational",
        "showLegends": False,
        "visibility": True,
        "displayCacheType": "Permanent",
        "maxDisplayCacheAge": 5,
        "showPopups": True,
        "serviceLayerID": -1,
        "refreshRate": -1,
        "refreshRateUnit": "esriTimeUnitsSeconds",
        "blendingMode": "Alpha",
        "allowDrapingOnIntegratedMesh": True,
        "elevationMode": "BaseGlobeSurface",
        "verticalExaggeration": 1,
        "color": {"type": "CIMRGBColor", "values": [255, 255, 255, 100]},
        "surfaceTINShadingMode": "Smooth",
    }


def _build_cim_map(
    spec: ArcGISProject,
    layer_cimpaths: list[str],
    extra_cim_cimpaths: list[str],
    metadata_cimpath: str,
) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "type": "CIMMap",
        "name": spec.title,
        "uRI": "CIMPATH=map/map.json",
        "sourceModifiedTime": {"type": "TimeInstant"},
        "metadataURI": metadata_cimpath,
        "useSourceMetadata": True,
        "layers": layer_cimpaths + extra_cim_cimpaths,
        "datumTransforms": _NAD83_DATUM_TRANSFORMS * 2,
        "defaultViewingMode": "Map",
        "mapType": "Map",
        "groundElevationSurfaceLayer": "CIMPATH=map/Ground.json",
        "spatialReference": _sr_dict(spec.crs),
    }

    if spec.extent:
        xmin, ymin, xmax, ymax = spec.extent
        doc["defaultExtent"] = {
            "xmin": xmin,
            "ymin": ymin,
            "xmax": xmax,
            "ymax": ymax,
            "spatialReference": _sr_dict(spec.crs),
        }

    return doc


def _build_feature_layer(layer: Layer, project_dir: Path) -> dict[str, Any]:
    cimpath = f"CIMPATH=map/{layer.id.lower()}.json"
    doc: dict[str, Any] = {
        "type": "CIMFeatureLayer",
        "name": layer.name,
        "uRI": cimpath,
        "sourceModifiedTime": {"type": "TimeInstant"},
        "useSourceMetadata": True,
        "description": layer.name,
        "layerElevation": {
            "type": "CIMLayerElevationSurface",
            "elevationSurfaceLayerURI": "CIMPATH=map/Ground.json",
        },
        "expanded": True,
        "layerType": "Operational",
        "showLegends": True,
        "visibility": layer.visible,
        "displayCacheType": "Permanent",
        "maxDisplayCacheAge": 5,
        "showPopups": True,
        "serviceLayerID": -1,
        "refreshRate": -1,
        "refreshRateUnit": "esriTimeUnitsSeconds",
        "blendingMode": "Alpha",
        "allowDrapingOnIntegratedMesh": True,
        "autoGenerateFeatureTemplates": True,
        "featureElevationExpression": "0",
        "htmlPopupEnabled": True,
        "selectable": True,
        "featureCacheType": "Session",
        "displayFiltersType": "ByScale",
        "featureBlendingMode": "Alpha",
        "layerEffectsMode": "Layer",
        "labelVisibility": False,
        "scaleSymbols": True,
        "snappable": True,
    }

    conn = _cim_source(layer, project_dir)
    if conn:
        ws_str, ws_factory, dataset = conn
        doc["featureTable"] = {
            "type": "CIMFeatureTable",
            "displayField": "OBJECTID",
            "editable": True,
            "dataConnection": {
                "type": "CIMStandardDataConnection",
                "workspaceConnectionString": ws_str,
                "workspaceFactory": ws_factory,
                "dataset": dataset,
                "datasetType": "esriDTFeatureClass",
            },
            "studyAreaSpatialRel": "esriSpatialRelUndefined",
            "searchOrder": "esriSearchOrderSpatial",
        }

    renderer = _cim_simple_renderer(layer) or _cim_graduated_renderer(layer)
    if renderer is not None:
        doc["renderer"] = renderer

    return doc


def _build_metadata() -> tuple[str, ET.Element]:
    meta_uuid = uuid.uuid4().hex
    root = ET.Element("metadata")
    root.set("xml:lang", "en")
    esri = ET.SubElement(root, "Esri")
    ET.SubElement(esri, "ArcGISFormat").text = "1.0"
    data = ET.SubElement(root, "dataIdInfo")
    ET.SubElement(ET.SubElement(data, "idCitation"), "resTitle").text = "Map"
    return meta_uuid, root


def _build_index(
    map_filename: str,
    ground_filename: str,
    feature_layer_filenames: list[str],
    extra_cim_filenames: list[str],
    metadata_filename: str,
) -> dict[str, Any]:
    """Build Index.json — node graph of all documents in the archive."""
    nodes: list[dict[str, Any]] = []
    node_id = 0

    # Extra CIM (basemap tiles) come first, matching original ArcGIS Pro export order.
    extra_ids: list[int] = []
    for fn in extra_cim_filenames:
        eid = node_id
        extra_ids.append(eid)
        nodes.append(
            {
                "NodeId": eid,
                "NodeType": "Layer",
                "FileName": fn,
                "ChildNodeIds": "",
            }
        )
        node_id += 1

    ground_id = node_id
    nodes.append(
        {
            "NodeId": ground_id,
            "NodeType": "Layer",
            "FileName": ground_filename,
            "ChildNodeIds": "",
        }
    )
    node_id += 1

    feature_ids: list[int] = []
    for fn in feature_layer_filenames:
        fid = node_id
        feature_ids.append(fid)
        nodes.append(
            {
                "NodeId": fid,
                "NodeType": "Layer",
                "FileName": fn,
                "ChildNodeIds": str(ground_id),
            }
        )
        node_id += 1

    map_id = node_id
    meta_id = node_id + 1
    # Order matches ArcGIS Pro: Ground, Metadata, extra CIM, feature layers.
    map_child_ids = [ground_id, meta_id] + extra_ids + feature_ids
    nodes.append(
        {
            "NodeId": map_id,
            "NodeType": "Map",
            "FileName": map_filename,
            "ChildNodeIds": ",".join(str(i) for i in map_child_ids),
        }
    )
    node_id += 1

    nodes.append(
        {
            "NodeId": meta_id,
            "NodeType": "BinaryReference",
            "FileName": metadata_filename,
            "ChildNodeIds": "",
        }
    )
    node_id += 1

    return {
        "DocumentType": "Index",
        "MajorVersion": 1,
        "MinorVersion": 0,
        "PatchVersion": 0,
        "NumberOfNodes": node_id,
        "Nodes": nodes,
    }


def _to_xml_bytes(root: ET.Element) -> bytes:
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode").encode("utf-8")


def _to_json_bytes(doc: dict[str, Any]) -> bytes:
    return json.dumps(doc, indent=2).encode("utf-8")


def render_arcgispro(spec: ArcGISProject, project_dir: Path) -> None:
    """Write output/project.aprx from spec."""
    output_dir = project_dir / "output"
    output_dir.mkdir(exist_ok=True)
    out_path = output_dir / "project.aprx"

    feature_files: dict[str, dict[str, Any]] = {}
    layer_cimpaths: list[str] = []
    layer_filenames: list[str] = []
    for la in spec.layers:
        doc = _build_feature_layer(la, project_dir)
        filename = f"map/{la.id.lower()}.json"
        feature_files[filename] = doc
        layer_cimpaths.append(f"CIMPATH={filename}")
        layer_filenames.append(filename)

    extra_cim_files: dict[str, dict[str, Any]] = {}
    extra_cim_cimpaths: list[str] = []
    extra_cim_filenames: list[str] = []
    for cim_doc in spec.arcgispro_extra_cim:
        uri = cim_doc.get("uRI", "")
        filename = uri[len("CIMPATH=") :] if uri.startswith("CIMPATH=") else uri
        extra_cim_files[filename] = cim_doc
        extra_cim_cimpaths.append(uri)
        extra_cim_filenames.append(filename)

    meta_uuid, meta_el = _build_metadata()
    metadata_filename = f"Metadata/{meta_uuid}.xml"
    metadata_cimpath = f"CIMPATH={metadata_filename}"

    map_doc = _build_cim_map(
        spec,
        layer_cimpaths=layer_cimpaths,
        extra_cim_cimpaths=extra_cim_cimpaths,
        metadata_cimpath=metadata_cimpath,
    )
    gis_doc = _build_gis_project("CIMPATH=map/map.json")
    doc_info_bytes = _build_document_info()
    ground_doc = _build_ground_json()
    index_doc = _build_index(
        map_filename="map/map.json",
        ground_filename="map/Ground.json",
        feature_layer_filenames=layer_filenames,
        extra_cim_filenames=extra_cim_filenames,
        metadata_filename=metadata_filename,
    )

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("DocumentInfo.xml", doc_info_bytes)
        zf.writestr("GISProject.json", _to_json_bytes(gis_doc))
        zf.writestr("Index.json", _to_json_bytes(index_doc))
        zf.writestr("map/map.json", _to_json_bytes(map_doc))
        zf.writestr("map/Ground.json", _to_json_bytes(ground_doc))
        for filename, doc in feature_files.items():
            zf.writestr(filename, _to_json_bytes(doc))
        for filename, doc in extra_cim_files.items():
            zf.writestr(filename, _to_json_bytes(doc))
        zf.writestr(metadata_filename, _to_xml_bytes(meta_el))

    print(f"Wrote {out_path}")
