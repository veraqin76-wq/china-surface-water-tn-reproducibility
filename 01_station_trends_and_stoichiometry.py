from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.preprocessing import SplineTransformer
from sklearn.linear_model import RidgeCV
from src.common import ROOT, load_config, read_table, standardize_columns, ensure_columns, mkdirs, mk_sen, bh_adjust

POLLUTANTS=["TN","TP","COD","NH3N"]
META=["StationID","StationName","StationType","WatershedUnit","Basin","River","Province","City","Longitude","Latitude"]

def preprocess(cfg):
    raw=standardize_columns(read_table(ROOT/cfg["paths"]["station_monthly"]),"station")
    ensure_columns(raw,["StationID","Basin","Province","Year","Month"]+POLLUTANTS,"station data")
    nums=POLLUTANTS+[c for c in ["DO","WaterTemp","Flu","Longitude","Latitude","Year","Month"] if c in raw]
    for c in nums: raw[c]=pd.to_numeric(raw[c],errors="coerce").replace([np.inf, -np.inf], np.nan)
    raw=raw.query("Year >= @cfg['analysis']['start_year'] and Year <= @cfg['analysis']['end_year']").copy()
    dup=raw.duplicated(["StationID","Year","Month"],keep=False)
    audit={"raw_rows":len(raw),"duplicate_station_month_rows":int(dup.sum())}
    if dup.any():
        meta=[c for c in META if c in raw]
        keys = ["StationID", "Year", "Month"]
        aggregation = {column: "first" for column in meta if column not in keys}
        aggregation.update({column: "mean" for column in nums
                            if column not in keys + ["Longitude", "Latitude"]})
        raw = raw.groupby(keys, dropna=False, as_index=False).agg(aggregation)
    calendar = []
    for (_, _), group in raw.groupby(["StationID", "Year"], sort=False):
        group = group.set_index("Month").reindex(range(1, 13))
        for field in [c for c in META + ["Year"] if c in group]:
            group[field] = group[field].ffill().bfill()
        calendar.append(group.rename_axis("Month").reset_index())
    raw = pd.concat(calendar, ignore_index=True)
    flagged=[]
    for c in [x for x in POLLUTANTS+["DO","WaterTemp","Flu"] if x in raw]:
        raw.loc[raw[c]<=0 if c in POLLUTANTS+["Flu"] else pd.Series(False,index=raw.index),c]=np.nan
        mu=raw.groupby(["StationID","Month"])[c].transform("mean")
        sd=raw.groupby(["StationID","Month"])[c].transform("std")
        bad=(sd>0)&((raw[c]-mu).abs()>cfg["analysis"]["sigma_threshold"]*sd)
        flagged.append(pd.DataFrame({"row":raw.index[bad],"variable":c,"value":raw.loc[bad,c]}))
        raw.loc[bad,c]=np.nan
        if cfg["analysis"]["interpolate_single_month_gap"]:
            raw=raw.sort_values(["StationID","Year","Month"])
            def isolated_gap(series):
                interpolated = series.interpolate(limit_area="inside")
                isolated = series.isna() & series.shift().notna() & series.shift(-1).notna()
                return series.where(~isolated, interpolated)
            raw[c]=raw.groupby(["StationID","Year"],group_keys=False)[c].transform(isolated_gap)
    valcols=[c for c in POLLUTANTS+["DO","WaterTemp","Flu"] if c in raw]
    meta=[c for c in META if c in raw]
    counts=raw.groupby(["StationID","Year"])[valcols].count().add_suffix("_n_month")
    annual=raw.groupby(meta+["Year"],dropna=False)[valcols].mean().reset_index().merge(counts.reset_index(),on=["StationID","Year"])
    for c in valcols:
        annual.loc[annual[c+"_n_month"]<cfg["analysis"]["min_months_per_station_year"],c]=np.nan
    audit.update({"annual_rows":len(annual),"stations":annual.StationID.nunique(),"flagged_3sigma":sum(len(x) for x in flagged)})
    return raw,annual,pd.concat(flagged,ignore_index=True),audit

