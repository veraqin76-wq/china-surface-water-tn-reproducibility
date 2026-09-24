# Reviewer guide

The Python and R demonstration workflows supplied in release 1.0.1 have been confirmed to complete successfully with the included synthetic inputs. This is a workflow-execution check, not numerical reproduction of restricted-data estimates.

## What can be verified publicly

Running `python run_all.py --mode demo` verifies input validation, monthly-to-annual aggregation, trend and ratio calculations, consecutive-year matching, empirical COD–TP states, bootstrap mechanics, model-data construction, governance trend analysis and output provenance. With R installed, the same command also executes the GAM and robustness scripts.

## What cannot be inferred from the demo

The synthetic data do not validate reported effect sizes, transition locations, sample sizes or basin rankings. Exact numerical verification requires the restricted monitoring data. Exact plotted values are supplied separately as journal Source Data.

## Manuscript execution

Authorized users copy `config.manuscript.example.yml` to `config.manuscript.yml`, enter local paths and run:

```bash
python run_all.py --mode manuscript --config config.manuscript.yml
python validation/validate_outputs.py --mode manuscript --config config.manuscript.yml
```

No restricted data are copied into the repository. The output manifest records SHA-256 checksums for traceability.

## Independent checks

1. Inspect `results/01_trends/audit/data_quality_summary.csv` before interpreting results.
2. Confirm reported sample counts against `station_annual.csv` and `cp_model_panel.csv`.
3. Inspect `S5_M2_diagnostics.txt`, CV tables and concurvity before accepting response surfaces.
4. Confirm every manuscript figure panel against the submission Source Data index.
5. Treat model contrasts as associations, not causal effects.
