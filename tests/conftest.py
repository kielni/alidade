"""Pytest fixtures for alidade unit tests."""

from pathlib import Path

import pytest

from alidade.color import Color
from alidade.models import (
    BoundMap,
    Extent,
    GraduatedRange,
    GraduatedRenderer,
    Layer,
    PaletteEntry,
    PalettedRenderer,
    Rule,
    RuleRenderer,
    SimpleFill,
    SimpleLine,
    SimpleMarker,
    SingleSymbol,
    SvgMarker,
    Symbol,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"

PARK_EXTENT = Extent(
    xmin=-121.84, ymin=37.33, xmax=-121.69, ymax=37.46, crs="EPSG:4326"
)

PARK_FILL = Color.from_hex("#ffffff")
PARK_BORDER = Color.from_hex("#6464c8", alpha=180)
ROADS_LINE = Color.from_hex("#784828")
STAGING_FILL = Color.from_hex("#b400ff")
SLOPE_GENTLE = Color.from_hex("#1a9641")
SLOPE_MODERATE = Color.from_hex("#ffffbf")
SLOPE_STEEP = Color.from_hex("#fdae61")
SLOPE_TOO_STEEP = Color.from_hex("#ddd0c0")
RANK_TIER_0 = Color.from_hex("#00c83c")
RANK_TIER_1 = Color.from_hex("#78e65a")
RANK_TIER_2 = Color.from_hex("#e1ff50")


@pytest.fixture
def map_root():
    """Path to tests/fixtures/; used as map_path for all test BoundMaps."""
    return FIXTURES_DIR


@pytest.fixture
def simple_fill_layer() -> Layer:
    return Layer(
        id="simple_fill_layer",
        name="Park Boundary",
        type="vector",
        datasource="park_boundary.geojson",
        geometry_type="Polygon",
        crs="EPSG:4326",
        renderer=SingleSymbol(
            symbol=Symbol(
                type="fill",
                layers=[SimpleFill(color=PARK_FILL, outline_color=PARK_BORDER)],
            )
        ),
    )


@pytest.fixture
def simple_line_layer() -> Layer:
    return Layer(
        id="simple_line_layer",
        name="Roads and Trails",
        type="vector",
        datasource="roads_trails.geojson",
        geometry_type="LineString",
        crs="EPSG:4326",
        renderer=SingleSymbol(
            symbol=Symbol(
                type="line",
                layers=[SimpleLine(line_color=ROADS_LINE, line_width=0.5)],
            )
        ),
    )


@pytest.fixture
def svg_marker_layer() -> Layer:
    return Layer(
        id="svg_marker_layer",
        name="Staging Marker",
        type="vector",
        datasource="staging_ranked.geojson",
        geometry_type="Point",
        crs="EPSG:4326",
        renderer=SingleSymbol(
            symbol=Symbol(
                type="marker",
                layers=[
                    SvgMarker(
                        name="test_marker.svg",
                        color=STAGING_FILL,
                        size=4.0,
                    )
                ],
            )
        ),
    )


@pytest.fixture
def rule_renderer_layer() -> Layer:
    return Layer(
        id="rule_renderer_layer",
        name="Staging Ranked",
        type="vector",
        datasource="staging_ranked.geojson",
        geometry_type="Point",
        crs="EPSG:4326",
        renderer=RuleRenderer(
            rules_key="rank",
            rules=[
                Rule(key="rank1", label="Best", filter='"rank" = 1', symbol_index=0),
                Rule(key="rank2", label="Better", filter='"rank" = 2', symbol_index=1),
                Rule(
                    key="rank3",
                    label="Good",
                    filter='"rank" >= 3',
                    symbol_index=2,
                ),
            ],
            symbols=[
                Symbol(
                    type="marker",
                    layers=[SimpleMarker(color=RANK_TIER_0, size=4.0)],
                ),
                Symbol(
                    type="marker",
                    layers=[SimpleMarker(color=RANK_TIER_1, size=4.0)],
                ),
                Symbol(
                    type="marker",
                    layers=[SimpleMarker(color=RANK_TIER_2, size=4.0)],
                ),
            ],
        ),
    )


@pytest.fixture
def graduated_layer() -> Layer:
    return Layer(
        id="graduated_layer",
        name="Staging Score",
        type="vector",
        datasource="staging_ranked.geojson",
        geometry_type="Point",
        crs="EPSG:4326",
        renderer=GraduatedRenderer(
            attr="score_norm",
            ranges=[
                GraduatedRange(
                    lower=0.0,
                    upper=0.33,
                    label="Low",
                    color=Color.from_hex("#ffffcc"),
                ),
                GraduatedRange(
                    lower=0.33,
                    upper=0.67,
                    label="Medium",
                    color=Color.from_hex("#a1dab4"),
                ),
                GraduatedRange(
                    lower=0.67,
                    upper=1.0,
                    label="High",
                    color=Color.from_hex("#41b6c4"),
                ),
            ],
        ),
    )


@pytest.fixture
def paletted_layer() -> Layer:
    return Layer(
        id="paletted_layer",
        name="Slope",
        type="raster",
        datasource="slope.tif",
        crs="EPSG:26910",
        renderer=PalettedRenderer(
            entries=[
                PaletteEntry(
                    value=1,
                    color=SLOPE_GENTLE,
                    label="Flat to gentle (0-15%)",
                ),
                PaletteEntry(
                    value=2,
                    color=SLOPE_MODERATE,
                    label="Moderate (15-27%)",
                ),
                PaletteEntry(
                    value=3,
                    color=SLOPE_STEEP,
                    label="Steep (27-58%)",
                ),
                PaletteEntry(
                    value=4,
                    color=SLOPE_TOO_STEEP,
                    label="Too steep (58%+)",
                ),
            ]
        ),
    )


@pytest.fixture
def make_map(map_root):
    """Return a factory that builds a BoundMap rooted at map_root."""

    def _make(layers: list[Layer]) -> BoundMap:
        return BoundMap(
            title="Test Map",
            crs="EPSG:4326",
            extent=PARK_EXTENT,
            layers=layers,
            map_path=map_root,
        )

    return _make
