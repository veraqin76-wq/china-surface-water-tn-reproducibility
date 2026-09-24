# Statistical implementation notes

## S1 preprocessing

The public workflow records every exclusion and aggregation decision. The current 3σ implementation is section-by-calendar-month screening on the original scale, followed by optional interpolation of one internal missing month within a section-year. This operational definition must match the final Methods; if the historical analysis used a different grouping or log-scale rule, change the code and text together. Interpolation is never applied across year boundaries or at series ends.

## S2 stoichiometry

R1 is the ratio of annual arithmetic mean concentrations, R2 the arithmetic mean of positive section ratios, and R3 their geometric mean. Balanced sections must be observed in every configured year. Basin- and province-equal results first calculate the statistic within each spatial unit and then average units equally. Log decomposition uses `Delta log(X/Y) = Delta log X - Delta log Y`.

## S3 trends

Mann–Kendall and Sen estimates operate on annual national/basin mean series. The Python spline derivative is a reproducible screening implementation. Claims of statistically significant increasing/decreasing intervals require derivative uncertainty from a formal GAM and must be checked against the final manuscript output. Same-section improvement uses only consecutive positive observations.

## Main COD–TP GAM and S5

The response is `log(TN_t/TN_t-1)`. Lagged COD and TP are log-transformed. M0–M2 share controls and random effects; M2 adds separate thin-plate main effects and a `ti()` tensor interaction. Station and year are random-effect smooths and smoothing is selected by REML. Predictions excluding random-effect terms are population-average associations. They are not causal effects. The zero contour separates negative from non-negative fitted changes but is not automatically a mechanistic threshold.

## S4 empirical validation

Median states use fixed long-term national or basin medians. Empirical bins use previous-year COD and TP, specified widths and a minimum cell size without smoothing or extrapolation. Sections, not rows, are resampled so each selected trajectory remains intact.

## Governance models

One-year-lagged measures enter jointly with nonlinear year, temperature, precipitation and province effects. For a response observed in 2007, the first lagged measure corresponds to its 2006 value; counterfactual baselines therefore use the first finite lagged value in each province. Duan smearing is applied after log-response prediction. Counterfactual contrasts are associational and depend on observed support.

## Mandatory pre-submission checks

1. Freeze the restricted analysis extract and retain its checksum privately.
2. Run full manuscript mode with R and archive the log and session information.
3. Resolve all `gam.check` basis warnings and inspect concurvity.
4. Confirm every reported number against machine-readable output.
5. Populate the journal Source Data directory only from manuscript-mode results.
6. Replace all URL/DOI placeholders and update citation metadata.

