from pathlib import Path


def map_dir(map_file: str) -> Path:
    """Return the map directory containing map_file.

    Usage in a map-level file (main.py, etc.):
        from alidade import map_dir
        _DIR = map_dir(__file__)
    """
    return Path(map_file).parent


def map_data_dir(layer_file: str) -> Path:
    """Return the data/ directory for the map containing layer_file.

    Assumes the standard layout: projects/<name>/layers/<layer>.py
    with source data at projects/<name>/data/.

    Usage in a layer file:
        from alidade import map_data_dir
        _CSV = map_data_dir(__file__) / "malls.csv"
    """
    return Path(layer_file).parent.parent / "data"
