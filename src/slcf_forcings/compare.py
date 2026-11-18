"""Compare two CEDS releases on a common footing."""

from __future__ import annotations
import pandas as pd
import xarray as xr
from pathlib import Path


def align_releases(left: pd.DataFrame, right: pd.DataFrame,
                   left_label: str, right_label: str) -> pd.DataFrame:
    """Join two annual-totals tables on (species, year, sector).

    Inner join on years: CEDS-2017 (CMIP6) ends 2014 while CEDS-CMIP-2025 runs
    to 2023, so the comparable window is set by the shorter release, not
    assumed.
    """
    keys = [k for k in ("species", "year", "sector") if k in left.columns and k in right.columns]
    merged = left.merge(right, on=keys, suffixes=(f"_{left_label}", f"_{right_label}"))
    l, r = f"tg_yr_{left_label}", f"tg_yr_{right_label}"
    merged["abs_diff"] = merged[r] - merged[l]
    merged["pct_diff"] = 100.0 * merged["abs_diff"] / merged[l].where(merged[l] != 0)
    return merged


def spatial_difference(left_file: Path, right_file: Path, year: int,
                       cell_area: xr.DataArray) -> xr.DataArray:
    """Annual-mean gridded difference (right - left) for one species, one year.

    Both releases must share a grid; regridding is deliberately not done here,
    so a mismatch raises rather than silently interpolating.
    """
    def _annual(path: Path) -> xr.DataArray:
        with xr.open_dataset(path, use_cftime=True, chunks={"time": 12}) as ds:
            var = next(n for n in ds.data_vars if "_em_" in n)
            da = ds[var].sel(time=str(year))
            if "sector" in da.dims:
                da = da.sum("sector")
            return da.mean("time").compute()

    a, b = _annual(left_file), _annual(right_file)
    if a.shape != b.shape:
        raise ValueError(f"Grid mismatch: {a.shape} vs {b.shape}; regrid explicitly.")
    return b - a