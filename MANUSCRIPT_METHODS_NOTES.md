# Statistical methods

## Preprocessing and ratios

Records are screened by station and calendar month using a 3σ rule on the original concentration scale. Actual month positions are retained. Optional interpolation fills isolated internal one-month gaps within station-years. Annual means use the configured per-variable minimum valid-month count.

R1 is the ratio of arithmetic mean concentrations, R2 the arithmetic mean of station ratios and R3 their geometric mean. The common balanced panel has positive COD, TN and TP in every configured year. Spatial equal weighting first computes each spatial unit's ratio and then averages units equally. Ratio intervals resample whole station trajectories.

## Trends and paired changes

Mann–Kendall and Sen estimates use annual national/basin mean series. Relative pollutant slopes divide by the corresponding long-term mean. The Southeast Rivers COD trend starts in 2007 as specified in the SI.

The R temporal model fits log annual national/basin mean concentration against a penalised year smooth using REML. Derivatives use central finite differences with a 0.01-year step and pointwise covariance-based intervals. The Python-only spline diagnostic has a separate filename.

Annual improvement is log(previous concentration/current concentration). Paired differences equal comparator improvement minus TN improvement, so positive differences indicate slower TN improvement. Annual intervals resample stations within each annual comparison.

## COD–TP models

The response is log(TN_t/TN_t-1). Predictors include preceding-year log COD and log TP, current-year air temperature and precipitation, and station/year random-effect smooths. M2 adds a tensor-product interaction. Model smoothing uses REML.

Surface predictions hold climate covariates at medians and exclude station/year effects. Gaussian KDE in standardized log-COD/log-TP space identifies joint support. Zero contours are extracted from supported grid cells. COD and TP transition coordinates are the separate minima on the contour.

Scenario predictions set COD and TP to their respective 20th or 80th percentiles. Predicted log changes are averaged over the observed climate covariates with station and year effects excluded, and converted to percentages using 100 × [exp(mean predicted log change) − 1]. Empirical states use national or basin-specific long-term medians of positive annual concentrations.

## Governance models

The eight one-year-lagged management measures enter jointly with year, air-temperature and precipitation smooths and a province random effect. LN and RAW models use GCV. LN predictions use Duan smearing. Blocked-year validation reports original-concentration-scale performance for both response scales.

Management scenarios use each province's first study-year values. The target-year concentration decrease equals the baseline-management prediction minus the observed-management prediction. Province predictions are averaged equally within national and regional summaries. Model uncertainty uses region-stratified province-cluster resampling.

Additional exports cover 0–3-year lag structures, raw/log specifications, basis checks, concurvity, available flow-adjusted models, province omission influence and joint-management scenario support.
