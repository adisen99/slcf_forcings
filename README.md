# CMIP7 SLCF forcings evaluation

This project evaluates the historical anthropogenic short-lived climate forcer
(SLCF) and CO2 emissions supplied for CMIP7, and uses the FaIR simple climate
model to quantify their global climate implications.

The near-term question is:

> How well do the CMIP7 CEDS historical emissions reproduce independent
> emissions evidence, and what do changes in individual SLCFs and sectors imply
> for historical effective radiative forcing and global-mean temperature?

This is an **emissions and global climate-response** study. It is not presently
a regional air-quality, atmospheric chemistry, or fully coupled Earth System
Model (ESM) project.

## Objectives

1. Build a reproducible reader and QA workflow for gridded CEDS emissions.
2. Produce annual global, sectoral, and regional emissions totals for CO2 and
   SLCF species.
3. Compare those totals and trends against independent inventories and
   observations.
4. Convert the evaluated global emissions to FaIR inputs and run historical
   forcing, concentration, and temperature ensembles.
5. Use counterfactual experiments to attribute the global response to aerosol
   pollution, individual species, and emitting sectors.
6. Report uncertainty from emissions choices and FaIR's calibrated parameter
   ensemble, clearly distinguishing observed constraints from model-derived
   attribution.

## Current project status at a glance

This project is structured as a staged scientific workflow:

1. Establish a checked historical baseline using the archived CEDS files.
2. Build a reproducible QA and emissions-aggregation pipeline.
3. Replace the baseline with the production CMIP7 CEDS release and compare the
   change against the archived reference.
4. Benchmark the resulting annual totals against independent inventories and
   observations.
5. Convert the evaluated emissions to FaIR inputs and run historical forcing,
   concentration, and temperature experiments.

At present, the project is in the baseline-validation stage. The archived old
release has been audited, the annual 1750–2023 archive is understood, and the
active 2000–2023 working subset has been saved in `output/preliminary/` for quick
re-use. The next major transition is to the production CEDS data and then to the
independent inventory comparison.

## Notebook-first repository workflow

The project is intentionally organised so that the main analysis lives in the
notebooks at the repository root, while reusable logic stays in helper modules
and scripts.

- `00_old_ceds_baseline_overview.ipynb` — conceptual overview and old-data
  baseline checks.
- `01_old_ceds_qa_pipeline.ipynb` — main QA, audit, aggregation, and old-archive
  comparison workflow.

The current active notebook workflow is intentionally limited to the two old-data
notebooks above. The FaIR notebook is kept as a future step and is not part of
this active analysis cycle.

A small CSV cache is also kept in `output/preliminary/` for repeated quick
analysis. This includes the annual totals, global species totals, and normalized
trend tables so the notebooks do not need to re-run the heavy gridded aggregation
workflow on every pass.

Reusable code should live in:

- `src/slcf_forcings/ceds.py` — emissions-file discovery, metadata audit, and
  area-weighted aggregation helpers.
- `scripts/download_ceds_gn.sh` — production dataset download wrapper.
- `scripts/` — supporting utilities only when they simplify notebook execution or
  make a repeated task explicit.

The notebooks should call these helper functions rather than embedding all the
logic inline. This keeps the science transparent and makes the analysis easy to
review step by step.

## Current repository contents

| Location | Contents | Status / intended use |
|---|---|---|
| `data/SLCF_main/` | Historical CEDS NetCDF files and grid-cell area | Primary starting input; the old archived release lives in `data/SLCF_main/old/` |
| `data/SLCF_supp/` | Directory for the CEDS supplemental stream | Planned download; not required for the first baseline analysis |
| `data/SLCF_testing/` | Directory for testing datasets | Empty; not required for the main study |
| `output/preliminary/` | Generated old-data annual totals | Validated baseline outputs for the archived March release |
| `src/slcf_forcings/ceds.py` | Shared QA and aggregation functions | Reusable helper code for the notebooks |
| `scripts/download_ceds_gn.sh` | Download wrapper for the production CEDS collections | Required utility for moving to the current CMIP7 release |
| `00_old_ceds_baseline_overview.ipynb` | Baseline review and overview | Active notebook |
| `01_old_ceds_qa_pipeline.ipynb` | NetCDF QA and annual summary workflow | Active notebook |
| `02_fair_historical_evaluation.ipynb` | Historical FaIR analysis | Deferred; not part of the current active workflow |

