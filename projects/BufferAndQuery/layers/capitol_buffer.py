from pathlib import Path

from models import Layer, ProcessingStep, ShellAction, SimpleFill, SingleSymbol, Symbol

capitol_buffer = Layer(
    id="capitol_buffer",
    name="State Capitol 25-Mile Buffer",
    type="vector",
    source="./output/capitol_buffer.shp",
    provider="ogr",
    crs="EPSG:3857",
    visible=True,
    geometry_type="Polygon",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            layers=[
                SimpleFill(
                    color="100,150,255,80",
                    outline_color="0,80,200,255",
                    outline_width=0.8,
                )
            ],
        )
    ),
    processing_step=ProcessingStep(
        description=(
            "Buffer each State Capitol building point by 25 miles (40,233.6 m in"
            " EPSG:3857) using gdal vector buffer."
        ),
        action=ShellAction(
            command="gdal vector buffer --distance 40233.6 --overwrite {input} {output}"
        ),
        depends_on=["state_capitol_bldgs"],
        output=Path("output/capitol_buffer.shp"),
    ),
)
