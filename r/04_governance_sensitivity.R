#!/usr/bin/env Rscript
suppressPackageStartupMessages({library(mgcv); library(data.table)})
args <- commandArgs(trailingOnly = TRUE)
d <- fread(args[1])
out <- args[2]
annual <- fread(args[3])
setorder(d, Province, Year)
measures <- c("Pipe", "Capacity", "EcoWater", "GreenCover", "CropArea",
              "IrrigatedArea", "NFertIntensity", "PFertIntensity")
baseline <- d[Year == min(d$Year), c("Province", measures), with = FALSE]
for (v in measures) {
    d[, paste0(v, "_lag1") := fifelse(Year - shift(Year) == 1, shift(get(v)), NA_real_), by = Province]
}
d[, ProvinceF := factor(Province)]
target <- max(d$Year)
terms <- c("s(Year,bs='tp',k=8)", paste0("s(", measures, "_lag1,bs='tp',k=6)"),
           "s(Temperature,bs='tp',k=6)", "s(Precipitation,bs='tp',k=6)", "s(ProvinceF,bs='re')")
effects <- function(model, panel) {
    latest <- panel[Year == target]
    smear <- mean(exp(residuals(model)), na.rm = TRUE)
    observed <- exp(predict(model, latest)) * smear
    rbindlist(lapply(measures, function(measure) {
        scenario <- copy(latest)
        scenario[[paste0(measure, "_lag1")]] <- baseline[[measure]][match(scenario$Province, baseline$Province)]
        cf <- exp(predict(model, scenario)) * smear
        data.table(Measure = measure, Decrease = mean(cf - observed, na.rm = TRUE))
    }))
}
influence <- list()
hydrology <- list()
for (outcome in c("TN", "NH3N", "COD", "TP")) {
    required <- c(outcome, "Year", "Temperature", "Precipitation", "ProvinceF", paste0(measures, "_lag1"))
    panel <- d[complete.cases(d[, ..required]) & get(outcome) > 0]
    formula <- reformulate(terms, paste0("log(", outcome, ")"))
    full <- gam(formula, data = panel, method = "GCV.Cp", select = TRUE)
    ids <- sort(unique(panel$Province))
    if (Sys.getenv("NS_MODE") == "demo") ids <- ids[seq_len(min(2L, length(ids)))]
    for (id in ids) {
        subset <- panel[Province != id]
        fit <- gam(formula, data = subset, method = "GCV.Cp", select = TRUE)
        ref <- effects(full, subset)
        omitted <- effects(fit, subset)
        comparison <- merge(ref, omitted, by = "Measure", suffixes = c("_full", "_omitted"))
        comparison[, `:=`(Outcome = outcome, OmittedProvince = id,
                           Difference = Decrease_omitted - Decrease_full)]
        influence[[length(influence) + 1L]] <- comparison
    }
    if ("Flu" %in% names(annual)) {
        flow <- annual[is.finite(Flu) & Flu > 0, .(Flow = mean(Flu)), by = .(Province, Year)]
        joined <- merge(panel, flow, by = c("Province", "Year"))
        joined <- joined[is.finite(Flow) & Flow > 0]
        if (nrow(joined) > 100L && uniqueN(joined$Flow) > 6L) {
            for (include_flow in c(FALSE, TRUE)) {
                model_terms <- c(terms, if (include_flow) "s(log(Flow),bs='tp',k=6)")
                fit <- gam(reformulate(model_terms, paste0("log(", outcome, ")")),
                           data = joined, method = "GCV.Cp", select = TRUE)
                result <- effects(fit, joined)
                result[, `:=`(Outcome = outcome, FlowAdjusted = include_flow,
                               n = nobs(fit), AIC = AIC(fit))]
                hydrology[[length(hydrology) + 1L]] <- result
            }
        }
    }
}
fwrite(rbindlist(influence), file.path(out, "tables/governance_province_influence.csv"))
if (length(hydrology)) {
    fwrite(rbindlist(hydrology), file.path(out, "tables/governance_hydrological_sensitivity.csv"))
}
