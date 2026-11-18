"""Canonical data locations on Gadi (project qv56, read-only).

Every dataset is pinned by source id, and where known by grid label and
version. A CEDS source id can carry more than one of either —
CEDS-CMIP-2025-03-18 has versions v20250325 and v20250327, and
CEDS-CMIP-2025-04-18 has both gn (0.5 degree) and gr (0.1 degree) — so globbing
across them would mix incompatible data. Nothing outside this module should
hardcode a replica path.
"""

from pathlib import Path

QV56 = Path("/g/data/qv56/replicas/input4MIPs")

CEDS = {
    "production":  QV56 / "CMIP7/CMIP/PNNL-JGCRI/CEDS-CMIP-2025-04-18",
    "archive":     QV56 / "CMIP7/CMIP/PNNL-JGCRI/CEDS-CMIP-2025-03-18",
    "preprod_nov": QV56 / "CMIP6Plus/CMIP/PNNL-JGCRI/CEDS-CMIP-2024-11-25",
    # AIR stream only (plus NMVOC surface); ends 2022. Partial publication,
    # not usable for surface emissions comparison.
    "preprod_oct": QV56 / "CMIP6Plus/CMIP/PNNL-JGCRI/CEDS-CMIP-2024-10-21",
    "cmip6":       QV56 / "CMIP6/CMIP/PNNL-JGCRI/CEDS-2017-05-18",
}

CEDS_SUPPLEMENTAL = {
    "production": QV56 / "CMIP7/CMIP/PNNL-JGCRI/CEDS-CMIP-2025-04-18-supplemental",
    "archive":    QV56 / "CMIP7/CMIP/PNNL-JGCRI/CEDS-CMIP-2025-03-18-supplemental",
}

FORCINGS = {
    "biomass_burning": QV56 / "CMIP7/CMIP/DRES/DRES-CMIP-BB4CMIP7-2-1",
    "volcanic":        QV56 / "CMIP7/CMIP/uoexeter/UOEXETER-CMIP-2-2-1",
    "solar":           QV56 / "CMIP6Plus/CMIP/SOLARIS-HEPPA/SOLARIS-HEPPA-CMIP-4-5",
    "scenariomip":     QV56 / "CMIP7/ScenarioMIP/uoexeter/UOEXETER-ScenarioMIP-2-2-2",
}

# Pin the realisation. None means "not yet confirmed" — select_files then does
# not filter, and assert_single_realisation raises if more than one is present.
# Fail loud rather than mix.
VERSIONS = {
    "production":  "v20250421",
    "archive":     None,
    "preprod_nov": None,
    "preprod_oct": None,
    "cmip6":       None,
}

GRID = "gn"