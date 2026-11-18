from __future__ import annotations
import argparse, json, os, sys
from pathlib import Path
import pandas as pd, yaml
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument("--mode",choices=["demo","manuscript"],default="demo");ap.add_argument("--config");ap.add_argument("--skip-r",action="store_true");a=ap.parse_args()
cfgpath=Path(a.config or ("config.yml" if a.mode=="demo" else "config.manuscript.yml"));cfgpath=cfgpath if cfgpath.is_absolute() else ROOT/cfgpath
cfg=yaml.safe_load(cfgpath.read_text(encoding="utf-8"));base=ROOT/cfg["paths"]["results"]
required={
 "annual":base/"01_trends/model_data/station_annual.csv",
 "ratios":base/"01_trends/source_data/stoichiometric_ratios_R1_R2_R3.csv",
 "trends":base/"01_trends/tables/mk_sen_pollutants.csv",
 "derivatives":base/"01_trends/source_data"/("S3_python_spline_derivatives.csv" if a.skip_r else "S3_temporal_GAM_derivatives.csv"),
 "paired":base/"01_trends/source_data/S7_S8_paired_improvement.csv",
 "state_periods":base/"02_cp/source_data/S9_S11_S13_state_statistics.csv",
 "cp_panel":base/"02_cp/model_data/cp_model_panel.csv",
 "states":base/"02_cp/source_data/S4_national_median_states.csv",
 "bins":base/"02_cp/source_data/S4_national_2D_bins.csv",
 "governance":base/"03_governance/model_data/province_year_panel.csv",
 "sen_governance":base/"03_governance/tables/S6_province_MK_Sen.csv"}
if not a.skip_r:
 required["surface"] = base/"02_cp/source_data/Fig2_S24_CP_surfaces.csv"
 required["governance_2024"] = base/"03_governance/tables/S13_2024_governance_effects.csv"
errors=[];summary={"mode":a.mode,"checks":{}}
for k,p in required.items():
 if not p.exists(): errors.append(f"missing {p}");continue
 d=pd.read_csv(p); summary["checks"][k]={"rows":len(d),"columns":len(d.columns),"all_missing_columns":d.columns[d.isna().all()].tolist()}
 if len(d)==0: errors.append(f"empty {p}")
annual=pd.read_csv(required["annual"]);cp=pd.read_csv(required["cp_panel"])
if not annual.Year.between(cfg["analysis"]["start_year"],cfg["analysis"]["end_year"]).all():errors.append("annual years outside configured range")
if not ((cp.r_TN<0)|(cp.r_TN>=0)).all():errors.append("non-finite TN changes")
if not (cp[["TN","TN_lag1","COD_lag1","TP_lag1"]]>0).all().all():errors.append("non-positive values in log-ratio panel")
if not a.skip_r:
    fits = pd.read_csv(base/"02_cp/tables/S5_basin_model_fit.csv")
    if fits.Basin.nunique() != cp.Basin.nunique():
        errors.append("some basin models were not exported")
    cv = pd.read_csv(base/"02_cp/tables/S5_blocked_CV.csv")
    if not cv.groupby("Model").Fold.nunique().eq(5).all():
        errors.append("incomplete CP cross-validation folds")
    if cv[["R2", "RMSE", "MAE"]].isna().any().any():
        errors.append("non-finite CP cross-validation metrics")
    scenarios = pd.read_csv(base/"02_cp/tables/S8_counterfactual_predictions.csv")
    supported = scenarios.loc[scenarios.supported]
    if supported[["TN_change_pct", "lo", "hi"]].isna().any().any():
        errors.append("missing supported scenario estimate or interval")
    if not (supported.lo <= supported.hi).all():
        errors.append("unordered CP scenario intervals")
    governance = pd.read_csv(base/"03_governance/tables/S13_2024_governance_effects.csv")
    if governance.ModelScale.nunique() != 2:
        errors.append("incomplete LN/RAW governance coverage")
    if governance.Outcome.nunique() != 4 or governance.Measure.nunique() != 8:
        errors.append("incomplete governance outcome/measure coverage")
    if governance[["decrease", "lo", "hi"]].isna().any().any():
        errors.append("missing governance estimate or interval")
    if not governance.successful.gt(0).all():
        errors.append("some governance strata have no successful bootstrap")
    if not (governance.lo <= governance.hi).all():
        errors.append("unordered governance intervals")
    summary["model_checks"] = {"basins":int(fits.Basin.nunique()),
                               "cp_CV_fits":len(cv),
                               "supported_S8_scenarios":len(supported),
                               "governance_estimates":len(governance)}
summary["errors"]=errors;(base/"validation_report.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
print(json.dumps(summary,indent=2));sys.exit(1 if errors else 0)

