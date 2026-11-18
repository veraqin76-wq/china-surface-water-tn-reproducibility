"""Export station-map layers, temporal-scale series and investment summaries."""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors

from src.common import ROOT, load_config, read_table


def main():
    config = load_config()
    results = ROOT / config["paths"]["results"]
    trends = results / "01_trends"
    annual = pd.read_csv(trends / "model_data/station_annual.csv")
    monthly = pd.read_csv(trends / "model_data/station_monthly_clean.csv")
    pollutants = ["TN", "COD", "NH3N", "TP"]
    years = [config["analysis"]["start_year"], config["analysis"]["end_year"]]
    spatial = annual[annual.Year.isin(years)]
    spatial.to_csv(trends / "arcgis_join_tables/S19_S21_station_endpoints.csv", index=False)
    network = annual.groupby("Year").StationID.nunique().rename("StationCount")
    network.to_csv(trends / "source_data/S19_network_counts.csv")
    grade_rows = []
    thresholds = config.get("water_quality_thresholds", {})
    for baseline_year in years:
        ids = annual.loc[annual.Year.eq(baseline_year), "StationID"].unique()
        subset = annual[annual.StationID.isin(ids)]
        for pollutant in ["COD", "NH3N", "TP"]:
            if pollutant not in thresholds:
                continue
            limits = np.asarray(thresholds[pollutant], dtype=float)
            if len(limits) != 5 or np.any(np.diff(limits) < 0):
                raise ValueError(f"Five ordered Grade I–V limits required for {pollutant}")
            valid = subset.dropna(subset=[pollutant]).copy()
            valid["Grade"] = np.searchsorted(limits, valid[pollutant], side="left") + 1
            counts = valid.groupby(["Year", "Grade"]).size().rename("n").reset_index()
            counts["proportion_pct"] = 100 * counts.n / counts.groupby("Year").n.transform("sum")
            grade_rows.append(counts.assign(Pollutant=pollutant, NetworkBaseline=baseline_year))
    if grade_rows:
        pd.concat(grade_rows).to_csv(trends / "source_data/S20_water_quality_classes.csv", index=False)
    monthly["Season"] = np.select(
        [monthly.Month.isin([3, 4, 5]), monthly.Month.isin([6, 7, 8]),
         monthly.Month.isin([9, 10, 11])], ["Spring", "Summer", "Autumn"], default="Winter")
    monthly["Hydrology"] = np.where(monthly.Month.between(6, 9), "Wet", "Dry")
    series = []
    basin_series = []
    for scale, keys in [("Season", ["Year", "Season"]), ("Hydrology", ["Year", "Hydrology"]),
                        ("Month", ["Year", "Month"])]:
        station_means = monthly.groupby(["StationID", *keys])[pollutants].mean().reset_index()
        summary = station_means.groupby(keys)[pollutants].mean().reset_index().assign(Scale=scale)
        series.append(summary)
        basin_station_means = monthly.groupby(["Basin", "StationID", *keys])[pollutants].mean().reset_index()
        basin_summary = basin_station_means.groupby(["Basin", *keys])[pollutants].mean().reset_index()
        basin_series.append(basin_summary.assign(Scale=scale))
    pd.concat(series, ignore_index=True).to_csv(
        trends / "source_data/S22_S23_temporal_scales.csv", index=False)
    pd.concat(basin_series, ignore_index=True).to_csv(
        trends / "source_data/S22_S23_basin_temporal_scales.csv", index=False)
    panel = pd.read_csv(results / "03_governance/model_data/province_year_panel.csv")
    panel.groupby(["Region", "Year"])[pollutants].mean().to_csv(
        results / "03_governance/source_data/S29_regional_concentrations.csv")
    measures = ["Pipe", "Capacity", "EcoWater", "GreenCover", "CropArea",
                "IrrigatedArea", "NFertIntensity", "PFertIntensity"]
    ordered = panel.sort_values(["Province", "Year"]).copy()
    lagged = ordered.groupby("Province")[measures].shift()
    consecutive = ordered.Year.sub(ordered.groupby("Province").Year.shift()).eq(1)
    lagged = lagged.where(consecutive, axis=0)
    valid = lagged.notna().all(axis=1)
    inputs = lagged.loc[valid]
    center, scale = inputs.mean(), inputs.std().replace(0, 1)
    standardized = (inputs - center) / scale
    neighbours = min(10, len(inputs) - 1)
    if neighbours >= 1:
        estimator = NearestNeighbors().fit(standardized)
        observed_distances = estimator.kneighbors(standardized, n_neighbors=neighbours + 1)[0][:, -1]
        threshold = np.quantile(observed_distances, .95)
        baseline = ordered[ordered.Year.eq(years[0])].set_index("Province")
        support_rows = []
        for measure in measures:
            scenario = inputs.copy()
            scenario[measure] = ordered.loc[valid, "Province"].map(baseline[measure])
            complete = scenario.notna().all(axis=1)
            selected = scenario.loc[complete]
            distances = estimator.kneighbors((selected - center) / scale, n_neighbors=neighbours)[0][:, -1]
            support = ordered.loc[selected.index, ["Province", "Year", "Region"]].copy()
            support["Measure"] = measure
            support["NeighbourDistance"] = distances
            support["SupportThreshold"] = threshold
            support["Supported"] = distances <= threshold
            support_rows.append(support)
        pd.concat(support_rows).to_csv(
            results / "03_governance/source_data/governance_counterfactual_support.csv", index=False)
    investment_path = config["paths"].get("investment")
    if investment_path:
        investment = read_table(ROOT / investment_path)
    elif os.environ.get("NS_MODE") == "demo":
        rng = np.random.default_rng(config["analysis"]["seed"])
        investment = pd.DataFrame({"Year": np.arange(years[0], years[1] + 1)})
        for variable, start, end in [("LEEP", 100, 1000), ("CEEP", 20, 150),
                                     ("Grey", 60, 700), ("Green", 3, 60)]:
            investment[variable] = np.linspace(start, end, len(investment)) * rng.uniform(.95, 1.05, len(investment))
    else:
        investment = None
    if investment is not None:
        required = ["Year", "LEEP", "CEEP", "Grey", "Green"]
        missing = set(required) - set(investment)
        if missing:
            raise ValueError(f"Investment data missing fields: {sorted(missing)}")
        investment = investment.groupby("Year")[required[1:]].sum().reset_index()
        investment["NEEP"] = investment.LEEP + investment.CEEP
        for variable in ["LEEP", "CEEP", "NEEP"]:
            investment[f"{variable}_lo"] = .95 * investment[variable]
            investment[f"{variable}_hi"] = 1.05 * investment[variable]
        investment.to_csv(results / "03_governance/source_data/S27_investment.csv", index=False)


if __name__ == "__main__":
    main()
