#!/usr/bin/env Rscript
suppressPackageStartupMessages({library(mgcv); library(data.table)})
set.seed(as.integer(Sys.getenv("NS_SEED", "20260924")))
args <- commandArgs(trailingOnly = TRUE)
d <- fread(args[1])
out <- args[2]
setorder(d, Province, Year)
d[, ProvinceF := factor(Province)]
measures <- c("Pipe", "Capacity", "EcoWater", "GreenCover", "CropArea",
              "IrrigatedArea", "NFertIntensity", "PFertIntensity")
outcomes <- c("TN", "NH3N", "COD", "TP")

lag_panel <- function(lag) {
    x <- copy(d)
    for (measure in measures) {
        x[, paste0(measure, "_lag1") := if (lag == 0L) get(measure) else
          fifelse(Year - shift(Year, lag) == lag, shift(get(measure), lag), NA_real_),
          by = Province]
    }
    x
}
form <- function(outcome, baseline = FALSE, raw = FALSE) {
    terms <- c("s(Year, bs='tp', k=8)", "s(Temperature, bs='tp', k=6)",
               "s(Precipitation, bs='tp', k=6)", "s(ProvinceF, bs='re')")
    if (!baseline) terms <- c(terms, paste0("s(", measures, "_lag1,bs='tp',k=6)"))
    reformulate(terms, if (raw) outcome else paste0("log(", outcome, ")"))
}
fit_model <- function(formula, data) {
    gam(formula, data = data, method = "GCV.Cp", select = TRUE, na.action = na.exclude)
}
x <- lag_panel(1L)
folds <- split(sort(unique(x$Year)), cut(seq_along(sort(unique(x$Year))), 5, labels = FALSE))
cv <- list()
sensitivity <- list()
for (outcome in outcomes) {
    eligible <- x[complete.cases(x[, c(outcome, "Year", "Temperature", "Precipitation",
                    "ProvinceF", paste0(measures, "_lag1")), with = FALSE]) & get(outcome) > 0]
    for (fold in seq_along(folds)) {
        train <- eligible[!Year %in% folds[[fold]]]
        test <- eligible[Year %in% folds[[fold]]]
        for (raw in c(FALSE, TRUE)) for (baseline in c(FALSE, TRUE)) {
            model <- fit_model(form(outcome, baseline, raw), train)
            predicted <- predict(model, test)
            if (!raw) predicted <- exp(predicted) * mean(exp(residuals(model)), na.rm = TRUE)
            observed <- test[[outcome]]
            cv[[length(cv) + 1L]] <- data.table(
                Outcome = outcome, ModelScale = if (raw) "RAW" else "LN",
                Model = if (baseline) "Baseline" else "Management",
                Fold = fold, n = length(observed),
                R2 = 1 - sum((observed - predicted)^2) / sum((observed - mean(observed))^2),
                RMSE = sqrt(mean((observed - predicted)^2)), MAE = mean(abs(observed - predicted)))
        }
    }
    for (lag in 0:3) {
        panel <- lag_panel(lag)
        for (raw in c(FALSE, TRUE)) {
            model <- fit_model(form(outcome, raw = raw), panel[get(outcome) > 0])
            stats <- summary(model)
            sensitivity[[length(sensitivity) + 1L]] <- data.table(
                Outcome = outcome, Lag = lag, Scale = if (raw) "Concentration" else "Log",
                n = nobs(model), AIC = AIC(model), Adjusted_R2 = stats$r.sq,
                Deviance_explained = stats$dev.expl)
        }
    }
    model <- fit_model(form(outcome), eligible)
    capture.output({gam.check(model); print(concurvity(model, full = TRUE))},
                   file = file.path(out, "tables", paste0("governance_diagnostics_", outcome, ".txt")))
}
fwrite(rbindlist(cv), file.path(out, "tables/governance_blocked_year_CV.csv"))
fwrite(rbindlist(sensitivity), file.path(out, "tables/governance_lag_sensitivity.csv"))