def ratios_for_group(df, group):
    pairs={"COD_TN":("COD","TN"),"TN_TP":("TN","TP"),"COD_TP":("COD","TP")}; rows=[]
    for keys,g in df.groupby(group,dropna=False):
        keys=(keys,) if not isinstance(keys,tuple) else keys
        base=dict(zip(group,keys))
        for name,(x,y) in pairs.items():
            z=g[[x,y]].dropna(); z=z[(z[x]>0)&(z[y]>0)]
            if len(z): rows.append(base|{"Ratio":name,"R1":z[x].mean()/z[y].mean(),"R2":np.mean(z[x]/z[y]),"R3":np.exp(np.mean(np.log(z[x]/z[y]))),"n":len(z)})
    return pd.DataFrame(rows)

def equal_weight_ratios(annual, spatial):
    inner=ratios_for_group(annual,["Year",spatial])
    return inner.groupby(["Year","Ratio"])[["R1","R2","R3"]].mean().reset_index().assign(Sample=f"{spatial}_equal")

def trends(annual):
    series=[]
    for scope,groups in [("National",[]),("Basin",["Basin"])]:
        iterator=[("China",annual)] if not groups else annual.groupby(groups[0])
        for area,g in iterator:
            yy=g.groupby("Year")[POLLUTANTS].mean().reset_index()
            for p in POLLUTANTS:
                selected = yy.loc[yy.Year.ge(2007)] if scope == "Basin" and area == "SeR" and p == "COD" else yy
                result = mk_sen(selected.Year, selected[p])
                mean = selected[p].mean()
                result.update(relative_sen_pct_yr=100 * result["sen"] / mean,
                              relative_lo=100 * result["lo"] / mean,
                              relative_hi=100 * result["hi"] / mean)
                series.append({"Scope":scope,"Area":area,"Pollutant":p}|result)
    out=pd.DataFrame(series); out["p_BH"]=bh_adjust(out.p); return out

def paired_change(annual, nboot, seed):
    a=annual.sort_values(["StationID","Year"]).copy()
    for p in POLLUTANTS:
        a[p+"_lag"]=a.groupby("StationID")[p].shift(); a[p+"_lag_year"]=a.groupby("StationID")["Year"].shift()
        a[p+"_improve"]=np.where((a.Year-a[p+"_lag_year"]==1)&(a[p]>0)&(a[p+"_lag"]>0),np.log(a[p+"_lag"]/a[p]),np.nan)
    rows=[]
    for q in ["COD","TP","NH3N"]:
        a["diff"]=a[q+"_improve"]-a["TN_improve"]
        for (year,basin),g in a.groupby(["Year","Basin"]):
            z=g.dropna(subset=["diff"]); rows.append({"Year":year,"Basin":basin,"Comparator":q,"n":len(z),"mean":z["diff"].mean(),"median":z["diff"].median(),"prop_slower":(z["diff"]>0).mean()})
    return pd.DataFrame(rows)

def log_decomposition(annual):
    pairs={"COD_TN":("COD","TN"),"TN_TP":("TN","TP"),"COD_TP":("COD","TP")}; rows=[]
    means=annual.groupby("Year")[POLLUTANTS].mean()
    y0,y1=means.index.min(),means.index.max()
    for name,(x,y) in pairs.items():
        dx=np.log(means.loc[y1,x]/means.loc[y0,x]); dy=np.log(means.loc[y1,y]/means.loc[y0,y]); total=dx-dy
        rows.append({"Ratio":name,"StartYear":y0,"EndYear":y1,"Numerator_log_change":dx,"Denominator_log_change":dy,"Ratio_log_change":total,
                     "Numerator_contribution":dx/total if total else np.nan,"Negative_denominator_contribution":(-dy)/total if total else np.nan})
    return pd.DataFrame(rows)

