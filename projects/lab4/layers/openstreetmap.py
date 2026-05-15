from pathlib import Path

from alidade.models import Layer

openstreetmap = Layer(
    id="openstreetmap",
    name="OpenStreetMap",
    type="raster",
    source=(
        "<GDAL_WMS>\n"
        '  <Service name="TMS">\n'
        "    <ServerUrl>"
        "http://tile.openstreetmap.org/${z}/${x}/${y}.png"
        "</ServerUrl>\n"
        "  </Service>\n"
        "  <DataWindow>\n"
        "    <UpperLeftX>-20037508.34</UpperLeftX>\n"
        "    <UpperLeftY>20037508.34</UpperLeftY>\n"
        "    <LowerRightX>20037508.34</LowerRightX>\n"
        "    <LowerRightY>-20037508.34</LowerRightY>\n"
        "    <TileLevel>19</TileLevel>\n"
        "    <TileCountX>1</TileCountX>\n"
        "    <TileCountY>1</TileCountY>\n"
        "    <YOrigin>top</YOrigin>\n"
        "  </DataWindow>\n"
        "  <Projection>EPSG:3857</Projection>\n"
        "  <BlockSizeX>256</BlockSizeX>\n"
        "  <BlockSizeY>256</BlockSizeY>\n"
        "  <BandsCount>3</BandsCount>\n"
        "  <Cache />\n"
        "</GDAL_WMS>\n"
    ),
    provider="gdal",
    crs="EPSG:3857",
    visible=True,
    style_xml=Path("styles/openstreetmap.xml"),
)
