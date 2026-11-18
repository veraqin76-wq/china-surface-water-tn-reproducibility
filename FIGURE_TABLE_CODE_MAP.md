# Figure, table and script index

The workflow exports analytical source tables as CSV files and fitted GAMs as RDS files. The figure renderer produces PDF and PNG analysis plots. Spatial layers are exported for ArcGIS. Paths below are relative to the configured results directory.

## Main figures

| Figure | Analysis scripts | Principal outputs and methods |
| --- | --- | --- |
| Fig. 1a | `01_station_trends_and_stoichiometry.py`; `05_ratio_uncertainty.py` | `01_trends/source_data/S1_S3_ratios_with_intervals.csv`. Ratios of concentration means, arithmetic and geometric station-ratio means, and station-cluster intervals. |
| Fig. 1b–l | `r/01_temporal_gam.R` | `01_trends/source_data/S3_temporal_GAM_derivatives.csv`. REML temporal GAMs of log annual mean concentrations, finite-difference derivatives and covariance-based pointwise intervals. |
| Fig. 2 | `r/02_cp_tensor_gam.R`; `r/02_cp_robustness.R`; `r/02_cp_surfaces.R` | `02_cp/source_data/Fig2_S24_CP_surfaces.csv` and `S10_zero_contour_coordinates.csv`. National and basin tensor-product GAMs, supported prediction grids and zero contours. Annual TN means are supplied by script 01. |
| Fig. 3 | `03_governance_analysis.py`; `r/03_governance_2024.R` | `03_governance/source_data/Fig3_2024_province_counterfactuals.csv` and `tables/S13_2024_governance_effects.csv`. Joint management GAMs, province-specific baseline scenarios, Duan smearing and region-stratified province-cluster bootstrap. Positive `decrease` denotes a lower concentration under observed management. |

## Supplementary figures

| Figure | Scripts | Principal outputs and methods |
| --- | --- | --- |
| Figs. S1–S3 | 01; 05 | `01_trends/source_data/S1_S3_ratios_with_intervals.csv`. Alternative ratio definitions, balanced networks, spatial weighting and basin summaries with station-cluster intervals. |
| Figs. S4–S5 | 01; 04 | `01_trends/tables/S4_S5_log_decomposition.csv`. National and basin endpoint log decomposition. |
| Fig. S6 | `r/01_temporal_gam.R` | Temporal GAM derivative file used for Fig. 1. |
| Figs. S7–S8 | 04 | `01_trends/source_data/S7_S8_paired_improvement.csv`. Comparator-minus-TN log improvement, mean/median differences, proportions and annual station-resampling intervals. |
| Figs. S9, S11 | 02; 04 | `02_cp/source_data/S9_S11_S13_state_statistics.csv`, `Definition=Median`. Annual occupancy and period-stratified empirical TN responses, with full-trajectory station-cluster intervals for period statistics. |
| Figs. S10, S12 | 02; 04 | `02_cp/source_data/S4_national_2D_bins.csv`, `S4_basin_2D_bins.csv` and `S10_S12_annual_median_trajectories.csv`. Two-dimensional empirical bins and annual lagged-COD/TP median trajectories. |
| Figs. S13–S14 | `r/02_cp_surfaces.R`; 02; 04 | State-statistics file with `Definition=GAM`, zero-contour cut-offs and empirical bin files. GAM-derived cut-offs are held fixed during empirical resampling. |
| Figs. S15–S18 | 03; 04 | `03_governance/tables/S4_management_trends.csv`, `S16_S18_category_tests.csv` and `source_data/S16_S18_province_category_scores.csv`. Mann–Kendall tests, Sen slopes, relative slopes, Friedman tests and Holm-adjusted paired Wilcoxon tests. |
| Figs. S19, S21 | 01; 06 | `01_trends/arcgis_join_tables/S19_S21_station_endpoints.csv` and `source_data/S19_network_counts.csv`. Station endpoint layers and annual network counts. |
| Fig. S20 | 06 | `01_trends/source_data/S20_water_quality_classes.csv`. Grade distributions under the start-year and end-year station-network baselines. Supply the study's Grade I–V limits in `water_quality_thresholds`. |
| Figs. S22–S23 | 06 | `01_trends/source_data/S22_S23_temporal_scales.csv`. Station-first aggregation of seasonal, wet/dry and monthly concentration series. |
| Fig. S24 | `r/02_cp_robustness.R`; `r/02_cp_surfaces.R` | Basin rows in the surface file used for Fig. 2. |
| Figs. S25–S26 | 01 | `01_trends/source_data/basin_annual_means.csv`. Basin trajectories and final-year concentrations. |
| Fig. S27 | 06 | `03_governance/source_data/S27_investment.csv`. NEEP = LEEP + CEEP, grey/green investment totals and the specified ±5% bands. Manuscript input uses `paths.investment`. |
| Fig. S28 | 03 | `03_governance/model_data/province_year_panel.csv`. Provincial distributions and national annual means of management measures. |
| Fig. S29 | 06 | `03_governance/source_data/S29_regional_concentrations.csv`. Regional concentration series derived from province-year means. |

