from __future__ import annotations
from pathlib import Path
import json
import os
import numpy as np
import pandas as pd
import yaml
from scipy.stats import kendalltau, theilslopes

ROOT = Path(__file__).resolve().parents[1]

STATION_MAP = {
    "断面编码": "StationID", "断面名称": "StationName", "断面类型": "StationType",
    "所属流域": "WatershedUnit", "流域": "Basin", "所在河流": "River",
    "责任省份": "Province", "责任城市": "City", "经度": "Longitude", "纬度": "Latitude",
    "年": "Year", "月": "Month", "监测时间": "Date", "Do": "DO", "Watertem": "WaterTemp",
    "watertem": "WaterTemp", "flu": "Flu", "NH₃-N": "NH3N", "氨氮": "NH3N",
}
GOV_MAP = {
    "pro": "ProvinceFullName", "dili": "Region",
    "城市排水管道长度（万公里）": "Pipe", "城市污水日处理能力（万立方米）": "Capacity",
    "生态用水总量（亿立方米）": "EcoWater", "建成区绿化覆盖率（%）": "GreenCover",
    "氨氮排放量（万吨）": "NH3NEmission", "总氮排放量（万吨）": "TNEmission",
    "总磷排放量（万吨）": "TPEmission", "化学需氧量排放量（万吨）": "CODEmission",
    "农作物总播种面积（千公顷）": "CropArea",
    "单位农用氮肥施用折纯度（吨/千公顷）": "NFertIntensity",
    "单位农用磷肥施用折纯度（吨/千公顷）": "PFertIntensity",
    "有效灌溉面积（千公顷）": "IrrigatedArea",
}

def load_config(path: str | Path = ROOT / "config.yml") -> dict:
    path = os.environ.get("NS_CONFIG", path)
    path = Path(path)
    if not path.is_absolute(): path = ROOT / path
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def read_table(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    return pd.read_csv(path)

def standardize_columns(df: pd.DataFrame, kind: str) -> pd.DataFrame:
    mapping = STATION_MAP if kind == "station" else GOV_MAP
    out = df.rename(columns=lambda x: mapping.get(str(x).strip(), str(x).strip())).copy()
    if "Date" in out and ("Year" not in out or "Month" not in out):
        dt = pd.to_datetime(out["Date"], errors="coerce")
        out["Year"], out["Month"] = dt.dt.year, dt.dt.month
    return out

def ensure_columns(df: pd.DataFrame, required: list[str], label: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")

def mkdirs(base: Path) -> None:
    for p in ["tables", "source_data", "figures", "audit", "arcgis_join_tables", "model_data"]:
        (base / p).mkdir(parents=True, exist_ok=True)

def bh_adjust(pvalues) -> np.ndarray:
    p = np.asarray(pvalues, dtype=float)
    ok = np.isfinite(p); out = np.full(len(p), np.nan)
    if not ok.any(): return out
    vals = p[ok]; order = np.argsort(vals); ranked = vals[order]
    adj = np.minimum.accumulate((ranked * len(ranked) / np.arange(1, len(ranked)+1))[::-1])[::-1]
    temp = np.empty_like(adj); temp[order] = np.minimum(adj, 1.0); out[ok] = temp
    return out

def mk_sen(year, value) -> dict:
    z = pd.DataFrame({"Year": year, "Value": value}).dropna().sort_values("Year")
    if len(z) < 4: return {"n": len(z), "tau": np.nan, "p": np.nan, "sen": np.nan, "lo": np.nan, "hi": np.nan}
    tau, p = kendalltau(z.Year, z.Value)
    sen, intercept, lo, hi = theilslopes(z.Value, z.Year, alpha=.95)
    return {"n": len(z), "tau": tau, "p": p, "sen": sen, "lo": lo, "hi": hi}

def write_json(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
