# Stoichiometric restructuring and total-nitrogen dynamics in Chinese surface waters

Reproducible workflow accompanying the manuscript. The repository separates **workflow reproducibility** from **numerical reproducibility** because the underlying National Environmental Monitoring Network records are subject to redistribution restrictions.

## Release status

Version 1.0.1 is the submission-oriented public release. The Python demonstration workflow and the independent R/`mgcv` demonstration workflow have both been confirmed to complete successfully using the included synthetic inputs. The demonstration verifies executable implementation and output generation; it does not reproduce manuscript numerical estimates.

## Reproducibility modes

```bash
python run_all.py --mode demo
python run_all.py --mode manuscript --config config.manuscript.yml
```

- `demo` generates an explicitly synthetic dataset and runs the full public workflow. Its numerical values are not manuscript results.
- `manuscript` reads authorized analysis data from user-supplied paths and produces manuscript tables, Source Data and diagnostics.

The synthetic data are provided solely to demonstrate the computational workflow. They must not be cited as observations or used to verify manuscript effect sizes.

## Software responsibility

| Component | Software | Purpose |
|---|---|---|
| Cleaning, aggregation, ratios, trend tests, empirical states | Python | Statistical analysis and audit tables |
| Tensor-product and governance GAMs | R `mgcv` | Penalized smooths, random effects, REML and diagnostics |
| Statistical figures | Python or Origin | Origin reads immutable CSV Source Data; it performs no estimation |
| Spatial maps | ArcGIS 10.5 | Joins exported section summaries and draws maps; it performs no trend/GAM estimation |

## Key files

| Path | Description |
|---|---|
| `00_generate_synthetic_data.py` | Creates non-confidential demonstration inputs |
| `01_station_trends_and_stoichiometry.py` | S1–S3 cleaning, annualization, stoichiometry and trends |
| `02_cp_empirical_analysis.py` | S4 lag matching, four states, bins and cluster bootstrap |
| `03_governance_analysis.py` | S6 governance trends and non-parametric comparisons |
| `r/02_cp_tensor_gam.R` | Main COD–TP GAM, M0–M2, diagnostics and predictions |
| `r/02_cp_cross_validation.R` | Within-site contiguous time-block CV |
| `r/02_cp_robustness.R` | Site holdout, rolling extrapolation and basin models |
| `r/03_governance_gam.R` | Provincial governance GAM and counterfactuals |
| `r/03_governance_robustness.R` | Blocked-year CV and lag sensitivity |
| `validation/validate_outputs.py` | Completion and sanity checks |
| `DATA_DICTIONARY.md` | Fields, units and aggregation rules |
| `METHODS_CODE_MAP.md` | Method-to-code crosswalk |

## Installation and execution

Python 3.11+ and R 4.3+ are recommended.

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
Rscript environment/install_R_packages.R
python run_all.py --mode demo
python validation/validate_outputs.py --mode demo
```

Every run writes a log and a SHA-256 output manifest. Random seeds and bootstrap counts are controlled in YAML.

For a rapid installation check, the demo configuration uses reduced model-bootstrap counts. Submission analyses must use the counts in `config.manuscript.example.yml`: 200 station-cluster replicates for the COD–TP model, 500 region-stratified province-cluster replicates for governance models, and 1,000 section-cluster replicates for the empirical state analysis.

## Restricted data

Do not commit `config.manuscript.yml`, raw monitoring data, provider credentials or identifiable site metadata. Manuscript mode requires only variables used in this study; unrelated variables for unpublished studies should be omitted.

## Before journal submission

1. Copy `config.manuscript.example.yml` to the ignored file `config.manuscript.yml` and enter authorized local data paths.
2. Run manuscript mode with the full bootstrap counts.
3. Inspect GAM basis-dimension diagnostics, concurvity and all cross-validation tables.
4. Populate `source_data/` only with approved manuscript-mode values.
5. Replace the GitHub and Zenodo placeholders in the availability statements and `CITATION.cff`.
6. Archive the final run log, R session information and output manifest with the release.

## Conventions

- `r_TN = log(TN_t / TN_t-1)`: negative values indicate declining TN.
- `TN_improvement = log(TN_t-1 / TN_t)`: positive values indicate improvement.
- S4 median states and S5 20th/80th-percentile prediction states are not interchangeable.
- COD is an organic-matter-related water-quality measure, not directly measured elemental carbon.
