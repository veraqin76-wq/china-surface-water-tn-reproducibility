#!/usr/bin/env Rscript
suppressPackageStartupMessages({library(mgcv); library(data.table)})
args <- commandArgs(trailingOnly = TRUE)
outdir <- args[2]
replicates <- as.integer(args[3])
set.seed(as.integer(args[4]))
d <- fread(args[1])
setorder(d, Province, Year)
measures <- c("Pipe", "Capacity", "EcoWater", "GreenCover", "CropArea",
              "IrrigatedArea", "NFertIntensity", "PFertIntensity")
outcomes <- c("TN", "NH3N", "COD", "TP")
target <- max(d$Year)
baseline <- d[Year == min(d$Year), c("Province", measures), with = FALSE]
for (measure in measures) {
    d[, paste0(measure, "_lag1") := fifelse(Year - shift(Year) == 1,
                                           shift(get(measure)), NA_real_), by = Province]
}
d[, ProvinceF := factor(Province)]
terms <- c("s(Year, bs='tp', k=8)", paste0("s(", measures, "_lag1, bs='tp', k=6)"),
           "s(Temperature, bs='tp', k=6)", "s(Precipitation, bs='tp', k=6)",
           "s(ProvinceF, bs='re')")
groups <- split(unique(d[, .(Province, Region)])$Province,
                unique(d[, .(Province, Region)])$Region)
by_province <- split(d, by = "Province", keep.by = TRUE)

estimate <- function(panel, outcome, raw_scale = FALSE) {
    panel <- panel[is.finite(get(outcome)) & get(outcome) > 0]
    response <- if (raw_scale) outcome else paste0("log(", outcome, ")")
    model <- gam(reformulate(terms, response), data = panel,
                 method = "GCV.Cp", select = TRUE, na.action = na.exclude)
    smear <- if (raw_scale) 1 else mean(exp(residuals(model)), na.rm = TRUE)
    latest <- panel[Year == target]
    back_transform <- function(value) if (raw_scale) value else exp(value) * smear
    observed <- back_transform(predict(model, latest, type = "response"))
    rows <- rbindlist(lapply(measures, function(measure) {
        scenario <- copy(latest)
        scenario[[paste0(measure, "_lag1")]] <- baseline[[measure]][match(scenario$Province, baseline$Province)]
        counterfactual <- back_transform(predict(model, scenario, type = "response"))
        data.table(Province = latest$Province, Region = latest$Region, Outcome = outcome,
                   Measure = measure, ModelScale = if (raw_scale) "RAW" else "LN", Observed = observed, Counterfactual = counterfactual,
                   Decrease = counterfactual - observed)
    }))
    list(model = model, rows = rows)
}

summarize <- function(rows) {
    stats <- function(x) x[is.finite(Decrease), .(n = .N, decrease = mean(Decrease),
                    change_pct = if (sum(Counterfactual) > 0)
                        -100 * sum(Decrease) / sum(Counterfactual) else NA_real_),
                    by = .(Region, Outcome, Measure, ModelScale)]
    rbind(stats(rows), stats(copy(rows)[, Region := "China"]))
}

specifications <- CJ(Outcome = outcomes, ModelScale = c("LN", "RAW"))
point <- lapply(seq_len(nrow(specifications)), function(i)
    estimate(d, specifications$Outcome[i], specifications$ModelScale[i] == "RAW"))
values <- rbindlist(lapply(point, `[[`, "rows"))
smooth_terms <- rbindlist(lapply(seq_along(point), function(i) {
    terms <- as.data.table(summary(point[[i]]$model)$s.table, keep.rownames = "Term")
    terms[, `:=`(Outcome = specifications$Outcome[i], ModelScale = specifications$ModelScale[i])]
    terms
}))
fwrite(smooth_terms, file.path(outdir, "tables", "governance_smooth_terms.csv"))
fwrite(values, file.path(outdir, "source_data", "Fig3_2024_province_counterfactuals.csv"))
point_summary <- summarize(values)
raw <- list()
for (b in seq_len(replicates)) {
    picks <- unlist(lapply(groups, function(ids) sample(ids, length(ids), replace = TRUE)))
    panel <- rbindlist(lapply(seq_along(picks), function(j) {
        copy(by_province[[picks[j]]])[, ProvinceF := as.character(j)]
    }))
    panel[, ProvinceF := factor(ProvinceF)]
    for (i in seq_len(nrow(specifications))) {
        outcome <- specifications$Outcome[i]
        boot <- tryCatch(estimate(panel, outcome, specifications$ModelScale[i] == "RAW")$rows, error = function(e) {
            message("Bootstrap ", b, " / ", outcome, ": ", conditionMessage(e))
            NULL
        })
        if (!is.null(boot)) raw[[length(raw) + 1L]] <- summarize(boot)[, Replicate := b]
    }
}
if (!length(raw)) stop("All governance bootstrap fits failed.")
if (length(raw)) {
    draws <- rbindlist(raw)
    fwrite(draws, file.path(outdir, "tables", "S13_bootstrap_draws.csv"))
    limits <- draws[, .(lo = quantile(decrease, .025), hi = quantile(decrease, .975),
                       pct_lo = quantile(change_pct, .025, na.rm = TRUE),
                       pct_hi = quantile(change_pct, .975, na.rm = TRUE),
                       successful = .N,
                       p = min(1, 2 * min((sum(decrease <= 0) + 1) / (.N + 1), (sum(decrease >= 0) + 1) / (.N + 1)))),
                    by = .(Region, Outcome, Measure, ModelScale)]
    point_summary <- merge(point_summary, limits, by = c("Region", "Outcome", "Measure", "ModelScale"), all.x = TRUE)
    point_summary[, p_BH := p.adjust(p, "BH"), by = Region]
}
fwrite(point_summary, file.path(outdir, "tables", "S13_2024_governance_effects.csv"))
fit_summary <- rbindlist(lapply(seq_along(point), function(i) {
    model <- point[[i]]$model
    stats <- summary(model)
    effective_parameters <- attr(logLik(model), "df")
    correction <- if (nobs(model) > effective_parameters + 1)
        2 * effective_parameters * (effective_parameters + 1) / (nobs(model) - effective_parameters - 1) else NA_real_
    data.table(Outcome = specifications$Outcome[i], ModelScale = specifications$ModelScale[i],
               n = nobs(model), Total_EDF = sum(model$edf), AIC = AIC(model), AICc = AIC(model) + correction,
               Adjusted_R2 = stats$r.sq, Deviance_explained = stats$dev.expl)
}))
fwrite(fit_summary, file.path(outdir, "tables", "S12_governance_GAM_fit.csv"))
