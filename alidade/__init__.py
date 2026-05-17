from pathlib import Path


def project_dir(project_file: str) -> Path:
    """Return the project directory containing project_file.

    Usage in a project-level file (project.py, main.py, etc.):
        from alidade import project_dir
        _DIR = project_dir(__file__)
    """
    return Path(project_file).parent


def project_data_dir(layer_file: str) -> Path:
    """Return the data/ directory for the project containing layer_file.

    Assumes the standard layout: projects/<name>/layers/<layer>.py
    with source data at projects/<name>/data/.

    Usage in a layer file:
        from alidade import project_data_dir
        _CSV = project_data_dir(__file__) / "malls.csv"
    """
    return Path(layer_file).parent.parent / "data"