def temporal_smooth_derivative(annual):
    rows=[]
    for scope,iterator in [("National",[("China",annual)]),("Basin",annual.groupby("Basin"))]:
        for area,g in iterator:
            yy=g.groupby("Year")[POLLUTANTS].mean().reset_index()
            x=yy[["Year"]].to_numpy(); grid=np.arange(int(yy.Year.min()),int(yy.Year.max())+1,dtype=float)[:,None]
            for p in POLLUTANTS:
                ok=yy[p].gt(0)&yy[p].notna()
                if ok.sum()<8: continue
                spl=SplineTransformer(n_knots=min(8,int(ok.sum())-2),degree=3,include_bias=False)
                X=spl.fit_transform(x[ok]); model=RidgeCV(alphas=np.logspace(-4,4,81)).fit(X,np.log(yy.loc[ok,p]))
                h=.01; pred=model.predict(spl.transform(grid)); deriv=(model.predict(spl.transform(grid+h))-model.predict(spl.transform(grid-h)))/(2*h)
                for yr,fit,d in zip(grid.ravel(),pred,deriv): rows.append({"Scope":scope,"Area":area,"Pollutant":p,"Year":int(yr),"log_fitted":fit,"first_derivative":d,"annual_change_pct":100*np.expm1(d),"ridge_alpha":model.alpha_})
    return pd.DataFrame(rows)

def main():
    cfg=load_config(); base=ROOT/cfg["paths"]["results"]/"01_trends"; mkdirs(base)
    raw,annual,flags,audit=preprocess(cfg)
    raw.to_csv(base/"model_data/station_monthly_clean.csv",index=False); annual.to_csv(base/"model_data/station_annual.csv",index=False)
    flags.to_csv(base/"audit/outliers_3sigma.csv",index=False); pd.DataFrame([audit]).to_csv(base/"audit/data_quality_summary.csv",index=False)
    allr=ratios_for_group(annual,["Year"]).assign(Sample="all")
    balanced_ids = [identifier for identifier, group in annual.groupby("StationID")
                    if group.Year.nunique() == cfg["analysis"]["end_year"] - cfg["analysis"]["start_year"] + 1
                    and group[["COD", "TN", "TP"]].gt(0).all(axis=None)]
    bal=ratios_for_group(annual[annual.StationID.isin(balanced_ids)],["Year"]).assign(Sample="balanced")
    rr=pd.concat([allr,bal,equal_weight_ratios(annual,"Basin"),equal_weight_ratios(annual,"Province")],ignore_index=True)
    rr.to_csv(base/"source_data/stoichiometric_ratios_R1_R2_R3.csv",index=False)
    trend=trends(annual); trend.to_csv(base/"tables/mk_sen_pollutants.csv",index=False)
    log_decomposition(annual).to_csv(base/"tables/stoichiometric_log_decomposition.csv",index=False)
    temporal_smooth_derivative(annual).to_csv(base/"source_data/S3_python_spline_derivatives.csv",index=False)
    paired=paired_change(annual,cfg["analysis"]["bootstrap_s3"],cfg["analysis"]["seed"]); paired.to_csv(base/"source_data/within_station_TN_lag.csv",index=False)
    annual.groupby("Year")[POLLUTANTS].mean().reset_index().to_csv(base/"source_data/national_annual_means.csv",index=False)
    annual.groupby(["Basin","Year"])[POLLUTANTS].mean().reset_index().to_csv(base/"source_data/basin_annual_means.csv",index=False)
    annual.groupby("StationID",as_index=False).agg({
        **{column: "first" for column in ["StationName", "Basin", "Province", "Longitude", "Latitude"] if column in annual},
        **{p:"mean" for p in POLLUTANTS}}).to_csv(base/"arcgis_join_tables/station_long_term_means.csv",index=False)
    print(f"01 complete: {base}")
if __name__=="__main__": main()
