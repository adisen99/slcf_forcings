#!/usr/bin/env python
"""Plot normalized 2000–2023 CEDS global-emissions trends."""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "output/preliminary/ceds_old_2000_2023_annual_totals_global.csv"
OUTPUT = ROOT / "plots/ceds_old_2000_2023_normalized_emissions.png"


def main() -> None:
    data = pd.read_csv(INPUT)
    series = data.pivot(index="year", columns="species_variable", values="tg_per_year")
    normalized = series.divide(series.loc[2000]).multiply(100)

    fig, axis = plt.subplots(figsize=(10, 6))
    for column in normalized:
        axis.plot(normalized.index, normalized[column], linewidth=2, label=column.removesuffix("_em_anthro"))
    axis.axhline(100, color="0.4", linewidth=1, linestyle="--")
    axis.set(xlabel="Year", ylabel="Emissions index (2000 = 100)", xlim=(2000, 2023))
    axis.legend(ncol=2, frameon=False)
    axis.grid(alpha=0.2)
    fig.tight_layout()
    OUTPUT.parent.mkdir(exist_ok=True)
    fig.savefig(OUTPUT, dpi=180)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
