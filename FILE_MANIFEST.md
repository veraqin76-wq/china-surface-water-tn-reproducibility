# Repository contents

- `run_all.py` executes the configured analysis steps and writes run logs and SHA-256 output checksums.
- `00_generate_synthetic_data.py` generates demonstration inputs.
- `01_station_trends_and_stoichiometry.py` cleans monthly records and exports annual station records, ratios, trends and spatial tables.
- `02_cp_empirical_analysis.py` matches lagged chemistry to TN responses and constructs empirical states and the climate-matched model panel.
- `03_governance_analysis.py` constructs the province panel and management-indicator summaries.
- `04_supplementary_exports.py` exports paired differences, period-level state statistics, management trends, category tests and manuscript tables.
- `05_ratio_uncertainty.py` adds ratio cluster-bootstrap intervals and national/basin decompositions.
- `06_context_exports.py` exports spatial endpoints, temporal-scale series, configured grade distributions and investment series.
- `07_render_figures.py` renders analysis plots from exported source data.
- `r/` contains the temporal GAM, COD–TP national/basin models and validation, scenario/bootstrap procedures and governance models.
- `data/templates/` contains input field templates.
- `validation/validate_outputs.py` checks required outputs and core data constraints.
- `FIGURE_TABLE_CODE_MAP.md` maps figure/table identifiers to methods, scripts and outputs.
