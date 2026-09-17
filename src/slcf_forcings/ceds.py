"""Small, explicit building blocks for the CEDS Phase 0 workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd
import xarray as xr

try:
    from tqdm.auto import tqdm
except ImportError:  # pragma: no cover - tqdm is optional for lightweight usage.
    def tqdm(iterable, **kwargs):
        return iterable


def _emissions_variable(dataset: xr.Dataset, path: Path) -> str:
    """Return the one physical emissions variable, excluding CF bounds fields."""
    candidates = [name for name in dataset.data_vars if "_em_" in name]
    if len(candidates) != 1:
        raise ValueError(
            f"Expected one emissions variable in {path.name}; found {candidates} "
            f"among {list(dataset.data_vars)}"
        )
    return candidates[0]


def discover_emissions_files(data_dir: str | Path) -> list[Path]:
    """Return top-level gridded CEDS emission files, excluding area and old data."""
    directory = Path(data_dir)
    return sorted(
        path for path in directory.glob("*-em-*_input4MIPs_*.nc")
        if "areacella" not in path.name
    )


def audit_collection(data_dir: str | Path) -> pd.DataFrame:
    """Read metadata only and return one audit row per NetCDF file."""
    rows: list[dict[str, object]] = []
    for path in discover_emissions_files(data_dir):
        try:
            with xr.open_dataset(path, decode_times=False) as dataset:
                variable = _emissions_variable(dataset, path)
                field = dataset[variable]
                rows.append({
                    "file": path.name,
                    "readable": True,
                    "error": None,
                    "variable": variable,
                    "units": field.attrs.get("units"),
                    "dimensions": ",".join(field.dims),
                    "time_size": dataset.sizes.get("time", 0),
                    "has_sector": "sector" in field.dims,
                    "has_lat_lon": {"lat", "lon"}.issubset(field.dims),
                    "mip_era": dataset.attrs.get("mip_era"),
                    "source_id": dataset.attrs.get("source_id"),
                })
        except OSError as error:
            rows.append({
                "file": path.name,
                "readable": False,
                "error": str(error),
            })
    return pd.DataFrame(rows)


def load_cell_area(data_dir: str | Path) -> xr.DataArray:
    """Load the supplied cell area, rather than estimating it from latitude."""
    candidates = sorted(Path(data_dir).glob("areacella*_input4MIPs_*.nc"))
    if len(candidates) != 1:
        raise FileNotFoundError(f"Expected exactly one areacella file in {data_dir}; found {len(candidates)}")
    with xr.open_dataset(candidates[0]) as dataset:
        variable = next(name for name in dataset.data_vars if name == "areacella")
        return dataset[variable].load()


def _seconds_per_timestep(time: xr.DataArray) -> xr.DataArray:
    """Return CF-calendar-aware seconds per monthly timestep."""
    if not hasattr(time.dt, "days_in_month"):
        raise ValueError("A decodable monthly time coordinate is required.")
    return time.dt.days_in_month.astype("float64") * 86_400.0


def annual_global_totals(
    file_paths: Iterable[str | Path], cell_area: xr.DataArray
) -> pd.DataFrame:
    """Integrate kg m-2 s-1 emissions to annual Tg yr-1 by sector.

    The calculation preserves the sector dimension when available and uses
    actual month lengths rather than a fixed 365-day multiplier.
    """
    results: list[pd.DataFrame] = []
    file_list = list(map(Path, file_paths))
    for path in tqdm(file_list, desc="Aggregating CEDS files", unit="file"):
        with xr.open_dataset(path, use_cftime=True) as dataset:
            variable = _emissions_variable(dataset, path)
            emissions = dataset[variable]
            units = emissions.attrs.get("units", "").replace(" ", "")
            if units not in {"kgm-2s-1", "kgm**-2s**-1"}:
                raise ValueError(f"Unsupported units for {path.name}: {emissions.attrs.get('units')}")
            seconds = _seconds_per_timestep(emissions.time)
            mass_kg = (emissions * cell_area * seconds).sum(("lat", "lon"), skipna=False)
            annual_tg = (mass_kg / 1e9).resample(time="YS").sum()
            table = annual_tg.to_dataframe(name="tg_per_year").reset_index()
            table["species_variable"] = variable
            table["source_file"] = path.name
            # cftime objects retain a native ``year`` attribute but pandas does
            # not always expose a .dt accessor for them.
            table["year"] = [date.year for date in table["time"]]
            results.append(table.drop(columns="time"))
    return pd.concat(results, ignore_index=True) if results else pd.DataFrame()
