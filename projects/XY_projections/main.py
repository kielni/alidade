from pathlib import Path

import geopandas as gpd


def main():
    project_dir = Path(__file__).parent
    libraries = gpd.read_file(project_dir / "project_data" / "Libraries.shp")
    buffer = gpd.read_file(project_dir / "data" / "high_schools_buffer.shp")

    joined = gpd.sjoin(
        buffer[["School", "geometry"]],
        libraries[["Name", "geometry"]],
        how="left",
        predicate="contains",
    )
    counts = joined.groupby("School")["Name"].count()

    for school, count in counts.items():
        libs = "library" if count == 1 else "libraries"
        print(f"{school}: {count} {libs}")


if __name__ == "__main__":
    main()
