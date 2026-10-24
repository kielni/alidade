"""Raster band statistics shared by the QGIS and PNG renderers."""

from pathlib import Path

import numpy as np
import rasterio

from alidade.models import MultibandColorRenderer


def band_stretch(
    path: Path, renderer: MultibandColorRenderer
) -> list[tuple[float, float]]:
    """Return (low, high) stretch limits for each of renderer's bands, in order.

    Pixels equal to the raster's nodata value are ignored. "minmax" returns
    each band's min and max; "cumulative_cut" its 2nd and 98th percentiles.
    """
    limits: list[tuple[float, float]] = []
    with rasterio.open(path) as ds:
        for band in renderer.bands:
            values = ds.read(band, masked=True).compressed()
            if values.size == 0:
                limits.append((0.0, 1.0))
            elif renderer.stretch == "cumulative_cut":
                low, high = np.percentile(values, [2, 98])
                limits.append((float(low), float(high)))
            else:
                limits.append((float(values.min()), float(values.max())))
    return limits
