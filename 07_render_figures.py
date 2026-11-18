"""Render analysis figures from the exported CSV source data."""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.common import ROOT, load_config

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                     "axes.spines.top": False, "axes.spines.right": False})


def line_panels(data, group, value, destination, ylabel):
    levels = list(data[group].dropna().unique())
    fig, axes = plt.subplots(len(levels), 1, figsize=(7, max(3, len(levels) * 2.2)), squeeze=False)
    for axis, level in zip(axes.flat, levels):
        subset = data[data[group].eq(level)]
        for label, series in subset.groupby("Series", sort=False):
            series = series.sort_values("Year")
            axis.plot(series.Year, series[value], label=str(label), linewidth=1.3)
        axis.set(title=str(level), ylabel=ylabel)
        axis.legend(fontsize=7, frameon=False, ncol=4)
    axes.flat[-1].set_xlabel("Year")
    fig.tight_layout()
    fig.savefig(destination.with_suffix(".pdf"))
    fig.savefig(destination.with_suffix(".png"), dpi=180)
    plt.close(fig)


def main():
    cfg = load_config()
    base = ROOT / cfg["paths"]["results"]
    out = base / "figures"
    out.mkdir(exist_ok=True)
    ratios = pd.read_csv(base / "01_trends/source_data/S1_S3_ratios_with_intervals.csv")
    ratios = ratios[ratios.Sample.eq("all")].melt(
        id_vars=["Year", "Ratio"], value_vars=["R1", "R2", "R3"], var_name="Series", value_name="value")
    line_panels(ratios, "Ratio", "value", out / "FigS1_ratio_definitions", "Concentration ratio")
    derivative_path = base / "01_trends/source_data/S3_temporal_GAM_derivatives.csv"
    if derivative_path.is_file():
        derivatives = pd.read_csv(derivative_path).rename(columns={"Pollutant": "Series"})
        line_panels(derivatives, "Area", "annual_change_pct", out / "Fig1_S6_derivatives", "Annual change (%)")
    surface_path = base / "02_cp/source_data/Fig2_S24_CP_surfaces.csv"
    if surface_path.is_file():
        surfaces = pd.read_csv(surface_path)
        transitions = pd.read_csv(base / "02_cp/tables/S10_transition_positions.csv")
        for area, group in surfaces.groupby("Area"):
            field = group.pivot(index="TP", columns="COD", values="TN_change_pct")
            support = group.pivot(index="TP", columns="COD", values="supported")
            z = np.ma.masked_where(~support.to_numpy(dtype=bool), field.to_numpy())
            fig, axis = plt.subplots(figsize=(6, 4))
            image = axis.pcolormesh(field.columns, field.index, z, cmap="RdBu_r", shading="auto")
            if z.count() and z.min() < 0 < z.max():
                axis.contour(field.columns, field.index, z, levels=[0], colors="black")
            transition = transitions.loc[transitions.Area.eq(area)]
            if len(transition) and transition[["COD_cut", "TP_cut"]].notna().all(axis=None):
                axis.axvline(transition.COD_cut.iloc[0], color="red", linestyle="--", linewidth=.9)
                axis.axhline(transition.TP_cut.iloc[0], color="red", linestyle="--", linewidth=.9)
            axis.set(xlabel="Preceding-year COD (mg/L)", ylabel="Preceding-year TP (mg/L)", title=area)
            fig.colorbar(image, ax=axis, label="Annual TN change (%)")
            fig.tight_layout()
            safe = "".join(letter if letter.isalnum() else "_" for letter in str(area))
            fig.savefig(out / f"Fig2_S24_{safe}.pdf")
            plt.close(fig)
    effects_path = base / "03_governance/tables/S13_2024_governance_effects.csv"
    if effects_path.is_file():
        effects = pd.read_csv(effects_path)
        effects = effects[effects.ModelScale.eq("LN")]
        smooths = pd.read_csv(base / "03_governance/tables/governance_smooth_terms.csv")
        smooths = smooths[smooths.ModelScale.eq("LN")].copy()
        smooths["Measure"] = smooths.Term.str.extract(r"^s\((.+)_lag1\)$", expand=False)
        smooths = smooths.dropna(subset=["Measure"]).rename(columns={"p-value": "association_p"})
        effects = effects.merge(smooths[["Outcome", "Measure", "association_p"]],
                                on=["Outcome", "Measure"], how="left")
        for region, group in effects.groupby("Region"):
            group = group.copy()
            if region == "China":
                group.loc[group.association_p.ge(.05) | group.association_p.isna(), "decrease"] = np.nan
            table = group.pivot(index="Measure", columns="Outcome", values="decrease")
            axis = table.plot.bar(figsize=(9, 4))
            axis.axhline(0, color="black", linewidth=.6)
            axis.set(ylabel="Model-associated concentration decrease (mg/L)", title=region)
            fig = axis.get_figure()
            fig.tight_layout()
            safe = "".join(letter if letter.isalnum() else "_" for letter in str(region))
            fig.savefig(out / f"Fig3_{safe}.pdf")
            plt.close(fig)


if __name__ == "__main__":
    main()
