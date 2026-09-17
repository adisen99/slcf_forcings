#!/usr/bin/env python
"""Generate initial 2000–2023 global and sectoral totals from old CEDS data."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from slcf_forcings.ceds import (  # noqa: E402
    annual_global_totals,
    discover_emissions_files,
    load_cell_area,
)


def main() -> None:
    source = PROJECT_ROOT / "data" / "SLCF_main" / "old"
    output = PROJECT_ROOT / "output" / "preliminary"
    output.mkdir(parents=True, exist_ok=True)

    wanted = {"CO2", "SO2", "BC", "OC"}
    files = [
        path
        for path in discover_emissions_files(source)
        if "-em-anthro_" in path.name
        and "200001-202312" in path.name
        and path.name.split("-em-", maxsplit=1)[0] in wanted
    ]
    if len(files) != len(wanted):
        raise RuntimeError(f"Expected {len(wanted)} key-species files; found {len(files)}")

    totals = annual_global_totals(files, load_cell_area(source))
    totals.to_csv(output / "ceds_old_2000_2023_key_species_by_sector.csv", index=False)

    global_totals = totals.groupby(["year", "species_variable"], as_index=False)["tg_per_year"].sum()
    global_totals.to_csv(output / "ceds_old_2000_2023_key_species_global.csv", index=False)

    print("Wrote preliminary annual totals:")
    print(output / "ceds_old_2000_2023_key_species_by_sector.csv")
    print(output / "ceds_old_2000_2023_key_species_global.csv")
    print("\n2023 global totals (Tg/yr):")
    print(
        global_totals.loc[global_totals.year == 2023]
        .sort_values("species_variable")
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
