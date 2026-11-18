"""Reusable building blocks for the CMIP7 CEDS emissions workflow.

Design notes
------------
**Selection is by parsed time coverage, never by chunk-string matching.** CEDS
chunk boundaries move between releases: CEDS-CMIP-2025-03-18 splits CH4/N2O at
197001-201912 / 202001-202312, while CEDS-CMIP-2025-04-18 splits them at
197001-199912 / 200001-202312. Matching the literal ``200001-202312`` string
therefore returns ten species for April and eight for March, silently
corrupting any release comparison.

**Discovery is recursive over the input4MIPs DRS.** On the Gadi qv56 replica a
source id expands to ``<source_id>/atmos/mon/<variable_id>/<grid_label>/<version>/``,
so each species sits in its own leaf directory. A source id may carry more than
one grid (``gn`` at 0.5 degrees, ``gr`` at 0.1) and more than one version
(CEDS-CMIP-2025-03-18 has v20250325 and v20250327). Globbing across either
mixes incompatible data, so both are filterable and
:func:`assert_single_realisation` enforces the result.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
import xarray as xr

try:
    from tqdm.auto import tqdm
except ImportError:  # pragma: no cover - tqdm is optional.
    def tqdm(iterable, **kwargs):
        return iterable


CHUNK_RE = re.compile(r"_(\d{6})-(\d{6})\.nc$")
VERSION_RE = re.compile(r"^v\d{8}$")
GRID_LABELS = {"gn", "gr", "gr1", "gm"}

MAIN_SPECIES = ["BC", "CH4", "CO", "CO2", "N2O", "NH3", "NMVOC", "NOx", "OC", "SO2"]


# --------------------------------------------------------------------------
# Filename parsing
# --------------------------------------------------------------------------

def species_of(path: str | Path) -> str:
    """Return the species prefix, e.g. 'CH4' from 'CH4-em-anthro_...nc'."""
    return Path(path).name.split("-em-", maxsplit=1)[0]


def is_aircraft(path: str | Path) -> bool:
    """True for the AIR (aviation) stream, which carries a vertical dimension."""
    return "-em-AIR-anthro_" in Path(path).name


def parse_time_range(path: str | Path) -> tuple[int, int]:
    """Return (first_year, last_year) from the filename's YYYYMM-YYYYMM chunk."""
    match = CHUNK_RE.search(Path(path).name)
    if match is None:
        raise ValueError(f"No YYYYMM-YYYYMM time chunk in {Path(path).name}")
    return int(match.group(1)[:4]), int(match.group(2)[:4])


def source_id_of(path: str | Path) -> str | None:
    """Return the CEDS source id from the filename, across release generations.

    Matches both the CMIP6 form (``CEDS-2017-05-18``) and the CMIP7 form
    (``CEDS-CMIP-2025-04-18``).
    """
    match = re.search(r"(CEDS(?:-CMIP)?-\d{4}-\d{2}-\d{2})", Path(path).name)
    return match.group(1) if match else None


def drs_fields(path: str | Path) -> dict[str, str | None]:
    """Extract grid_label and version from a file's DRS path components."""
    parts = Path(path).parts
    grid = next((p for p in parts if p in GRID_LABELS), None)
    version = next((p for p in reversed(parts) if VERSION_RE.match(p)), None)
    return {"grid_label": grid, "version": version}


# --------------------------------------------------------------------------
# Discovery and selection
# --------------------------------------------------------------------------

def discover_emissions_files(
    data_dir: str | Path,
    recursive: bool = True,
    grid_label: str | None = None,
    version: str | None = None,
) -> list[Path]:
    """Return gridded CEDS emission files under ``data_dir``.

    ``recursive=True`` walks the input4MIPs DRS, where each variable lives in
    its own leaf directory; this is the layout on the qv56 replica. Use
    ``recursive=False`` for a flat directory of files, as a manual ESGF
    download produces.

    ``grid_label`` and ``version`` filter on DRS path components. Pass them
    whenever a source id carries more than one of either.
    """
    root = Path(data_dir)
    pattern = "**/*-em-*_input4MIPs_*.nc" if recursive else "*-em-*_input4MIPs_*.nc"
    files = [p for p in root.glob(pattern) if "areacella" not in p.name]

    if grid_label is not None:
        files = [p for p in files if grid_label in p.parts]
    if version is not None:
        files = [p for p in files if version in p.parts]

    return sorted(files)


