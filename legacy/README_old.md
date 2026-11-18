# Legacy workflow (retired 2026-11-18)

Local-ESGF-download workflow, superseded by the qv56 replica on Gadi
(`/g/data/qv56/replicas/input4MIPs`), which carries every CEDS release this
project needs — including `CEDS-CMIP-2025-04-18 / v20250421 / gn`, 105 files,
51.5 GB.

Retained for provenance only. Not maintained; paths and assumptions are stale.

- `scripts/download_ceds_gn.sh` — ESGF wget-manifest wrapper with SHA-256
  verification and resumable `.part` downloads.
- `scripts/run_preliminary_old_analysis.py`, `scripts/plot_preliminary_trends.py`
  — superseded by `notebooks/02_release_timeseries.ipynb`.
- `notebooks/` — the two old-archive QA notebooks and the FaIR stub. Both
  notebooks selected files by matching the literal `200001-202312` chunk
  string, which silently excluded CH4 and N2O from the March release; see
  `select_files()` in `src/slcf_forcings/ceds.py` for the fix.