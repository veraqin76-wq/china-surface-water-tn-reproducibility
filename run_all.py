from __future__ import annotations
import argparse, shutil, subprocess, sys, os, hashlib, json, datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def run(cmd, env, log):
    line="RUN: "+" ".join(map(str,cmd)); print(line); log.write(line+"\n"); log.flush()
    subprocess.run(cmd,cwd=ROOT,check=True,env=env,stdout=log,stderr=subprocess.STDOUT)
def manifest(result_dir):
    rows=[]
    for p in sorted(result_dir.rglob("*")):
        if p.is_file() and p.name != "output_manifest.json": rows.append({"path":str(p.relative_to(ROOT)),"bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
    (result_dir/"output_manifest.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--mode",choices=["demo","manuscript"],default="demo"); ap.add_argument("--config"); ap.add_argument("--skip-r",action="store_true"); a=ap.parse_args()
    config=a.config or ("config.yml" if a.mode=="demo" else "config.manuscript.yml")
    if not (ROOT/config).exists() and not Path(config).is_absolute(): raise SystemExit(f"Configuration not found: {config}. Copy config.manuscript.example.yml to config.manuscript.yml and edit paths.")
    env=os.environ.copy(); env["NS_CONFIG"]=str(Path(config).resolve() if Path(config).exists() else config); env["NS_MODE"]=a.mode; env["NS_SKIP_R"]=str(int(a.skip_r))
    import yaml
    cfg=yaml.safe_load(Path(env["NS_CONFIG"]).read_text(encoding="utf-8")); result_dir=ROOT/cfg["paths"]["results"]; result_dir.mkdir(parents=True,exist_ok=True); env["NS_SEED"]=str(cfg["analysis"]["seed"])
    log_path=result_dir/f"run_{datetime.datetime.now().strftime('%Y%m%dT%H%M%S')}.log"
    with log_path.open("w",encoding="utf-8") as log:
      if a.mode=="demo": run([sys.executable,"00_generate_synthetic_data.py"],env,log)
      run([sys.executable,"01_station_trends_and_stoichiometry.py"],env,log); run([sys.executable,"02_cp_empirical_analysis.py"],env,log); run([sys.executable,"03_governance_analysis.py"],env,log)
      if not a.skip_r:
        if not shutil.which("Rscript"): raise SystemExit("Rscript not found. Install R packages or use --skip-r for Python-only diagnostics.")
        cp=str(result_dir/"02_cp/model_data/cp_model_panel.csv"); cpout=str(result_dir/"02_cp"); gov=str(result_dir/"03_governance/model_data/province_year_panel.csv"); govout=str(result_dir/"03_governance")
        run(["Rscript","r/01_temporal_gam.R",str(result_dir/"01_trends")],env,log)
        run(["Rscript","r/02_cp_tensor_gam.R",cp,cpout],env,log); run(["Rscript","r/02_cp_cross_validation.R",cp,str(result_dir/"02_cp/tables/S5_blocked_CV.csv")],env,log); run(["Rscript","r/02_cp_robustness.R",cp,cpout],env,log); run(["Rscript","r/03_governance_gam.R",gov,govout],env,log); run(["Rscript","r/03_governance_robustness.R",gov,govout],env,log)
        run(["Rscript","r/02_cp_cluster_bootstrap.R",cp,cpout,str(cfg["analysis"].get("bootstrap_cp_model",200)),str(cfg["analysis"]["seed"])],env,log)
        run(["Rscript","r/03_governance_2024.R",gov,govout,str(cfg["analysis"].get("bootstrap_governance",500)),str(cfg["analysis"]["seed"])],env,log)
        run(["Rscript","r/02_cp_surfaces.R",cp,cpout],env,log)
        run(["Rscript","r/04_governance_sensitivity.R",gov,govout,str(result_dir/"01_trends/model_data/station_annual.csv")],env,log)
      run([sys.executable,"04_supplementary_exports.py"],env,log)
      run([sys.executable,"05_ratio_uncertainty.py"],env,log)
      run([sys.executable,"06_context_exports.py"],env,log)
      run([sys.executable,"07_render_figures.py"],env,log)
    manifest(result_dir)
    print("All requested modules completed.")
