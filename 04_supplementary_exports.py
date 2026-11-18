"""Assemble supplementary statistical tables from the cleaned analysis panels."""
from __future__ import annotations

import importlib
import itertools
import os

import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare, wilcoxon

from src.common import ROOT, bh_adjust, load_config, mk_sen

station = importlib.import_module("01_station_trends_and_stoichiometry")
empirical = importlib.import_module("02_cp_empirical_analysis")
governance = importlib.import_module("03_governance_analysis")


def paired_improvement(annual, replicates, rng):
    annual = annual.sort_values(["StationID", "Year"])
    previous = annual.groupby("StationID")[["Year", *station.POLLUTANTS]].shift()
    improvement = np.log(previous[station.POLLUTANTS].where(lambda x: x > 0)
                         / annual[station.POLLUTANTS].where(lambda x: x > 0))
    improvement = improvement.loc[annual.Year.sub(previous.Year).eq(1)]
    paired = annual.loc[improvement.index, ["Year", "Basin", "StationID"]].copy()
    rows = []
    for comparator in ["COD", "NH3N", "TP"]:
        paired["Difference"] = improvement[comparator] - improvement["TN"]
        valid = paired.dropna(subset=["Difference"])
        for scope, groups in (("National", ["Year"]), ("Basin", ["Basin", "Year"])):
            for key, group in valid.groupby(groups):
                basin, year = ("China", (key[0] if isinstance(key, tuple) else key)) if scope == "National" else key
                values = group.Difference.to_numpy()
                # Each station contributes one paired value within an annual group.
                draws = rng.choice(values, size=(replicates, len(values)), replace=True)
                limits = np.quantile(
                    [draws.mean(axis=1), np.median(draws, axis=1), (draws > 0).mean(axis=1)],
                    [.025, .975], axis=1,
                )
                rows.append(dict(Scope=scope, Area=basin, Year=year, Comparator=comparator,
                                 n=len(values), mean=values.mean(), median=np.median(values),
                                 prop_slower=(values > 0).mean(), mean_lo=limits[0, 0],
                                 mean_hi=limits[1, 0], median_lo=limits[0, 1],
                                 median_hi=limits[1, 1], prop_lo=limits[0, 2], prop_hi=limits[1, 2]))
    return pd.DataFrame(rows)


def state_exports(annual, cp, settings):
    panel = empirical.prepare(annual)
    bins = [settings["periods"][0][0] - 1] + [end for _, end in settings["periods"]]
    labels = [f"{start}-{end}" for start, end in settings["periods"]]
    panel["Period"] = pd.cut(panel.Year, bins, labels=labels).astype("string")
    transition_path = cp / "tables/S10_transition_positions.csv"
    transitions = pd.read_csv(transition_path) if transition_path.is_file() and os.environ.get("NS_SKIP_R") != "1" else pd.DataFrame()
    outputs, cutoffs, trajectories = [], [], []
    positive = annual.assign(COD=annual.COD.where(annual.COD > 0),
                             TP=annual.TP.where(annual.TP > 0))
    scopes = [("National", "China", panel, positive)]
    scopes.extend(("Basin", basin, group, positive.loc[positive.Basin.eq(basin)])
                  for basin, group in panel.groupby("Basin"))
    for scope, area, group, observations in scopes:
        medians = observations[["COD", "TP"]].median()
        cutoffs.append(dict(Scope=scope, Area=area, COD_cut=medians.COD, TP_cut=medians.TP))
        trajectory = group.groupby("Year")[["COD_lag1", "TP_lag1"]].median().reset_index()
        trajectories.append(trajectory.assign(Scope=scope, Area=area))
        definitions = [("Median", medians.COD, medians.TP)]
        if not transitions.empty:
            row = transitions.loc[transitions.Scope.eq(scope) & transitions.Area.eq(area)]
            if len(row) and row[["COD_cut", "TP_cut"]].notna().all(axis=None):
                definitions.append(("GAM", row.COD_cut.iloc[0], row.TP_cut.iloc[0]))
        for definition, cod, tp in definitions:
            data = group.assign(State=empirical.classify(group, cod, tp))
            annual_stats = empirical.state_stats(data)
            annual_stats["occupancy"] = annual_stats.n / annual_stats.groupby("Year").n.transform("sum")
            stats = data.groupby(["Period", "State"]).agg(
                n=("r_TN", "size"), median_r=("r_TN", "median"),
                prop_nonimproving=("NonImproving", "mean"),
            ).reset_index()
            ci = empirical.cluster_bootstrap_states(
                data, settings["bootstrap_s4"], settings["seed"], ["Period", "State"])
            period_stats = stats.merge(ci, on=["Period", "State"], how="left")
            outputs.extend([annual_stats.assign(Scope=scope, Area=area, Definition=definition),
                            period_stats.assign(Scope=scope, Area=area, Definition=definition)])
    pd.DataFrame(cutoffs).to_csv(cp / "tables/S3_empirical_cutoffs.csv", index=False)
    pd.concat(trajectories).to_csv(cp / "source_data/S10_S12_annual_median_trajectories.csv", index=False)
    pd.concat(outputs, ignore_index=True).to_csv(cp / "source_data/S9_S11_S13_state_statistics.csv", index=False)


