
You need membership of `qv56` (request via my.nci.org.au) and the storage flag
in any PBS job or ARE session:

```bash
#PBS -l storage=gdata/qv56+gdata/xp65+scratch/<proj>
```

Use the shared analysis environment rather than building your own:

```bash
module use /g/data/xp65/public/modules
module load conda/analysis3
export PYTHONPATH="$PWD/src"
```

It provides xarray, dask, pandas, matplotlib, cartopy and netcdf4. A personal
environment (`environment.yml`) is only needed for `fair`, at Phase 4.

Outputs are written to `output/`, which is gitignored. For anything large,
point it at `/scratch/<proj>/$USER`.

## Data layer

`src/slcf_forcings/paths.py` pins every dataset by source id, grid label and
version. Nothing elsewhere should hardcode a replica path.

### CEDS anthropogenic emissions

| Role | Source id | Grid | Version | Files | Size |
|---|---|---|---|---|---|
| **Production** | `CEDS-CMIP-2025-04-18` | gn | `v20250421` | 105 | 51.5 GB |
| Reference (March) | `CEDS-CMIP-2025-03-18` | gn | `v20250325` + `v20250327` | 97 + 8 | 51.5 GB |
| Pre-production | `CEDS-CMIP-2024-11-25` | gn | — | — | — |
| Pre-production | `CEDS-CMIP-2024-10-21` | gn | — | — | — |
| CMIP6 | `CEDS-2017-05-18` | gn | — | — | — |

Supplemental streams exist for the 2025 releases (200 gn files, 81.3 GB each)
and carry solid-biofuel emissions, speciated NMVOCs and the pre-1970 CH4/N2O
extension.

A `gr` (0.1-degree) grid exists for `CEDS-CMIP-2025-04-18` only — 440 main and
1012 supplemental files, 247 GB. Deliberately out of scope; it would only be
needed for fine-scale regional work.

### Companion forcings

| Dataset | Path under qv56 | Needed for |
|---|---|---|
| Biomass burning | `CMIP7/CMIP/DRES/DRES-CMIP-BB4CMIP7-2-1` | Phase 2 |
| Volcanic | `CMIP7/CMIP/uoexeter/UOEXETER-CMIP-2-2-1` | Phase 4 |
| Solar | `CMIP6Plus/CMIP/SOLARIS-HEPPA/SOLARIS-HEPPA-CMIP-4-5` | Phase 4 |
| ScenarioMIP | `CMIP7/ScenarioMIP/uoexeter/UOEXETER-ScenarioMIP-2-2-2` | Phase 5 |

Still to source externally: EDGAR, Global Carbon Project CO2, NOAA GML
concentrations, and an observational temperature series (HadCRUT5, Berkeley
Earth or GISTEMP).

## Two traps this code guards against

**Chunk boundaries move between releases.** CEDS-CMIP-2025-03-18 splits CH4 and
N2O at `197001-201912`, April at `197001-199912`. Selecting files by matching a
literal chunk string therefore returns ten species for one release and eight
for the other, with no error. `select_files()` selects by *parsed time
coverage* and raises on a missing species.

**Sector definitions are not stable across releases.** Sectors are a bare
integer coordinate with names in an attribute. An index-to-index comparison
between CEDS-2017 and CEDS-CMIP-2025 would produce plausible, wrong numbers.
Call `compare_sector_definitions()` before any sectoral comparison and map
through names, not indices.

Two further guards: `assert_single_realisation()` refuses to mix grid labels or
versions, and `_aligned_cell_area()` verifies the area grid matches the
emissions grid — xarray's inner-join alignment would otherwise silently shrink
the product rather than raise.

## Repository layout

| Location | Contents |
|---|---|
| `notebooks/00_qv56_data_discovery.ipynb` | What is available on qv56 and whether it is sufficient |
| `notebooks/01_ceds_inventory_qa.ipynb` | Integrity audit and provenance manifest |
| `notebooks/02_release_timeseries.ipynb` | Annual totals across CEDS releases |
| `notebooks/03_release_spatial.ipynb` | Gridded differences where totals diverge |
| `src/slcf_forcings/paths.py` | Pinned dataset locations |
| `src/slcf_forcings/ceds.py` | Discovery, audit, manifest, area-weighted aggregation |
| `src/slcf_forcings/compare.py` | Release intercomparison |
| `output/` | Derived tables and figures (gitignored) |
| `legacy/` | Retired local-download workflow; provenance only |

Analysis lives in notebooks; reusable logic lives in `src/`. Notebooks should
call helpers rather than embedding logic inline.

## Analysis design

The primary window is **1750–2023** for the CMIP7 releases. Comparisons against
CMIP6 CEDS are bounded by that release's end year (2014), set by inner join on
year rather than assumed.

Main-stream CH4 and N2O begin in 1970; earlier coverage requires the
supplemental stream.

### Directly evaluated quantities

- File integrity, units, time coverage, sector definitions, area-weighted
  global totals.
- Release-to-release differences in totals, trends, sector shares and spatial
  patterns.
- Emissions trends compared with independent inventories.
- FaIR simulated CO2, CH4 and N2O concentrations compared with observations.
- FaIR all-forcing global-mean temperature compared with an observational
  series.

### FaIR counterfactuals (Phase 4)

