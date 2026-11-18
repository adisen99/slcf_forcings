# CMIP7 SLCF forcings evaluation — Phase 1 findings

**Date:** 2026-11-19
**Status:** Phase 0 complete; Phase 1 global and sectoral comparison complete;
spatial comparison not started.

## Summary

CEDS emissions have changed substantially between CMIP6 (`CEDS-2017-05-18`) and
CMIP7 (`CEDS-CMIP-2025-04-18`). Carbonaceous aerosol is revised sharply
downward in the modern era and upward in the 19th century; the waste sector is
roughly halved across all species; CO2 is essentially unchanged. Comparable
window is 1750–2014, bounded by the CMIP6 release.

## Data and method

All data read from the NCI qv56 input4MIPs replica — nothing downloaded.

| Release | Source id | Grid | Version | Coverage |
|---|---|---|---|---|
| CMIP6 | `CEDS-2017-05-18` | gn | — | 1750–2014 |
| Pre-production | `CEDS-CMIP-2024-11-25` | gn | — | 1750–2022, no NMVOC |
| March | `CEDS-CMIP-2025-03-18` | gn | v20250325 + v20250327 | 1750–2023 |
| **Production** | `CEDS-CMIP-2025-04-18` | gn | v20250421 | 1750–2023 |

Area-weighted integration from kg m-2 s-1 to Tg yr-1 using the supplied
`areacella`, with CF-calendar-aware month lengths. CEDS-2017 ships no
`areacella`; cell areas are computed from its `lat_bnds`/`lon_bnds`, exact on a
regular lat-lon grid.

**Validation.** The pipeline reproduces three independently derived values from
an earlier local run to the cent: SO2 2000 = 107.19 Tg, BC 2000 = 5.47 Tg,
CO2 2000 = 25083.94 Tg.

**Sector definitions are identical** across CMIP6, the November pre-production
and both 2025 releases — all eight sectors match index for index. Sectoral
comparison is therefore valid.

## Findings

### 1. Carbonaceous aerosol: one revision, sign flip mid-century

BC and OC are higher in CMIP7 through the 19th century, peaking around +32% and
+26% in the 1850s, declining smoothly through zero at approximately 1950 (OC)
and 1960 (BC), and reaching −26% and −33% by 2014.

The signal is in **Residential/Commercial** in every period (+32/+26% in
1840–60, +24/+22% in 1890–1910, −25/−23% in 2005–14), consistent with a single
revision to residential solid-fuel emission factors rather than two independent
changes. The transition is smooth, indicating a revised time-varying factor
rather than a discontinuity.

**Implication for FaIR (Phase 4):** a materially different aerosol forcing
trajectory, with more early and less recent carbonaceous aerosol.

### 2. Waste sector roughly halved across all species

Post-1950, waste emissions fall by 56–64% for every species simultaneously
(2014: CO 40.3 → 17.1 Tg, CO2 129 → 49 Tg, NMVOC 7.3 → 2.7 Tg). The curves are
parallel with a constant offset.

A uniform multi-species change of this size is a methodology change, almost
certainly in open-burning treatment. **Action: check against the CEDS CMIP7
release notes.**

### 3. Substantial inter-sector reallocation

Sectoral changes exceed global changes for several species: Energy OC −52%
against global OC −29%; Energy NMVOC −44% against global −22%. Roughly half of
these sectoral signals are redistribution between sectors, not net change.

**Energy and Industrial move in opposite directions in every period** (Industrial
BC +11/+42/+11% while Energy BC −10/−2/−27%). This reciprocity across 160 years
indicates a sector-boundary definition difference. **Recommendation: report
Energy and Industrial combined**, as the split is not comparable between
releases.

### 4. SO2 declines later than the other species

SO2 is near zero through 2007 then falls to −14.3% by 2014 — a later onset than
BC, OC, CO and NOx. Timing is consistent with better representation of Chinese
flue-gas desulfurisation, which scaled up from ~2006.

### 5. CO2 essentially unchanged

Within ±10% across the full record and near zero after 1950, as expected for
the best-constrained species. Serves as a sanity check on the comparison.

### 6. NH3 uniformly negative

−5 to −9% across the entire 1750–2014 record with no sign change, unlike every
other species. Suggests a uniform baseline or emission-factor change. Not yet
explained.

## Caveats

- Percentage differences on small bases produce ratio artefacts. Sectoral
  tables are screened to cells exceeding 1% of the global total and 0.01 Tg
  **in both releases**; historical periods are better read in absolute terms.
- CH4 and N2O are excluded: main-stream coverage begins in 1970 and requires
  the supplemental stream.
- `CEDS-CMIP-2024-10-21` is an AIR-only partial publication and is excluded.
- Global totals only; no regional attribution yet.

## Open questions

1. Does the CEDS CMIP7 documentation explain the waste-sector revision?
2. Is Intl Shipping CO2 at 785 Tg (2014) consistent with IMO estimates? It
   appears high.
3. What drives the uniform NH3 offset?
4. Where is the Residential/Commercial BC/OC change concentrated regionally?

## Next steps

**Phase 1 completion**
- [ ] Spatial differences for BC/OC Residential/Commercial, 1850 and 2010
- [ ] March vs April gridding-issue test (CO, CO2, NOx, 1961–2021) as a
      known-answer validation of the spatial diagnostic
- [ ] Regional decomposition — China, India, Europe, North America
- [ ] Extend to CH4 and N2O using the supplemental stream

**Phase 2**
- [ ] EDGAR and Global Carbon Project comparison
- [ ] BB4CMIP7 for open biomass burning (already on qv56)