def governance_exports(base):
    trends = []
    for scope, filename in (("National", "S6_national_series.csv"), ("Region", "S6_regional_series.csv")):
        series = pd.read_csv(base / "source_data" / filename)
        groups = [("China", series)] if scope == "National" else series.groupby("Region")
        for area, group in groups:
            for measure in governance.MEASURES:
                stats = mk_sen(group.Year, group[measure])
                median = group[measure].median()
                relative = 100 / median if np.isfinite(median) and median != 0 else np.nan
                trends.append(dict(Scope=scope, Area=area, Measure=measure, **stats,
                                   relative_sen=stats["sen"] * relative,
                                   relative_lo=stats["lo"] * relative,
                                   relative_hi=stats["hi"] * relative))
    trend = pd.DataFrame(trends)
    trend["p_BH"] = bh_adjust(trend.p)
    trend.to_csv(base / "tables/S4_management_trends.csv", index=False)
    series = pd.read_csv(base / "source_data/S6_national_series.csv").set_index("Year")
    endpoints = pd.DataFrame({"start": series.iloc[0], "end": series.iloc[-1]})
    endpoints["change_pct"] = 100 * (endpoints.end / endpoints.start.replace(0, np.nan) - 1)
    endpoints.to_csv(base / "tables/S11_management_endpoints.csv", index_label="Measure")

    provinces = pd.read_csv(base / "tables/S6_province_MK_Sen.csv")
    scores = provinces.assign(Magnitude=provinces.relative_sen_pct_yr.abs()).pivot_table(
        index=["Region", "Province"], columns="Category", values="Magnitude", aggfunc="median"
    )
    scores.to_csv(base / "source_data/S16_S18_province_category_scores.csv")
    tests = []
    for area, subset in [("China", scores), *scores.groupby(level="Region")]:
        subset = subset.dropna()
        if len(subset) < 2 or len(subset.columns) < 3:
            continue
        statistic, p = friedmanchisquare(*(subset[col] for col in subset))
        tests.append(dict(Area=area, Test="Friedman", n=len(subset), statistic=statistic, p=p))
        contrasts = []
        for left, right in itertools.combinations(subset.columns, 2):
            statistic, p = ((0, 1) if subset[left].eq(subset[right]).all()
                            else wilcoxon(subset[left], subset[right]))
            contrasts.append(dict(Area=area, Test=f"{left} vs {right}", n=len(subset), statistic=statistic, p=p))
        contrasts.sort(key=lambda x: x["p"])
        adjusted = np.maximum.accumulate([row["p"] * (len(contrasts) - i)
                                         for i, row in enumerate(contrasts)])
        for row, p in zip(contrasts, adjusted):
            tests.append(dict(row, p_Holm=min(1, p)))
    pd.DataFrame(tests).to_csv(base / "tables/S16_S18_category_tests.csv", index=False)


def main():
    config = load_config()
    base = ROOT / config["paths"]["results"]
    settings = config["analysis"]
    trends = base / "01_trends"
    annual = pd.read_csv(trends / "model_data/station_annual.csv")
    rng = np.random.default_rng(settings["seed"])
    paired_improvement(annual, settings["bootstrap_s3"], rng).to_csv(
        trends / "source_data/S7_S8_paired_improvement.csv", index=False)
    decomposition = [station.log_decomposition(annual).assign(Scope="National", Area="China")]
    decomposition.extend(station.log_decomposition(group).assign(Scope="Basin", Area=basin)
                         for basin, group in annual.groupby("Basin"))
    pd.concat(decomposition).to_csv(trends / "tables/S4_S5_log_decomposition.csv", index=False)
    reference = [0.12, 1, 2, 2.18, 2.8, 4.6]
    tn = annual.dropna(subset=["TN"])
    values = tn.assign(**{f"TN_lt_{value:g}": 100 * tn.TN.lt(value) for value in reference})
    proportions = values.groupby("Year")[[f"TN_lt_{value:g}" for value in reference]].mean()
    proportions.assign(n=tn.groupby("Year").size()).to_csv(trends / "tables/S5_TN_reference_proportions.csv")
    state_exports(annual, base / "02_cp", settings)
    governance_exports(base / "03_governance")
    if os.environ.get("NS_SKIP_R") != "1":
        governance = base / "03_governance"
        model_fits = pd.read_csv(governance / "tables/S12_governance_GAM_fit.csv")
        validation = pd.read_csv(governance / "tables/governance_blocked_year_CV.csv")
        comparison = validation.groupby(["Outcome", "ModelScale", "Model"]).R2.mean().unstack("Model").reset_index()
        comparison["CV_increment"] = comparison.Management - comparison.Baseline
        model_fits.merge(comparison, on=["Outcome", "ModelScale"], how="left").to_csv(
            governance / "tables/S12_governance_model_comparison.csv", index=False)
        cp = base / "02_cp"
        point = pd.read_csv(cp / "tables/S5_four_state_predictions.csv")
        intervals = pd.read_csv(cp / "tables/S5_cluster_bootstrap_CI.csv")
        intervals = intervals.drop(columns=["estimate", "supported"], errors="ignore")
        point.merge(intervals, on="State", how="left").to_csv(
            cp / "tables/S8_counterfactual_predictions.csv", index=False)
        fits = pd.read_csv(cp / "tables/S5_model_fit.csv")
        folds = pd.read_csv(cp / "tables/S5_blocked_CV.csv")
        scores = folds.groupby("Model").agg(
            CV_R2_mean=("R2", "mean"), CV_R2_sd=("R2", "std"),
            CV_RMSE_mean=("RMSE", "mean"), CV_MAE_mean=("MAE", "mean"))
        fits.merge(scores, on="Model", how="left").to_csv(
            cp / "tables/S7_model_comparison.csv", index=False)


if __name__ == "__main__":
    main()