def assert_single_realisation(files: Sequence[Path]) -> tuple[str, str]:
    """Raise unless every file shares one grid_label and one version.

    Mixing 0.5-degree (gn) with 0.1-degree (gr) data, or two versions of one
    source id, yields totals that are wrong in a way no downstream check would
    catch. Returns the (grid_label, version) actually found.
    """
    grids, versions = set(), set()
    for path in files:
        fields = drs_fields(path)
        if fields["grid_label"]:
            grids.add(fields["grid_label"])
        if fields["version"]:
            versions.add(fields["version"])

    if len(grids) > 1:
        raise ValueError(
            f"Mixed grid labels: {sorted(grids)}. Pass grid_label= to select one."
        )
    if len(versions) > 1:
        raise ValueError(
            f"Mixed versions: {sorted(versions)}. Pass version= to select one."
        )
    return (
        grids.pop() if grids else "unknown",
        versions.pop() if versions else "unknown",
    )


def select_files(
    data_dir: str | Path,
    species: Sequence[str] = MAIN_SPECIES,
    year_range: tuple[int, int] = (1750, 2023),
    include_aircraft: bool = False,
    require_all: bool = True,
    recursive: bool = True,
    grid_label: str | None = "gn",
    version: str | None = None,
) -> list[Path]:
    """Select files for ``species`` whose time chunk overlaps ``year_range``.

    ``require_all=True`` raises when a requested species has no file covering
    the window; this is what prevents a silently short species set. Set False
    to probe coverage without raising.
    """
    first, last = year_range
    wanted = set(species)

    candidates = discover_emissions_files(
        data_dir, recursive=recursive, grid_label=grid_label, version=version
    )
    selected = [
        path for path in candidates
        if is_aircraft(path) == include_aircraft
        and species_of(path) in wanted
        and (lambda r: r[0] <= last and r[1] >= first)(parse_time_range(path))
    ]

    if require_all:
        missing = wanted - {species_of(p) for p in selected}
        if missing:
            raise ValueError(
                f"No files covering {first}-{last} for: {sorted(missing)} "
                f"in {data_dir}"
            )
    if selected:
        assert_single_realisation(selected)
    return sorted(selected)


# --------------------------------------------------------------------------
# Sector metadata
# --------------------------------------------------------------------------

def sector_labels(path: str | Path) -> dict[int, str]:
    """Return the sector index -> name mapping from the file's own metadata.

    CEDS stores sectors as a bare integer coordinate with names in an
    attribute whose key varies by release. Sector count and ordering are NOT
    stable across releases, so an index-to-index comparison between
    CEDS-2017 and CEDS-CMIP-2025 would produce plausible, wrong numbers.
    Always map through names before comparing sectors between releases.

    Returns an empty dict when no sector coordinate or label attribute exists;
    the caller should treat that as "cannot compare sectorally".
    """
    with xr.open_dataset(path, decode_times=False) as dataset:
        if "sector" not in dataset.coords:
            return {}
        attrs = dataset["sector"].attrs
        raw = (
            attrs.get("ids")
            or attrs.get("sector_names")
            or attrs.get("long_name")
            or attrs.get("labels")
        )
        if not raw:
            return {}

        parts = [p.strip() for p in re.split(r"[;\n]", str(raw)) if p.strip()]
        mapping: dict[int, str] = {}
        for part in parts:
            match = re.match(r"(\d+)\s*[:=]\s*(.+)", part)
            if match:
                mapping[int(match.group(1))] = match.group(2).strip()
        return mapping or dict(enumerate(parts))


def compare_sector_definitions(
    left: str | Path, right: str | Path
) -> pd.DataFrame:
    """Compare two releases' sector definitions index by index.

    Run this before any sectoral comparison. Rows where ``same`` is False mean
    the index refers to a different sector in the two releases.
    """
    a, b = sector_labels(left), sector_labels(right)
    indices = sorted(set(a) | set(b))
    return pd.DataFrame({
        "index": indices,
        "left": [a.get(i) for i in indices],
        "right": [b.get(i) for i in indices],
        "same": [a.get(i) == b.get(i) for i in indices],
    })


# --------------------------------------------------------------------------
# Integrity auditing
# --------------------------------------------------------------------------

