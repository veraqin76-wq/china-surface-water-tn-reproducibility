"""Station-cluster uncertainty for the three ratio definitions and spatial weighting schemes."""
from __future__ import annotations

import importlib

import numpy as np
import pandas as pd

from src.common import ROOT, load_config

analysis = importlib.import_module("01_station_trends_and_stoichiometry")


def summarize(data, cfg):
    years = set(range(cfg["start_year"], cfg["end_year"] + 1))
    balanced = []
    for identifier, group in data.groupby("StationID"):
        if years.issubset(set(group.Year)) and group[["COD", "TN", "TP"]].gt(0).all(axis=None):
            balanced.append(identifier)
    tables = [analysis.ratios_for_group(data, ["Year"]).assign(Sample="all", Area="China")]
    if balanced:
        tables.append(analysis.ratios_for_group(data[data.StationID.isin(balanced)], ["Year"])
                      .assign(Sample="balanced", Area="China"))
    for spatial in ["Basin", "Province"]:
        tables.append(analysis.equal_weight_ratios(data, spatial).assign(Area="China"))
    tables.append(analysis.ratios_for_group(data, ["Basin", "Year"])
                  .rename(columns={"Basin": "Area"}).assign(Sample="basin"))
    return pd.concat(tables, ignore_index=True)



def decompositions(data, cfg):
    years = set(range(cfg["start_year"], cfg["end_year"] + 1))
    balanced = [identifier for identifier, group in data.groupby("StationID")
                if years.issubset(set(group.Year)) and
                group[["COD", "TN", "TP"]].gt(0).all(axis=None)]
    selections = [("National", "China", "all", data),
                  ("National", "China", "balanced", data[data.StationID.isin(balanced)])]
    selections.extend(("Basin", basin, "all", group) for basin, group in data.groupby("Basin"))
    rows = []
    pairs = {"COD_TN": ("COD", "TN"), "TN_TP": ("TN", "TP"), "COD_TP": ("COD", "TP")}
    for scope, area, sample, group in selections:
        for ratio, (numerator, denominator) in pairs.items():
            valid = group.loc[group[numerator].gt(0) & group[denominator].gt(0)]
            if valid.empty:
                continue
            endpoint_years = [valid.Year.min(), valid.Year.max()]
            for method in ["R1", "R3"]:
                concentrations = valid.groupby("Year")[[numerator, denominator]].mean()
                if method == "R3":
                    logged = valid.assign(**{column: np.log(valid[column])
                                             for column in [numerator, denominator]})
                    concentrations = np.exp(logged.groupby("Year")[[numerator, denominator]].mean())
                start, end = concentrations.loc[endpoint_years].to_numpy()
                components = np.log(end / start)
                total = components[0] - components[1]
                rows.append(dict(Scope=scope, Area=area, Sample=sample, Method=method,
                                 Ratio=ratio, StartYear=endpoint_years[0], EndYear=endpoint_years[1],
                                 Numerator_log_change=components[0],
                                 Negative_denominator_log_change=-components[1],
                                 Ratio_log_change=total, Ratio_change_pct=100 * np.expm1(total)))
    return pd.DataFrame(rows)

def main():
    config = load_config()
    settings = config["analysis"]
    out = ROOT / config["paths"]["results"] / "01_trends"
    data = pd.read_csv(out / "model_data/station_annual.csv")
    point = summarize(data, settings)
    decompositions(data, settings).to_csv(out / "tables/S4_S5_log_decomposition.csv", index=False)
    rng = np.random.default_rng(settings["seed"])
    groups = [group for _, group in data.groupby("StationID")]
    draws = []
    for replicate in range(settings["bootstrap_s3"]):
        indices = rng.integers(0, len(groups), len(groups))
        sample = pd.concat([groups[index].assign(StationID=f"bootstrap_{i}")
                            for i, index in enumerate(indices)], ignore_index=True)
        draws.append(summarize(sample, settings).assign(Replicate=replicate))
    raw = pd.concat(draws, ignore_index=True)
    keys = ["Sample", "Area", "Year", "Ratio"]
    interval = raw.groupby(keys)[["R1", "R2", "R3"]].quantile([.025, .975]).unstack(-1)
    interval.columns = [f"{ratio}_{'lo' if quantile == .025 else 'hi'}"
                        for ratio, quantile in interval.columns]
    point.merge(interval.reset_index(), on=keys, how="left").to_csv(
        out / "source_data/S1_S3_ratios_with_intervals.csv", index=False)


if __name__ == "__main__":
    main()