- Historical all-forcing reference run.
- Fixed aerosol emissions after a selected reference year.
- SO2-only, BC-only, OC-only, and NOx/NMVOC/CO precursor experiments.
- Sector-removal experiments: energy, industry, surface transport,
  residential/commercial, shipping, agriculture, solvents, waste.
- Ensemble sensitivity across calibrated FaIR parameters.

FaIR is appropriate for global concentrations, effective radiative forcing and
global-mean temperature. It must not be used to claim a resolved regional
climate or air-quality response from the gridded fields alone.

## Chronological TODO

### Phase 0 — data layer and QA

- [x] Notebook-first workflow with reusable logic in `src/`.
- [x] Inventory the qv56 input4MIPs replica; confirm CEDS, biomass-burning,
      solar and volcanic availability.
- [x] Pin source id, grid label and version for every dataset (`paths.py`).
- [x] Select files by parsed time coverage, not chunk-string matching.
- [x] Guard against mixed grids and versions, and against grid misalignment
      between emissions and `areacella`.
- [ ] Run the integrity audit over every release to be compared.
- [ ] Write the provenance manifest: source id, version, grid, coverage,
      checksum, licence, tracking id.
- [ ] Confirm the two March versions (`v20250325`, `v20250327`) and identify
      which eight files were reissued.

### Phase 1 — release intercomparison

- [ ] Annual global and sectoral totals for each release: CMIP6
      `CEDS-2017-05-18`, pre-production `2024-10-21` and `2024-11-25`, and
      CMIP7 `2025-03-18` and `2025-04-18`.
- [ ] Map sector definitions across releases before any sectoral comparison.
- [ ] Time-series differences by species: absolute and percentage, with the
      comparable window set by the shorter release.
- [ ] Spatial difference maps for the species and years where totals diverge.
- [ ] Test whether the documented March CO/CO2/NOx gridding issue in energy and
      industry (1961–2021) is visible, and resolved in April.
- [ ] Regional decomposition — most CMIP6-to-CMIP7 SLCF revisions are regional
      (China SO2, India, shipping) and global totals will understate them.

### Phase 2 — independent evaluation

- [ ] Acquire and harmonise EDGAR and Global Carbon Project CO2.
- [ ] Compare against BB4CMIP7 for open biomass burning.
- [ ] Compare global totals, growth rates, sector shares and regional patterns;
      report agreement and disagreement rather than choosing a reference by
      default.
- [ ] Select the final annual series and document every splice, regrid and
      unit-conversion decision.

### Phase 3 — pipeline hardening

- [ ] Reproducible end-to-end aggregation from replica to tables.
- [ ] Automated checks: missing months, negative or impossible values,
      discontinuities, duplicated fields, double counting of supplemental data.
- [ ] Unit tests for aggregation arithmetic, unit conversion and sector mapping.
- [ ] Documented release process for derived products.

### Phase 4 — FaIR historical evaluation

- [ ] Convert evaluated annual emissions to FaIR species inputs.
- [ ] Add solar and volcanic forcing from qv56.
- [ ] Run an ensemble of historical all-forcing simulations.
- [ ] Compare simulated concentrations with NOAA GML and temperature with an
      observational series.
- [ ] Diagnose bias without silently tuning parameters to match observations.
- [ ] Species and sector counterfactual ensembles; quantify ERF and
      global-mean temperature changes with uncertainty intervals.

### Phase 5 — longer-term

- [ ] Extend to 1750 using the supplemental stream.
- [ ] ScenarioMIP pathways for future air-pollution and mitigation trade-offs.
- [ ] Compare FaIR attribution against CMIP7 ESM output as it appears.
- [ ] Aerosol optical-depth / ERF observational constraints.
- [ ] Fine-scale regional work using the `gr` 0.1-degree grid, if regional
      impacts become a goal. This is a separate project scope.

## Suggested team split

| Role | Responsibility | Near-term deliverable |
|---|---|---|
| Data and QA | Replica inventory, metadata, aggregation, manifests, tests | Validated annual species/sector/region tables per release |
| Release intercomparison | CMIP6-to-CMIP7 differencing, sector mapping, spatial diagnostics | Release-change report |
| External evaluation | Inventory and observational acquisition, harmonisation | Independent benchmark report |
| FaIR modelling | Input builder, ensemble runs, counterfactuals | Reproducible historical and attribution experiments |
| Integration | Notebook structure, figures, uncertainty synthesis, documentation | Reproducible release and methods narrative |

## Scope boundaries

The project will not produce regional air-quality estimates, infer causal
regional temperature effects from emissions maps, or run chemistry-transport
models. Those are sensible follow-ons only once the historical
emissions-to-FaIR workflow is validated.

## Key references

- [input4MIPs: anthropogenic SLCF and CO2 emissions](https://input4mips-cvs.readthedocs.io/en/latest/dataset-overviews/anthropogenic-slcf-co2-emissions/)
- [CMIP7 forcing datasets](https://wcrp-cmip.org/cmip-phases/cmip7/cmip7-forcing-datasets/)
- [ScenarioMIP-CMIP7 protocol](https://gmd.copernicus.org/articles/19/2627/2026/)
- [NCI CMIP data](https://opus.nci.org.au/display/CMIP/CMIP+Home)
- [qv56 catalogue record](https://geonetwork.nci.org.au/geonetwork/srv/eng/catalog.search#/metadata/f4756_8918_5098_5424)
- [FaIR documentation](https://docs.fairmodel.net/)