def audit_collection(
    data_dir: str | Path,
    recursive: bool = True,
    grid_label: str | None = None,
    version: str | None = None,
) -> pd.DataFrame:
    """Read metadata only and return one audit row per NetCDF file."""
    rows: list[dict[str, object]] = []
    files = discover_emissions_files(
        data_dir, recursive=recursive, grid_label=grid_label, version=version
    )

    for path in files:
        fields = drs_fields(path)
        row: dict[str, object] = {
            "file": path.name,
            "path": str(path),
            "species": species_of(path),
            "stream": "AIR" if is_aircraft(path) else "surface",
            "grid_label_path": fields["grid_label"],
            "version_path": fields["version"],
            "size_bytes": path.stat().st_size,
            "source_id_filename": source_id_of(path),
            "chunk_first_year": None,
            "chunk_last_year": None,
        }
        try:
            row["chunk_first_year"], row["chunk_last_year"] = parse_time_range(path)
        except ValueError:
            pass

        try:
            with xr.open_dataset(path, decode_times=False) as dataset:
                candidates = [n for n in dataset.data_vars if "_em_" in n]
                if len(candidates) != 1:
                    raise ValueError(
                        f"Expected one emissions variable; found {candidates}"
                    )
                field = dataset[candidates[0]]
                row.update({
                    "readable": True,
                    "error": None,
                    "variable": candidates[0],
                    "units": field.attrs.get("units"),
                    "dimensions": ",".join(field.dims),
                    "time_size": dataset.sizes.get("time", 0),
                    "n_sectors": dataset.sizes.get("sector", 0),
                    "has_lat_lon": {"lat", "lon"}.issubset(field.dims),
                    "mip_era": dataset.attrs.get("mip_era"),
                    "source_id": dataset.attrs.get("source_id"),
                    "grid_label": dataset.attrs.get("grid_label"),
                    "tracking_id": dataset.attrs.get("tracking_id"),
                    "further_info_url": dataset.attrs.get("further_info_url"),
                })
        except (OSError, ValueError) as error:
            row.update({"readable": False, "error": str(error)})
        rows.append(row)

    return pd.DataFrame(rows)


def assert_all_readable(audit: pd.DataFrame, context: str = "") -> None:
    """Raise if any audited file failed to open. Call this; don't eyeball the table."""
    if audit.empty:
        raise RuntimeError(f"Audit table is empty: no files discovered. {context}")
    bad = audit[~audit["readable"].fillna(False).astype(bool)]
    if not bad.empty:
        detail = bad[["file", "size_bytes", "error"]].to_string(index=False)
        raise RuntimeError(f"{len(bad)} unreadable file(s): {context}\n{detail}")


def flag_truncated(audit: pd.DataFrame, tolerance: float = 0.25) -> pd.DataFrame:
    """Return files far smaller than their peers of the same stream and time chunk.

    Catches interrupted downloads that still open cleanly. Irrelevant on a
    curated replica, but kept for any locally fetched data.
    """
    ok = audit[audit["readable"].fillna(False).astype(bool)].copy()
    if ok.empty:
        return ok
    median = ok.groupby(["stream", "chunk_first_year", "chunk_last_year"])[
        "size_bytes"
    ].transform("median")
    return ok[ok["size_bytes"] < tolerance * median]


def check_source_consistency(audit: pd.DataFrame) -> pd.DataFrame:
    """Return rows whose global source_id attribute disagrees with the filename."""
    ok = audit[audit["readable"].fillna(False).astype(bool)]
    return ok[ok["source_id"] != ok["source_id_filename"]]


def check_time_coverage(audit: pd.DataFrame) -> pd.DataFrame:
    """Return rows whose month count disagrees with the filename's chunk span."""
    ok = audit[audit["readable"].fillna(False).astype(bool)].copy()
    expected = (ok["chunk_last_year"] - ok["chunk_first_year"] + 1) * 12
    return ok[ok["time_size"] != expected].assign(expected_months=expected)


def check_single_realisation(audit: pd.DataFrame) -> pd.DataFrame:
    """Summarise grid labels and versions present, so mixing is visible."""
    return (
        audit.groupby(["source_id_filename", "grid_label_path", "version_path"],
                      dropna=False)
        .agg(n_files=("file", "count"), gb=("size_bytes", lambda s: s.sum() / 1e9))
        .round(2)
        .reset_index()
    )


# --------------------------------------------------------------------------
# Provenance manifest
# --------------------------------------------------------------------------