The gridded data are large (currently about 47 GB), so raw downloads should not
be committed to version control. Preserve the download script and record the
dataset source ID, version, checksum, access date, and any processing choices.

### Git tracking and local-only data policy

This repository deliberately excludes the raw NetCDF archives, the local working
`data/` tree, and generated analysis outputs from Git tracking. The project
keeps the data and derived files on disk locally for reproducible analysis while
keeping the repository lightweight and safe to push remotely.

This is enforced via the repository `.gitignore` file, which ignores the local
archive folders, downloaded NetCDF files, and the generated `output/` and
`plots/` products. The scripts and notebooks remain version-controlled so the
workflow is still fully reproducible, but the actual large input files are
treated as local working data rather than code artefacts.

### Downloading the production CEDS data

Use `scripts/download_ceds_gn.sh`, not the generated ESGF scripts directly.
The wrapper leaves those scripts unchanged, selects only the standard monthly
0.5-degree `gn` fields, resumes interrupted `.part` downloads, limits
concurrency, and verifies every SHA-256 checksum before accepting a file.

The current manifests contain 105 main and 200 supplemental `gn` files, with
no filename overlap. The much larger `gr` (0.1-degree) selection is deliberately
excluded: it is unnecessary for the current global, sectoral, and FaIR analysis
and should only be added for a future fine-scale spatial study.

```bash
# First inspect the exact 305 requested files; no network transfer occurs.
scripts/download_ceds_gn.sh --collection all --dry-run

# Then download the two collections. Three concurrent downloads is the default.
scripts/download_ceds_gn.sh --collection main
scripts/download_ceds_gn.sh --collection supplemental
```

The old March release is intentionally stored in `data/SLCF_main/old/` for
comparison while the new production files download into `data/SLCF_main/`.

## Data collections explained

| Collection | Purpose | Relevance here |
|---|---|---|
| **CMIP7 DECK historical forcing** | The common historical forcing suite used to run the core CMIP7 historical experiment; provides the observed-past baseline. | **Required now.** CEDS emissions are the central input for this project. |
| **CEDS supplemental data** | Companion data, such as solid-biofuel emissions, speciated NMVOCs, and historical CH4/N2O extensions. It is not an alternative scenario; its separate source ID helps avoid double counting. | **Recommended now** for a complete 1750–2023 input set; optional for a first 1970–2023 analysis. |
| **CMIP6Plus / testing data** | Pre-production inputs for testing forcing data and modelling workflows. | **Out of scope** for results intended to represent CMIP7 production data. |
| **CMIP7 ScenarioMIP** | Internally consistent future emissions, land-use, and forcing pathways from 2025, with long-term extensions. | **Later phase only.** Needed for prospective scenario work, not historical evaluation. |
| **CMIP model output** | Output from full ESM simulations driven by these forcings. | Optional future benchmark; not needed to establish the first FaIR-based evaluation. |

