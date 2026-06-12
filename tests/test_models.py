"""Tests for model-level invariants: ID padding, CRS reprojection, validation."""

import warnings

from alidade.models import Extent, Layer


def test_id_padding():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        short = Layer(id="myshort", name="Test", type="vector", datasource="x.geojson")
        long = Layer(
            id="my_long_layer_id", name="Test", type="vector", datasource="x.geojson"
        )
    padding_warnings = [x for x in w if "padded" in str(x.message).lower()]
    assert len(padding_warnings) == 1
    assert short.id.startswith("myshort_")
    assert len(short.id) > 10
    assert long.id == "my_long_layer_id"


def test_extent_to_crs_roundtrip():
    src = Extent(xmin=-121.84, ymin=37.33, xmax=-121.69, ymax=37.46, crs="EPSG:4326")
    projected = src.to_crs("EPSG:26910")
    assert projected.crs == "EPSG:26910"
    assert 550_000 < projected.xmin < 650_000
    assert 550_000 < projected.xmax < 650_000
    reprojected = projected.to_crs("EPSG:4326")
    assert abs(reprojected.xmin - src.xmin) < 0.01
    assert abs(reprojected.ymin - src.ymin) < 0.01