def sha256_of(path: str | Path, block_size: int = 1 << 20) -> str:
    """Streamed SHA-256 so multi-GB files are not read into memory."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(block_size), b""):
            digest.update(block)
    return digest.hexdigest()


def write_manifest(
    data_dir: str | Path,
    out_path: str | Path,
    recursive: bool = True,
    grid_label: str | None = None,
    version: str | None = None,
    compute_checksums: bool = True,
    download_manifest: str | Path | None = None,
) -> pd.DataFrame:
    """Record source id, version, grid, coverage, licence and checksum per input.

    On the qv56 replica there is no ESGF download manifest to borrow checksums
    from, so ``compute_checksums=True`` is the default; hashing ~50 GB takes a
    couple of minutes. Pass ``download_manifest`` to reuse verified checksums
    instead, which is both faster and a stronger claim: it attests the bytes
    matched ESGF at download time.

    Unreadable files are recorded with ``readable=False`` rather than raising,
    so an incomplete collection is documented rather than undocumented.
    """
    audit = audit_collection(
        data_dir, recursive=recursive, grid_label=grid_label, version=version
    )
    if audit.empty:
        raise RuntimeError(f"No emissions files discovered in {data_dir}")

    expected: dict[str, str] = {}
    urls: dict[str, str] = {}
    if download_manifest is not None and Path(download_manifest).exists():
        tsv = pd.read_csv(
            download_manifest, sep="\t", header=None,
            names=["file", "url", "sha256"],
        )
        expected = dict(zip(tsv["file"], tsv["sha256"]))
        urls = dict(zip(tsv["file"], tsv["url"]))

    records = []
    for row in tqdm(audit.itertuples(), total=len(audit), desc="Manifest", unit="file"):
        path = Path(row.path)
        readable = bool(getattr(row, "readable", False))

        attrs: dict = {}
        if readable:
            with xr.open_dataset(path, decode_times=False) as dataset:
                attrs = dict(dataset.attrs)

        if compute_checksums and readable:
            checksum, checksum_source = sha256_of(path), "disk"
        else:
            checksum, checksum_source = expected.get(row.file), "esgf_manifest"

        records.append({
            "file": row.file,
            "path": row.path,
            "species": row.species,
            "stream": row.stream,
            "readable": readable,
            "error": getattr(row, "error", None),
            "source_id": attrs.get("source_id") or row.source_id_filename,
            "mip_era": attrs.get("mip_era"),
            "institution_id": attrs.get("institution_id"),
            "grid_label": attrs.get("grid_label") or row.grid_label_path,
            "version": row.version_path,
            "frequency": attrs.get("frequency"),
            "variable": getattr(row, "variable", None),
            "units": getattr(row, "units", None),
            "first_year": row.chunk_first_year,
            "last_year": row.chunk_last_year,
            "n_months": getattr(row, "time_size", None),
            "n_sectors": getattr(row, "n_sectors", None),
            "size_bytes": row.size_bytes,
            "sha256": checksum,
            "sha256_source": checksum_source,
            "tracking_id": attrs.get("tracking_id"),
            "further_info_url": attrs.get("further_info_url"),
            "license": attrs.get("license"),
            "source_url": urls.get(row.file),
        })

    manifest = pd.DataFrame(records)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(out_path, index=False)
    return manifest


# --------------------------------------------------------------------------
# Area-weighted aggregation
# --------------------------------------------------------------------------

def load_cell_area(
    data_dir: str | Path,
    grid_label: str = "gn",
    version: str | None = None,
) -> xr.DataArray:
    """Load the supplied cell area rather than estimating it from latitude.

    On the DRS the area file sits in its own ``atmos/fx/areacella/<grid>/<version>/``
    leaf, so the search is recursive.
    """
    root = Path(data_dir)
    candidates = [
        p for p in root.glob("**/areacella*_input4MIPs_*.nc")
        if grid_label in p.parts or f"_{grid_label}." in p.name
    ]
    if version is not None:
        candidates = [p for p in candidates if version in p.parts]

    if len(candidates) != 1:
        raise FileNotFoundError(
            f"Expected exactly one {grid_label} areacella under {root}; found "
            f"{len(candidates)}: {[str(p) for p in candidates]}"
        )
    with xr.open_dataset(candidates[0]) as dataset:
        return dataset["areacella"].load()


def _aligned_cell_area(
    emissions: xr.DataArray, cell_area: xr.DataArray, path: Path
) -> xr.DataArray:
    """Verify the area grid matches the emissions grid, then share its coordinates.

    xarray aligns on coordinates with an inner join, so a sub-degree mismatch
    between areacella and the emissions grid would silently shrink or empty the
    product rather than raising.
    """
    for dim in ("lat", "lon"):
        if dim not in cell_area.dims:
            raise ValueError(f"areacella has no '{dim}' dimension")
        if emissions.sizes[dim] != cell_area.sizes[dim]:
            raise ValueError(
                f"{path.name}: {dim} size {emissions.sizes[dim]} != areacella "
                f"{cell_area.sizes[dim]}"
            )
        diff = np.abs(
            np.asarray(emissions[dim].values, dtype="float64")
            - np.asarray(cell_area[dim].values, dtype="float64")
        )
        if not np.all(diff < 1e-6):
            raise ValueError(
                f"{path.name}: {dim} coordinates differ from areacella "
                f"(max |diff| = {diff.max():.3e})"
            )
    return cell_area.assign_coords(lat=emissions["lat"], lon=emissions["lon"])


def _seconds_per_timestep(time: xr.DataArray) -> xr.DataArray:
    """Return CF-calendar-aware seconds per monthly timestep."""
    if not hasattr(time.dt, "days_in_month"):
        raise ValueError("A decodable monthly time coordinate is required.")
    return time.dt.days_in_month.astype("float64") * 86_400.0


def annual_global_totals(
    file_paths: Iterable[str | Path],
    cell_area: xr.DataArray,
    year_range: tuple[int, int] | None = None,
    chunks: dict | None = None,
) -> pd.DataFrame:
    """Integrate kg m-2 s-1 emissions to annual Tg yr-1, preserving sector.

    Uses actual month lengths rather than a fixed 365-day multiplier.
    ``year_range`` slices time before any arithmetic, so a file whose chunk
    merely overlaps the window contributes only the requested years.

    ``chunks`` must be a dict: ``"auto"`` cannot chunk the object-dtype cftime
    coordinate that ``use_cftime=True`` produces. Defaults to one year per
    chunk, which aligns with the annual resample so no cross-chunk shuffle is
    needed. Pass ``{}`` to load eagerly.
    """
    results: list[pd.DataFrame] = []
    file_list = list(map(Path, file_paths))
    if file_list:
        assert_single_realisation(file_list)

    for path in tqdm(file_list, desc="Aggregating", unit="file"):
        with xr.open_dataset(
            path, use_cftime=True, chunks=chunks if chunks is not None else {"time": 12}
        ) as dataset:
            candidates = [n for n in dataset.data_vars if "_em_" in n]
            if len(candidates) != 1:
                raise ValueError(
                    f"Expected one emissions variable in {path.name}; found {candidates}"
                )
            variable = candidates[0]
            emissions = dataset[variable]

            units = (emissions.attrs.get("units") or "").replace(" ", "")
            if units not in {"kgm-2s-1", "kgm**-2s**-1"}:
                raise ValueError(
                    f"Unsupported units for {path.name}: {emissions.attrs.get('units')}"
                )

            if year_range is not None:
                emissions = emissions.sel(
                    time=slice(str(year_range[0]), str(year_range[1]))
                )
                if emissions.sizes.get("time", 0) == 0:
                    continue

            area = _aligned_cell_area(emissions, cell_area, path)
            seconds = _seconds_per_timestep(emissions["time"])
            mass_kg = (emissions * area * seconds).sum(("lat", "lon"), skipna=False)

            unexpected = set(mass_kg.dims) - {"time", "sector"}
            if unexpected:
                raise ValueError(
                    f"{path.name}: dimensions {sorted(unexpected)} remain after the "
                    "spatial sum; aircraft files carry a vertical level axis and must "
                    "be aggregated separately"
                )

            annual_tg = (mass_kg / 1e9).resample(time="YS").sum().compute()

            if bool(annual_tg.isnull().any()):
                raise ValueError(
                    f"{path.name}: NaN in annual totals. With skipna=False any fill "
                    "value or missing month propagates; inspect before use."
                )

            fields = drs_fields(path)
            table = annual_tg.to_dataframe(name="tg_per_year").reset_index()
            table["species"] = species_of(path)
            table["species_variable"] = variable
            table["source_id"] = source_id_of(path)
            table["grid_label"] = fields["grid_label"]
            table["version"] = fields["version"]
            table["source_file"] = path.name
            # cftime objects expose .year but pandas does not reliably give a
            # .dt accessor for an object-dtype column of them.
            table["year"] = [date.year for date in table["time"]]
            results.append(table.drop(columns="time"))

    return pd.concat(results, ignore_index=True) if results else pd.DataFrame()