The current input4MIPs guidance identifies `CEDS-CMIP-2025-04-18` and its
supplemental companion as the production CMIP7 DECK source IDs. This repository
currently holds the older `CEDS-CMIP-2025-03-18` release. Before final analysis,
move to the current production release and document the change. The March
release has a documented CO, CO2, and NOx gridding issue in energy and industry
from 1961–2021; it is negligible in global totals but can matter in local or
regional comparisons. See the [input4MIPs CEDS dataset guidance](https://input4mips-cvs.readthedocs.io/en/latest/dataset-overviews/anthropogenic-slcf-co2-emissions/).

## Incremental data additions

Do not download everything at once. Add inputs only when their analysis stage
requires them.

| Stage | Dataset to add | Purpose | Required? |
|---|---|---|---|
| 1 | Latest production CEDS main (`2025-04-18`) | Replace the current historical baseline before final results | Yes |
| 1 | Matching CEDS supplemental stream | Complete historical emissions; especially pre-1970 CH4/N2O and supplemental sector/speciation fields | Recommended |
| 2 | EDGAR and Global Carbon Project CO2 data | Independent inventory checks for totals and trends | Yes for evaluation |
| 2 | GFED or another biomass-burning inventory | Sensitivity check for open biomass-burning contributions | Recommended |
| 3 | NOAA GML CO2, CH4, and N2O observations | Evaluate emissions-driven FaIR concentration pathways | Yes for FaIR evaluation |
| 3 | HadCRUT5, Berkeley Earth, or GISTEMP global temperature | Evaluate historical global temperature response | Yes for FaIR evaluation |
| 3 | Official CMIP7 solar and volcanic forcing | Complete the all-forcing historical FaIR experiment | Yes for final attribution |
| 4 | Satellite aerosol optical depth and/or assessed aerosol ERF | Additional constraint on aerosol forcing uncertainty | Useful, but optional |
| 5 | CMIP7 ScenarioMIP SLCF/CO2 and companion forcings | Future air-pollution/climate trade-off experiments | Long term |
| 5 | CMIP7 historical/ScenarioMIP ESM output | Compare FaIR attribution with full-model behaviour | Long term |

## Analysis design

The initial analysis window is **1970–2023**. It avoids the CH4/N2O historical
coverage gap in the current main-only collection, produces a useful result
quickly, and provides a clean basis for adding the supplemental 1750–2023
stream later.

### Directly evaluated quantities

- File integrity, units, time coverage, missing values, sector definitions, and
  area-weighted global totals.
- Emissions trends by species, sector, and broad region compared with
  independent inventories.
- FaIR simulated CO2, CH4, and N2O concentrations compared with observations.
- FaIR all-forcing global-mean temperature compared with an observational
  temperature series.

### FaIR counterfactuals

- Historical all-forcing reference run.
- Fixed aerosol-emissions experiment after a selected reference year.
- SO2-only, BC-only, OC-only, NOx/NMVOC/CO precursor experiments.
- Sector-removal experiments: energy, industry, surface transport, residential/
  commercial, shipping, agriculture, solvents, and waste.
- Ensemble sensitivity across calibrated FaIR parameters and plausible emissions
  alternatives.

FaIR is appropriate for global concentrations, effective radiative forcing, and
global-mean temperature. It must not be used to claim a resolved regional
climate or air-quality response from the gridded fields alone.

## Chronological TODO

### Phase 0 — establish a reproducible baseline

The reusable code is in `src/slcf_forcings/ceds.py`. It deliberately targets the
old collection or the new top-level collection through a configurable directory
argument, while excluding `data/SLCF_main/old/` from automatic file discovery.
The notebook workflow is the primary place to inspect, visualise, and interpret
results; helper functions are used transparently from there. Use the project’s
Mamba environment before analysis:

```bash
# Activate the repo environment.
source /Users/assengu/.miniforge3/etc/profile.d/conda.sh
mamba activate forcings_eval_cmip7

# If you need to recreate it from the repo spec:
mamba env create -f requirements.txt
mamba activate forcings_eval_cmip7

# Ensure the project source is importable from notebooks and scripts.
export PYTHONPATH="$PWD/src"
```

The current repo already includes the required scientific packages for the
historical CEDS analysis and the working environment is named
`forcings_eval_cmip7`.

The archived baseline currently contains the main historical anthropogenic species
for the working analysis: BC, CH4, CO, CO2, N2O, NH3, NMVOC, NOx, OC, and SO2.
In the present 2000–2023 working subset, the files available for the primary
annual global totals analysis are the eight anthropogenic main-species files that
are consistently present in the archive: BC, CO, CO2, NH3, NMVOC, NOx, OC, and
SO2. The active notebooks focus on the `data/SLCF_main/old/` archive and store
core intermediate outputs in `output/preliminary/` for reuse in quick analysis.

- [x] Use a notebook-first analysis workflow with helper functions in `src/` and
      `scripts/` for reusable logic.
- [x] Inventory the current old-data archive and confirm the active species set.
- [x] Verify the file layout, time range, and core dimensions for the archived
      files.
- [x] Save the key intermediate annual totals and normalized trend summaries to
      `output/preliminary/` for fast downstream analysis.
- [x] Confirm the active 2000–2023 working subset, and note the archive-specific
      species availability for the baseline workflow.
- [ ] Write a fuller data manifest with each input's source ID, version, DOI/URL,
      checksum, time range, and licence/citation.
- [ ] Correct the existing pipeline configuration and standardise paths,
      species names, sector labels, and unit conversions.

### Phase 1 — historical CEDS QA and aggregation

The quick-cache workflow in `output/preliminary/` is intended to hold the
baseline annual totals and normalized summaries that are repeatedly used in the
notebooks, rather than forcing a full gridded re-aggregation on every pass.

- [ ] Download the production `CEDS-CMIP-2025-04-18` main and matching
      supplemental data; retain the existing March data only for comparison.
- [ ] Implement safe area-weighted aggregation from kg m-2 s-1 to annual
      global Tg yr-1, using the supplied `areacella` rather than assuming a
      regular grid.
- [ ] Generate reproducible global, sectoral, and broad-regional annual tables.
- [ ] Add automated checks for missing months, negative/impossible values,
      discontinuities, duplicated fields, and accidental double counting of
      supplemental emissions.
- [ ] Produce a version-difference diagnostic between the March and April CEDS
      releases, focusing on CO, CO2, and NOx from 1961–2021.

### Phase 2 — independent emissions evaluation

- [ ] Acquire and harmonise EDGAR, Global Carbon Project CO2, and a
      biomass-burning inventory.
- [ ] Compare global totals, growth rates, sector shares, and regional patterns;
      report agreement and disagreement instead of choosing a reference by
      default.
- [ ] Select the final annual emissions series and document any splice,
      regridding, or unit-conversion decisions.

### Phase 3 — FaIR historical evaluation

- [ ] Convert evaluated annual emissions to the exact FaIR species inputs.
- [ ] Add official solar and volcanic forcing and prescribed inputs required by
      the selected FaIR configuration.
- [ ] Run an ensemble of historical all-forcing simulations.
- [ ] Compare simulated concentrations with NOAA observations and temperature
      with a selected global observational series.
- [ ] Diagnose bias without silently tuning parameters to match the observations.

### Phase 4 — attribution and reporting

- [ ] Run species and sector counterfactual ensembles.
- [ ] Quantify changes in effective radiative forcing and global-mean
      temperature with uncertainty intervals.
- [ ] Produce publication-quality figures, a methods note, and a fully
      reproducible results table.
- [ ] Add automated tests for aggregation, units, and scenario construction.

### Phase 5 — explicitly longer-term work

- [ ] Extend the historical workflow back to 1750 using the supplemental data.
- [ ] Add CMIP7 ScenarioMIP pathways for future air-pollution and mitigation
      trade-off analysis.
- [ ] Compare FaIR results against CMIP7 ESM historical and ScenarioMIP output
      as it becomes available.
- [ ] Add aerosol optical-depth / ERF observational constraints.
- [ ] If regional impacts become a goal, couple the emissions evaluation to
      chemistry-transport or ESM output; this is a separate project scope.

## Suggested team split

| Role | Primary responsibility | Near-term deliverable |
|---|---|---|
| Data and QA | NetCDF ingestion, metadata, aggregation, manifests, tests | Validated annual sector/species/region table |
| External evaluation | Inventory and observational-data acquisition, harmonisation, comparison | Emissions and observational benchmark report |
| FaIR modelling | FaIR input builder, ensemble runs, counterfactuals | Reproducible historical and attribution experiments |
| Integration and communication | Notebook structure, figure production, uncertainty synthesis, documentation | Reproducible release and methods/results narrative |

## Scope boundaries

For now, the project will not attempt to produce regional
air-quality estimates, infer causal regional temperature effects from emissions
maps, or download every CMIP7 forcing/scenario collection. Those are sensible
follow-on directions only after the historical emissions-to-FaIR workflow is
validated.

## Key references

- [input4MIPs: anthropogenic SLCF and CO2 emissions](https://input4mips-cvs.readthedocs.io/en/latest/dataset-overviews/anthropogenic-slcf-co2-emissions/)
- [CMIP7 forcing datasets](https://wcrp-cmip.org/cmip-phases/cmip7/cmip7-forcing-datasets/)
- [ScenarioMIP-CMIP7 protocol](https://gmd.copernicus.org/articles/19/2627/2026/)
- [FaIR documentation](https://docs.fairmodel.net/)
