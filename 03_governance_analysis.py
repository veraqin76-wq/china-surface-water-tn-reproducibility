from __future__ import annotations
import itertools
import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare, wilcoxon
from src.common import ROOT, load_config, read_table, standardize_columns, ensure_columns, mkdirs, mk_sen, bh_adjust

MEASURES=["Pipe","Capacity","EcoWater","GreenCover","CropArea","IrrigatedArea","NFertIntensity","PFertIntensity"]
SUM_VARS=["Pipe","Capacity","EcoWater","CropArea","IrrigatedArea"]
MEAN_VARS=["GreenCover","NFertIntensity","PFertIntensity"]
CATEGORY={"Pipe":"UrbanPoint","Capacity":"UrbanPoint","EcoWater":"UrbanNonpoint","GreenCover":"UrbanNonpoint","CropArea":"Agricultural","IrrigatedArea":"Agricultural","NFertIntensity":"Agricultural","PFertIntensity":"Agricultural"}

def main():
    cfg=load_config(); base=ROOT/cfg["paths"]["results"]/"03_governance"; mkdirs(base)
    g=standardize_columns(read_table(ROOT/cfg["paths"]["governance"]),"governance"); ensure_columns(g,["Year","Province","Region"]+MEASURES,"governance")
    cov=read_table(ROOT/cfg["paths"]["province_covariates"]); annual=pd.read_csv(ROOT/cfg["paths"]["results"]/"01_trends/model_data/station_annual.csv")
    water=annual.groupby(["Province","Year"])[["TN","TP","COD","NH3N"]].mean().reset_index()
    panel=g.merge(cov,on=["Province","Year"],how="left").merge(water,on=["Province","Year"],how="left")
    panel.to_csv(base/"model_data/province_year_panel.csv",index=False)
    rows=[]
    for p,x in panel.groupby("Province"):
        for v in MEASURES:
            r=mk_sen(x.Year,x[v]); med=x[v].median(); r["relative_sen_pct_yr"]=100*r["sen"]/med if med!=0 else np.nan
            rows.append({"Province":p,"Region":x.Region.iloc[0],"Variable":v,"Category":CATEGORY[v]}|r)
    tr=pd.DataFrame(rows); tr["p_BH"]=bh_adjust(tr.p); tr.to_csv(base/"tables/S6_province_MK_Sen.csv",index=False)
    national=pd.concat([panel.groupby("Year")[SUM_VARS].sum(),panel.groupby("Year")[MEAN_VARS].mean()],axis=1).reset_index()
    regional=pd.concat([panel.groupby(["Region","Year"])[SUM_VARS].sum(),panel.groupby(["Region","Year"])[MEAN_VARS].mean()],axis=1).reset_index()
    national.to_csv(base/"source_data/S6_national_series.csv",index=False); regional.to_csv(base/"source_data/S6_regional_series.csv",index=False)
    wide=tr.pivot(index="Province",columns="Variable",values="relative_sen_pct_yr").abs()
    cat=pd.DataFrame({k:wide[[v for v in MEASURES if CATEGORY[v]==k]].median(axis=1) for k in sorted(set(CATEGORY.values()))}).dropna()
    cats=list(cat.columns); tests=[{"test":"Friedman","statistic":friedmanchisquare(*[cat[c] for c in cats]).statistic,"p":friedmanchisquare(*[cat[c] for c in cats]).pvalue}]
    for a,b in itertools.combinations(cats,2):
        q=wilcoxon(cat[a],cat[b]); tests.append({"test":f"Wilcoxon_{a}_vs_{b}","statistic":q.statistic,"p":q.pvalue})
    tt=pd.DataFrame(tests); indices = tt.index[tt.test.str.startswith("Wilcoxon")]
    ordered = tt.loc[indices, "p"].sort_values()
    adjusted = np.minimum(1, np.maximum.accumulate(ordered.to_numpy() * np.arange(len(ordered), 0, -1)))
    tt.loc[ordered.index, "p_Holm"] = adjusted
    tt.to_csv(base/"tables/S6_category_tests.csv",index=False); tr.to_csv(base/"source_data/S6_province_points.csv",index=False)
    print(f"03 trends complete: {base}")
if __name__=="__main__": main()
