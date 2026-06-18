"""
Fine scale vegetation map
"""

import os
from pathlib import Path

import geopandas as gpd

from alidade.models import (
    BoundLayer,
    Layer,
    PythonAction,
    RuleRenderer,
    SimpleFill,
    Symbol,
)
from projects.goats.layers.border import border
from projects.goats.palette import VEG_EDGE
from projects.goats.util import (
    BBOX_GENERAL,
    CRS,
    VEGETATION_VALUE_TO_LABEL,
    VEGETATION_ZONES,
    clip_border,
    vegetation_rules,
)

GDB_LAYER = "CRUZ_CLARA_FINESCALE_VEG_6_15_2023"


def crop_vegetation_to_bbox() -> None:
    """Crop county-wide vegetation GDB to project bounding box; output as .gpkg.

    Run once before the pipeline to reduce the 400 MB+ GDB to a small park-only
    file.  Prints size before and after.
    """
    src_path = "projects/goats/data/fine_scale_vegetation.gdb"
    dst_path = "projects/goats/data/fine_scale_vegetation_bbox.gpkg"

    src_size = (
        sum(f.stat().st_size for f in Path(src_path).rglob("*") if f.is_file()) / 1e6
    )

    xmin, ymin, xmax, ymax = BBOX_GENERAL
    gdf = (
        gpd.read_file(src_path, layer=GDB_LAYER)
        .to_crs("EPSG:4326")
        .cx[xmin:xmax, ymin:ymax]
    )
    gdf.to_file(dst_path, driver="GPKG")

    dst_size = os.path.getsize(dst_path) / 1e6
    print(f"  fine_scale_vegetation: {src_size:.0f} MB → {dst_size:.1f} MB")


def clip_vegetation(layer: BoundLayer) -> None:
    """Reproject, clip, and dissolve fine-scale vegetation by lifeform category."""
    (border,) = layer.inputs
    gdf = gpd.read_file(layer.raw_path).to_crs(CRS)
    clipped = clip_border(gdf, border.path)
    clipped["veg_class"] = clipped["ENHANCED_LIFEFORM"].map(VEGETATION_VALUE_TO_LABEL)
    dissolved = (
        clipped[["veg_class", "geometry"]].dissolve(by="veg_class").reset_index()
    )
    dissolved.to_file(layer.path, driver="GPKG")


_symbols = [
    Symbol(
        type="fill",
        layers=[
            SimpleFill(
                color=zone.color.with_alpha(200),
                style="solid",
                outline_color=VEG_EDGE,
                outline_width=0,
            )
        ],
    )
    for zone in VEGETATION_ZONES
]

vegetation = Layer(
    id="fine_scale_vegetation",
    name="Fine-Scale Vegetation (2020)",
    type="vector",
    inputs=[border],
    raw_file="data/fine_scale_vegetation_bbox.gpkg",
    source_description=(
        "121-class NVC vegetation map, 2020; 309,785 polygons"
        " county-wide, 343 within park"
    ),
    source_origin="Santa Cruz / Santa Clara County, EPSG:6420",
    datasource="output/vegetation.gpkg|layername=vegetation",
    crs=CRS,
    geometry_type="MultiPolygon",
    renderer=RuleRenderer(
        rules_key="veg",
        rules=vegetation_rules,
        symbols=_symbols,
    ),
    action=PythonAction(fn=clip_vegetation),
)


if __name__ == "__main__":
    # run via `uv run projects/goats/layers/vegetation.py`
    crop_vegetation_to_bbox()
