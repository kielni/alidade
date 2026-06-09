"""CIMStandardDataConnection builder for shapefile layers."""

import os
from pathlib import Path
from typing import Any

from alidade.models import Layer


def _resolve_arcgis_path(local_path: Path, project_dir: Path) -> Path:
    """Remap a local absolute path to the ArcGIS machine path.

    If ARCGIS_WORKSPACE_ROOT is set in local.env, paths that are relative to
    project_dir are remapped to ARCGIS_WORKSPACE_ROOT / project_dir.name / <rel>.
    Otherwise the local absolute path is returned unchanged (same machine).
    """
    base = os.environ.get("ARCGIS_WORKSPACE_ROOT")
    if not base:
        return local_path
    try:
        rel = local_path.relative_to(project_dir.resolve())
        return Path(base) / project_dir.name / rel
    except ValueError:
        return local_path


def build_data_connection(layer: Layer, project_dir: Path) -> dict[str, Any]:
    """Return a CIMStandardDataConnection dict for a shapefile layer.

    workspace (DATABASE=<folder>) and dataset (stem) are derived from
    layer.datasource. If ARCGIS_WORKSPACE_ROOT is set, paths relative to
    project_dir are remapped to that root so the .lyrx resolves on the
    ArcGIS machine. Path must be absolute on the ArcGIS machine.
    """
    path_part = layer.datasource.split("|")[0].split("?")[0]
    local_path = Path(path_part)
    if not local_path.is_absolute():
        local_path = (project_dir / local_path).resolve()

    arcgis_path = _resolve_arcgis_path(local_path, project_dir)

    return {
        "type": "CIMStandardDataConnection",
        "workspaceConnectionString": f"DATABASE={arcgis_path.parent}",
        "workspaceFactory": "Shapefile",
        "dataset": arcgis_path.stem,
        "datasetType": "esriDTFeatureClass",
    }
