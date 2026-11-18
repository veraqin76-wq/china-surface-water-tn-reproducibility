from __future__ import annotations
import os

import numpy as np
import pandas as pd
from src.common import ROOT, ensure_columns, load_config, mkdirs, read_table

def prepare(a):
    a=a.sort_values(["StationID","Year"]).copy()
    for c in ["TN","COD","TP","DO","WaterTemp","Flu"]:
        if c in a:
            a[c+"_lag1"]=a.groupby("StationID")[c].shift(); a[c+"_lag_year"]=a.groupby("StationID")["Year"].shift()
    valid=(a.Year-a.TN_lag_year==1)&(a.TN>0)&(a.TN_lag1>0)&(a.COD_lag1>0)&(a.TP_lag1>0)
    z=a[valid].copy(); z["r_TN"]=np.log(z.TN/z.TN_lag1); z["TN_change_pct"]=100*np.expm1(z.r_TN); z["NonImproving"]=(z.r_TN>=0).astype(int)
    return z

def classify(z,cod_cut,tp_cut):
    return np.where(z.COD_lag1<=cod_cut,np.where(z.TP_lag1<=tp_cut,"LL","LH"),np.where(z.TP_lag1<=tp_cut,"HL","HH"))

def state_stats(z,scope="National"):
    group=["Year","State"] if scope=="National" else ["Basin","Year","State"]
    return z.groupby(group).agg(n=("r_TN","size"),median_r=("r_TN","median"),median_pct=("TN_change_pct","median"),prop_nonimproving=("NonImproving","mean")).reset_index()

def grid(z,codw,tpw,minn):
    x=z.copy(); x["COD_bin"]=np.floor(x.COD_lag1/codw)*codw; x["TP_bin"]=np.floor(x.TP_lag1/tpw)*tpw
    x["Period"]=pd.cut(x.Year,[2006,2010,2015,2020,2024],labels=["2007-2010","2011-2015","2016-2020","2021-2024"])
    out=x.groupby(["Period","COD_bin","TP_bin"],observed=True).agg(n=("r_TN","size"),median_r=("r_TN","median"),prop_nonimproving=("NonImproving","mean")).reset_index()
    return out[out.n>=minn]

def cluster_bootstrap_states(z, nboot, seed, group_cols):
    rng = np.random.default_rng(seed)
    station_rows = list(z.groupby("StationID", sort=False).indices.values())
    collected = []
    for b in range(nboot):
        sampled = rng.integers(0, len(station_rows), size=len(station_rows))
        q = z.iloc[np.concatenate([station_rows[i] for i in sampled])]
        s=q.groupby(group_cols).agg(median_r=("r_TN","median"),prop_nonimproving=("NonImproving","mean")).reset_index(); s["boot"]=b; collected.append(s)
    allb=pd.concat(collected,ignore_index=True)
    return allb.groupby(group_cols).agg(successful_bootstraps=("boot","nunique"),median_r_lo=("median_r",lambda x:x.quantile(.025)),median_r_hi=("median_r",lambda x:x.quantile(.975)),prop_lo=("prop_nonimproving",lambda x:x.quantile(.025)),prop_hi=("prop_nonimproving",lambda x:x.quantile(.975))).reset_index()

def join_current_year_climate(panel, paths, mode):
    climate_path = paths.get("station_year_climate")
    keys = ["StationID", "Year"]
    if mode == "demo" and not climate_path:
        # The bundled demo has synthetic climate at province-year resolution.
        climate_path = paths["province_covariates"]
        keys = ["Province", "Year"]
    if not climate_path:
        raise ValueError("Manuscript mode requires paths.station_year_climate (station-year climate data).")

    climate = read_table(ROOT / climate_path).copy()
    if keys[0] == "Province":
        climate = climate.rename(columns={"Temperature": "AirTemperature"})
    fields = ["AirTemperature", "Precipitation"]
    ensure_columns(climate, keys + fields, "COD–TP climate panel")
    climate = climate[keys + fields].copy()
    climate["Year"] = pd.to_numeric(climate["Year"], errors="raise")
    for field in fields:
        climate[field] = pd.to_numeric(climate[field], errors="raise")
    joined = panel.merge(climate, on=keys, how="left", validate="many_to_one")
    valid = np.isfinite(joined[fields]).all(axis=1)
    print(f"COD–TP climate complete cases: {valid.sum()} of {len(joined)}")
    if not valid.any():
        raise ValueError("No model observations have matched air temperature and precipitation.")
    return joined.loc[valid].copy()


def main():
    cfg=load_config(); base=ROOT/cfg["paths"]["results"]/"02_cp"; mkdirs(base)
    a=pd.read_csv(ROOT/cfg["paths"]["results"]/"01_trends/model_data/station_annual.csv"); z=prepare(a)
    cod=a.COD[a.COD.gt(0)].median(); tp=a.TP[a.TP.gt(0)].median(); z["State"]=classify(z,cod,tp)
    ns=state_stats(z); nci=cluster_bootstrap_states(z,cfg["analysis"]["bootstrap_s4"],cfg["analysis"]["seed"],["Year","State"]); ns.merge(nci,on=["Year","State"],how="left").to_csv(base/"source_data/S4_national_median_states.csv",index=False)
    cuts=a.assign(COD=a.COD.where(a.COD.gt(0)), TP=a.TP.where(a.TP.gt(0))).groupby("Basin")[["COD","TP"]].median().rename(columns={"COD":"COD_cut","TP":"TP_cut"})
    zb=z.join(cuts,on="Basin"); zb["State"]=np.where(zb.COD_lag1<=zb.COD_cut,np.where(zb.TP_lag1<=zb.TP_cut,"LL","LH"),np.where(zb.TP_lag1<=zb.TP_cut,"HL","HH"))
    bs=state_stats(zb,"Basin"); bs.to_csv(base/"source_data/S4_basin_median_states.csv",index=False)
    grid(z,cfg["analysis"]["cp_bin_cod"],cfg["analysis"]["cp_bin_tp"],cfg["analysis"]["cp_bin_min_n"]).to_csv(base/"source_data/S4_national_2D_bins.csv",index=False)
    bg=zb.copy(); bg["COD_bin"]=np.floor(bg.COD_lag1/cfg["analysis"]["cp_bin_cod"])*cfg["analysis"]["cp_bin_cod"]; bg["TP_bin"]=np.floor(bg.TP_lag1/cfg["analysis"]["cp_bin_tp"])*cfg["analysis"]["cp_bin_tp"]
    bg=bg.groupby(["Basin","COD_bin","TP_bin"]).agg(n=("r_TN","size"),median_r=("r_TN","median"),prop_nonimproving=("NonImproving","mean")).reset_index(); bg[bg.n>=cfg["analysis"]["cp_bin_min_n"]].to_csv(base/"source_data/S4_basin_2D_bins.csv",index=False)
    model_panel = join_current_year_climate(z, cfg["paths"], os.environ.get("NS_MODE", "demo"))
    model_panel.to_csv(base/"model_data/cp_model_panel.csv", index=False)
    pd.DataFrame([{"COD_median_cut":cod,"TP_median_cut":tp}]).to_csv(base/"tables/S4_national_cutoffs.csv",index=False)
    print(f"02 empirical complete: {base}")
if __name__=="__main__": main()
