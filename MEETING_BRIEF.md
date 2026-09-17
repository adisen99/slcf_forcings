# CMIP7 SLCF evaluation: meeting brief

## 1. Overall plan

This project is a historical emissions-and-response evaluation built around the CMIP7 CEDS dataset.

The working plan is:

1. Start from the archived old CEDS release and build a reproducible baseline.
2. QA the archive and compute annual global totals and trend summaries.
3. Move to the production CMIP7 CEDS release and compare with the archived baseline.
4. Compare the resulting emissions against independent inventories and observations.
5. Convert the agreed emissions series into FaIR inputs and evaluate historical forcing, concentration, and temperature response.
6. Use counterfactual experiments to attribute the climate response to key species and sectors.

The scope is intentionally focused on a global, emissions-to-climate evaluation rather than a regional chemistry or ESM project.

## 2. Where we are now

We are currently in the Phase 0 baseline-validation stage.

Key status points:

- The archived CEDS files in `data/SLCF_main/old/` are the working reference dataset.
- The repo is already set up as a notebook-first analysis workflow with reusable logic in `src/slcf_forcings/ceds.py`.
- The archive has been checked for file readability, dimensions, and aggregate behaviour.
- A working 2000–2023 subset has been established for the main annual-global comparisons.
- The derived outputs used repeatedly in downstream analysis are stored in `output/preliminary/`.
- The next step is to replace the archived reference with the production CMIP7 CEDS release and compare the differences.

Project current working emphasis:
- `00_old_ceds_baseline_overview.ipynb` — archive overview and broad historical context.
- `01_old_ceds_qa_pipeline.ipynb` — QA, audit, and aggregation checks.
- `src/slcf_forcings/ceds.py` — shared helper functions.

## 3. Next steps

### Near-term milestones

1. Production release check
   - Download and validate the newer CMIP7 CEDS collection.
   - Compare it with the archived baseline.
   - Document deltas in species totals, timing, and sector structure.

2. Standardised emissions pipeline
   - Finalise path handling, species naming, sector labels, unit conversion, and missing-value handling.
   - Create a clean, reproducible pipeline for annual totals and trend diagnostics.

3. Independent comparison stage
   - Add EDGAR and Global Carbon Project CO2 comparisons.
   - Add a biomass-burning or other supplemental check where relevant.
   - Identify which independent datasets are strongest for each species.

4. FaIR implementation
   - Convert the final emissions series to FaIR species inputs.
   - Add historical forcing configuration and observational comparisons.
   - Run initial ensemble simulations and document the response.

## 4. How we can collaborate and divide tasks

A good working structure is to split responsibilities by analysis layer while keeping the notebooks as the shared record of the scientific decisions.

### Suggested workstreams

#### A. Emissions QA and baseline comparison
- Archive check, inventory validation, and file-level QA.
- Production-release comparison against the old baseline.
- Unit and sector consistency checks.
- Output tables for annual global totals and trend summaries.

#### B. Independent inventory benchmarking
- Gather and harmonise EDGAR, GCP, and other external datasets.
- Compare trends, ratios, and sector structure.
- Summarise agreement and disagreement in a consistent, reviewable table.

#### C. FaIR forcing and climate response
- Convert annual emissions to FaIR inputs.
- Select and prepare observed concentration and temperature datasets.
- Run historical ensembles and compare to observational records.
- Diagnose response in terms of all-forcing, aerosol, and sector attribution.

#### D. Documentation and reproducibility
- Maintain README and meeting notes.
- Ensure notebooks remain transparent and easy to rerun.
- Keep derived intermediate outputs organised and documented.

### Collaboration model

- Use the notebooks as the main science ledger: figures, checks, and interpretation live there.
- Put reusable processing in `src/slcf_forcings/ceds.py` or scripts.
- Keep the outputs in `output/preliminary/` for repeated analysis.
- Agree on a short set of shared data products to compare across teams:
  - annual global totals by species
  - normalized trend plots
  - sectoral shares
  - compatibility checks against external inventories

### Good handoff pattern

Each collaborator can take ownership of one clearly bounded domain, while all outputs feed into the same baseline tables. For example:

- Person 1: archive QA and production comparison
- Person 2: external inventory benchmarking
- Person 3: FaIR setup and historical response runs
- Shared: figures, outputs, and interpretation in notebooks

This keeps progress parallel without fragmenting the project.

## 5. One-sentence objective for the meeting

The project is to establish a transparent, reproducible historical SLCF emissions baseline, compare the archived and production CEDS releases, and then convert the validated emissions record into a defensible FaIR-based historical climate evaluation.
