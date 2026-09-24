# File manifest

## Entry points

- `run_all.py`: orchestrates demo or manuscript execution, logging and checksums.
- `00_generate_synthetic_data.py`: creates demonstration data only.
- `01_station_trends_and_stoichiometry.py`: Methods S1–S3.
- `02_cp_empirical_analysis.py`: Method S4 and model-ready panel.
- `03_governance_analysis.py`: Method S6 and governance panel.

## R models

- `r/02_cp_tensor_gam.R`: main response surface, M0–M2 and state predictions.
- `r/02_cp_cross_validation.R`: within-section contiguous time-block CV.
- `r/02_cp_robustness.R`: station holdout, rolling extrapolation and basin models.
- `r/02_cp_cluster_bootstrap.R`: station-cluster model bootstrap.
- `r/03_governance_gam.R`: four water-quality outcomes and counterfactuals.
- `r/03_governance_robustness.R`: blocked-year CV and alternative lags.
- `r/03_governance_bootstrap.R`: region-stratified province-cluster bootstrap.

## Documentation

- `README.md`: public repository landing page.
- `README_CN.md`: Chinese operating notes.
- `REVIEWER_GUIDE.md`: verification scope and reviewer instructions.
- `DATA_DICTIONARY.md`: fields, units and aggregation.
- `METHODS_CODE_MAP.md`: method-to-code crosswalk and readiness state.
- `MANUSCRIPT_METHODS_NOTES.md`: estimands, assumptions and mandatory checks.
- `DATA_AVAILABILITY.md`, `CODE_AVAILABILITY.md`: statement drafts.
- `SOURCE_DATA_GUIDE.md`: journal Source Data rules.

## Environment and validation

- `requirements.txt`: Python requirements.
- `environment/environment.yml`: cross-language Conda environment.
- `environment/install_R_packages.R`: R dependency installation/session capture.
- `validation/validate_outputs.py`: output existence and invariant checks.
- `config.yml`: demo settings.
- `config.manuscript.example.yml`: restricted-data template.

## Data and outputs

- `data/example/`: synthetic inputs, clearly labelled.
- `source_data/`: empty submission placeholder and index template.
- `results/`: reproducible demo outputs; never substitute these for manuscript Source Data.