Numbers 01–07 refer to the numbered Python entry points in the repository. `07_render_figures.py` renders ratio, derivative, national/basin GAM surface and management-response analysis plots from these exports. ArcGIS supplies the spatial layout for maps.

## Supplementary tables

| Table | Script | Output |
| --- | --- | --- |
| S1–S2 | 01 | `01_trends/tables/mk_sen_pollutants.csv` |
| S3 | 04 | `02_cp/tables/S3_empirical_cutoffs.csv` |
| S4 | 04 | `03_governance/tables/S4_management_trends.csv` |
| S5 | 04 | `01_trends/tables/S5_TN_reference_proportions.csv`. Values are percentages. |
| S5b | Literature compilation | Benchmark descriptions and cited sources are supplied in the SI. |
| S6 | `r/02_cp_tensor_gam.R` | `02_cp/tables/S6_national_M2_summary.csv` and `S6_national_M2_smooth_terms.csv` |
| S7 | `r/02_cp_tensor_gam.R`; `r/02_cp_cross_validation.R` | `02_cp/tables/S5_model_fit.csv` and `S5_blocked_CV.csv` |
| S8 | `r/02_cp_tensor_gam.R`; `r/02_cp_cluster_bootstrap.R` | `02_cp/tables/S8_counterfactual_predictions.csv`, assembled from the point and bootstrap exports |
| S9 | `r/02_cp_robustness.R` | `02_cp/tables/S5_basin_model_fit.csv` |
| S10 | `r/02_cp_surfaces.R` | `02_cp/tables/S10_transition_positions.csv` |
| S11 | 04 | `03_governance/tables/S11_management_endpoints.csv` |
| S12 | `r/03_governance_2024.R` | `03_governance/tables/S12_governance_model_comparison.csv`. LN/RAW fits, EDF, AICc and original-scale full/baseline cross-validation. |
| S13 | `r/03_governance_2024.R` | `03_governance/tables/S13_2024_governance_effects.csv`. LN and RAW original-scale scenario differences and intervals. |

## Additional governance diagnostics

`r/04_governance_sensitivity.R` exports `governance_province_influence.csv` and, when flow records are available, `governance_hydrological_sensitivity.csv`. Province influence compares each omission fit with the full fit on the same retained-province target-year observations. Hydrological fits use matched samples with and without a log-flow smooth. The demo checks two province omissions per pollutant, while manuscript mode checks every province.

`06_context_exports.py` exports `governance_counterfactual_support.csv`. This diagnostic compares each scenario's 10th-nearest-neighbour distance in standardized lagged-management space with the 95th percentile of observed leave-one-out distances.
