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
from projects.goats.util import (
    CRS,
    clip_border,
    hex_to_rgba,
    VEGETATION_ZONES,
    vegetation_rules,
)

_GDB_LAYER = "CRUZ_CLARA_FINESCALE_VEG_6_15_2023"


def clip_vegetation(layer: BoundLayer) -> None:
    """Reproject, clip, and dissolve fine-scale vegetation by lifeform category."""
    (border,) = layer.inputs
    gdf = gpd.read_file(layer.raw_path, layer=_GDB_LAYER).to_crs(CRS)
    clipped = clip_border(gdf, border.path)
    dissolved = (
        clipped[["ENHANCED_LIFEFORM", "geometry"]]
        .dissolve(by="ENHANCED_LIFEFORM")
        .reset_index()
    )
    dissolved.to_file(layer.path, driver="GPKG")


_symbols = [
    Symbol(
        type="fill",
        layers=[
            SimpleFill(
                color=hex_to_rgba(color, 200),
                style="solid",
                outline_color="80,80,80,120",
                outline_width=0,
            )
        ],
    )
    for _, _, color in VEGETATION_ZONES
]

vegetation = Layer(
    id="fine_scale_vegetation",
    name="Fine-Scale Vegetation (2020)",
    type="vector",
    inputs=[border],
    raw_file="data/fine_scale_vegetation.gdb",
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
