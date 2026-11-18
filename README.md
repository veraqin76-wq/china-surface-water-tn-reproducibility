# Stoichiometric restructuring and total-nitrogen dynamics in Chinese surface waters

Python and R scripts for the study's preprocessing, stoichiometric analyses, pollutant trends, empirical COD–TP states, tensor-product GAMs and governance analyses. The included synthetic records demonstrate execution. Manuscript mode reads the authorized local study inputs.

## Installation

Python 3.11+ and R 4.3+ are recommended.

```bash
pip install -r requirements.txt
Rscript environment/install_R_packages.R
```

## Run

```bash
python run_all.py --mode demo
python validation/validate_outputs.py --mode demo
```

For the study inputs, copy `config.manuscript.example.yml` to `config.manuscript.yml`, enter local input paths and run:

```bash
python run_all.py --mode manuscript --config config.manuscript.yml
python validation/validate_outputs.py --mode manuscript --config config.manuscript.yml
```

The manuscript configuration uses 1,000 empirical station-cluster replicates, 200 COD–TP model replicates and 500 region-stratified province-cluster replicates for governance. The demonstration configuration uses reduced counts.

The COD–TP climate input has one row per `StationID, Year`, with `AirTemperature` and `Precipitation` on the TN response year. The governance climate input uses `Temperature` for air temperature. Field names and units are described in `DATA_DICTIONARY.md`.

## Figure and table outputs

`FIGURE_TABLE_CODE_MAP.md` lists the scripts, methods and CSV outputs corresponding to each main and supplementary figure/table. `07_render_figures.py` draws analysis plots. CSV spatial layers are supplied for ArcGIS layout.

Supplementary inputs are configured as follows.

- Fig. S20 reads five Grade I–V limits per pollutant from `water_quality_thresholds`.
- Fig. S27 reads `paths.investment`, containing `Year, LEEP, CEEP, Grey, Green` in RMB 100 million.
- Maps use the exported station tables and the study's geographic boundary layers.

Logs and SHA-256 output manifests are written to the configured results directory. The underlying monitoring records are subject to redistribution restrictions. Public inputs in `data/example/` are synthetic.

## Demonstration validation

The complete Python and R demonstration completed successfully with the reduced bootstrap counts in config.yml. Validation covered all ten basin models, 25 COD–TP cross-validation fits, LN/RAW governance outputs and 21 PDF analysis plots. Run and validation records are included in validation/.
