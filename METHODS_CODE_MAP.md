# Methods–code–software mapping

| Manuscript method | Implementation | Main output | Status |
|---|---|---|---|
| S1 field harmonization, 3σ screening, short-gap interpolation | `01_station_trends_and_stoichiometry.py` | audit files, cleaned monthly and annual panels | implemented and tested |
| S1 section long-term spatial means | Python aggregation; ArcGIS 10.5 draws map | `station_long_term_means.csv` | join table implemented |
| S2 R1/R2/R3 | Python | `stoichiometric_ratios_R1_R2_R3.csv` | implemented and tested |
| S2 balanced sites, basin/province equal weighting | Python | same file, `Sample` column | implemented and tested |
| S2 log decomposition | Python | `stoichiometric_log_decomposition.csv` | implemented and tested |
| S3 MK and Sen slope | Python/SciPy | `mk_sen_pollutants.csv` | implemented and tested |
| S3 temporal penalized smooth and derivative | Python spline + penalty selection | `S3_temporal_GAM_derivatives.csv` | implemented and tested |
| S3 within-section paired improvement | Python | `within_station_TN_lag.csv` | point estimates implemented; clustered-CI review required before submission |
| S4 median four states and migration | Python | national/basin state CSVs | implemented and tested |
| S4 station-cluster bootstrap 1,000 | Python | CI columns in national state CSV | implemented and tested |
| S4 empirical 2-D bins | Python | national/basin bin CSVs | implemented and tested |
| S4 GAM-transition sensitivity | R surface plus Python state workflow | transition/sensitivity outputs | requires manuscript-mode stable zero-contour review |
| Main COD–TP GAM and basin models | R `mgcv` | model RDS, surface CSV | synthetic-data execution confirmed |
| S5 M0–M2, REML, diagnostics | R `mgcv` | model fit and diagnostics | synthetic-data execution confirmed |
| S5 contiguous time-block CV | R `mgcv` | blocked CV CSV | synthetic-data execution confirmed |
| S5 station holdout and rolling extrapolation | R `mgcv` | `S5_holdout_and_rolling_CV.csv` | synthetic-data execution confirmed |
| S5 20/80 marginal-standardized states | R `mgcv` | four-state prediction CSV | scripted |
| S5 joint-support and model bootstrap | R/Python | model diagnostics | computationally intensive; manuscript-mode verification required |
| S6 MK/Sen/relative Sen | Python/SciPy | provincial/national/regional CSVs | implemented and tested |
| S6 Friedman and paired Wilcoxon/Holm | Python/SciPy | category test CSV | implemented and tested |
| Main governance GAM | R `mgcv` | model RDS and fit table | synthetic-data execution confirmed |
| Governance counterfactual + Duan smearing | R `mgcv` | counterfactual CSVs | scripted |
| Governance blocked CV and lag sensitivity | R `mgcv` | CV/sensitivity CSV | synthetic-data execution confirmed |
| Governance 500 stratified bootstrap | R `mgcv` | bootstrap distributions | must be executed and archived in manuscript mode |

Items requiring manuscript-mode execution are explicitly identified rather than replaced by an unreported approximation. This table must be updated after the restricted-data freeze and before repository release.
