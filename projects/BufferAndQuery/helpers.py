"""Processing helpers for the BufferAndQuery project."""

import subprocess
import tempfile
from pathlib import Path


def filter_capitol_buffers_near_parks(inputs: list[Path], output: Path) -> None:
    """Filter capitol buffers to those intersecting ≥1 national park; print count.

    Writes a temporary OGR VRT combining both shapefiles so ogr2ogr can run a
    cross-layer SQLite/SpatiaLite EXISTS query without requiring a single source.

    inputs[0]: output/capitol_buffer.shp
    inputs[1]: output/national_parks.shp
    """
    vrt = (
        "<OGRVRTDataSource>"
        "<OGRVRTLayer name='capitol_buffer'>"
        f"<SrcDataSource>{inputs[0].resolve()}</SrcDataSource>"
        "</OGRVRTLayer>"
        "<OGRVRTLayer name='national_parks'>"
        f"<SrcDataSource>{inputs[1].resolve()}</SrcDataSource>"
        "</OGRVRTLayer>"
        "</OGRVRTDataSource>"
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".vrt", delete=False) as fh:
        vrt_path = Path(fh.name)
        fh.write(vrt)
    try:
        subprocess.run(
            [
                "ogr2ogr",
                "-dialect",
                "sqlite",
                "-sql",
                "SELECT cb.* FROM capitol_buffer cb"
                " WHERE EXISTS (SELECT 1 FROM national_parks np"
                " WHERE ST_Intersects(cb.geometry, np.geometry))",
                str(output),
                str(vrt_path),
            ],
            check=True,
        )
    finally:
        vrt_path.unlink(missing_ok=True)

    info = subprocess.run(
        ["ogrinfo", "-al", "-so", str(output)],
        capture_output=True,
        text=True,
        check=True,
    )
    for line in info.stdout.splitlines():
        if line.startswith("Feature Count:"):
            count = int(line.split(":")[1].strip())
            print(
                f"State capitols with 25-mile buffer intersecting a national park:"
                f" {count}"
            )
            break


def filter_national_parks(inputs: list[Path], output: Path) -> None:
    """Filter USAParks.shp to FCC='D83' (National Park Service units) with ogr2ogr."""
    subprocess.run(
        [
            "ogr2ogr",
            "-where",
            "FCC='D83'",
            str(output),
            str(inputs[0]),
        ],
        check=True,
    )
