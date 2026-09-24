from pathlib import Path
import numpy as np
import pandas as pd
from src.common import ROOT, load_config

cfg = load_config(); rng = np.random.default_rng(cfg["analysis"]["seed"])
out = ROOT / "data/example"; out.mkdir(parents=True, exist_ok=True)
years = np.arange(2006, 2025); months = np.arange(1, 13)
basins = ["SeR","HaR","HuR","YeR","LiR","SoR","NwR","SwR","YaR","PeR"]
provinces = ["Beijing","Tianjin","Hebei","Shanxi","InnerMongolia","Liaoning","Jilin","Heilongjiang",
             "Shanghai","Jiangsu","Zhejiang","Anhui","Fujian","Jiangxi","Shandong","Henan","Hubei",
             "Hunan","Guangdong","Guangxi","Hainan","Chongqing","Sichuan","Guizhou","Yunnan","Tibet",
             "Shaanxi","Gansu","Qinghai","Ningxia","Xinjiang"]
regions = ["North","North","North","North","North","Northeast","Northeast","Northeast",
           "East","East","East","East","East","East","East","Central","Central","Central","South",
           "South","South","Southwest","Southwest","Southwest","Southwest","Southwest","Northwest",
           "Northwest","Northwest","Northwest","Northwest"]
n_station = 180
station = pd.DataFrame({
    "StationID":[f"S{i:04d}" for i in range(n_station)],
    "StationName":[f"Station_{i:04d}" for i in range(n_station)],
    "StationType":"National", "WatershedUnit":[f"WU{i%60:03d}" for i in range(n_station)],
    "Basin":rng.choice(basins,n_station), "River":[f"River_{i%40:02d}" for i in range(n_station)],
    "Province":rng.choice(provinces,n_station), "City":[f"City_{i%70:02d}" for i in range(n_station)],
    "Longitude":rng.uniform(82,131,n_station), "Latitude":rng.uniform(22,48,n_station),
    "start":np.where(np.arange(n_station)<80,2006,rng.integers(2007,2021,n_station))})
rows=[]
for s in station.itertuples(index=False):
    site_eff=rng.normal(0,.25)
    for y in years[years>=s.start]:
        tt=y-2006
        cod_base=30*np.exp(-.052*tt); tp_base=.24*np.exp(-.072*tt); nh_base=1.9*np.exp(-.10*tt)
        tn_base=3.9*np.exp(-.035*min(tt,6))*np.exp(-.006*max(tt-6,0))
        for m in months:
            season=np.sin(2*np.pi*(m-1)/12)
            cod=max(.3,cod_base*np.exp(site_eff+rng.normal(0,.18))*(1+.07*season))
            tp=max(.002,tp_base*np.exp(.5*site_eff+rng.normal(0,.25))*(1+.12*season))
            tn=max(.03,tn_base*np.exp(.35*site_eff+rng.normal(0,.17))*(1+.05*season))
            nh=max(.005,nh_base*np.exp(.5*site_eff+rng.normal(0,.25)))
            rows.append([s.StationID,s.StationName,s.StationType,s.WatershedUnit,s.Basin,s.River,s.Province,s.City,
                         s.Longitude,s.Latitude,y,m,cod,nh,tn,tp,7.5+rng.normal(0,.8),15+10*season+rng.normal(),
                         np.exp(rng.normal(-1,.5))])
monthly=pd.DataFrame(rows,columns=["StationID","StationName","StationType","WatershedUnit","Basin","River",
    "Province","City","Longitude","Latitude","Year","Month","COD","NH3N","TN","TP","DO","WaterTemp","Flu"])
for c in ["COD","NH3N","TN","TP","DO","WaterTemp","Flu"]:
    monthly.loc[rng.choice(monthly.index,int(.003*len(monthly)),replace=False),c]=np.nan
monthly.to_csv(out/"station_monthly_synthetic.csv",index=False)

gov=[]; cov=[]
for j,(p,r) in enumerate(zip(provinces,regions)):
    scale=np.exp(rng.normal(0,.45))
    for y in years:
        t=y-2006
        pipe=.7*scale*np.exp(.075*t); cap=180*scale*np.exp(.052*t); eco=2*scale*np.exp(.06*t)
        green=min(55,30+1.0*t+rng.normal(0,1)); crop=2500*scale*(1+rng.normal(0,.02))
        irrig=1200*scale*np.exp(.008*t); nf=190*np.exp(-.026*t)*np.exp(rng.normal(0,.03)); pf=60*np.exp(-.024*t)*np.exp(rng.normal(0,.03))
        gov.append([y,p,r,pipe,cap,eco,green,8*scale*np.exp(-.07*t),12*scale*np.exp(-.03*t),
                    2*scale*np.exp(-.055*t),60*scale*np.exp(-.06*t),crop,nf,pf,irrig])
        cov.append([y,p,8+j%10+.025*t+rng.normal(0,.4),500+j%7*100+rng.normal(0,40),.45+.005*t+rng.normal(0,.02)])
pd.DataFrame(gov,columns=["Year","Province","Region","Pipe","Capacity","EcoWater","GreenCover","NH3NEmission",
 "TNEmission","TPEmission","CODEmission","CropArea","NFertIntensity","PFertIntensity","IrrigatedArea"]).to_csv(out/"governance_synthetic.csv",index=False)
pd.DataFrame(cov,columns=["Year","Province","Temperature","Precipitation","NDVI"]).to_csv(out/"province_covariates_synthetic.csv",index=False)
print(f"Synthetic files written to {out}")
