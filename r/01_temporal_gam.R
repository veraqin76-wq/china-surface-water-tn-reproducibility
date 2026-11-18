#!/usr/bin/env Rscript
suppressPackageStartupMessages({library(mgcv); library(data.table)})
set.seed(as.integer(Sys.getenv("NS_SEED", "20260924")))
args <- commandArgs(trailingOnly = TRUE)
out <- file.path(args[1], "source_data")
national <- fread(file.path(out, "national_annual_means.csv"))
national[, Basin := "China"]
national[, Scope := "National"]
basin <- fread(file.path(out, "basin_annual_means.csv"))
basin[, Scope := "Basin"]
series <- melt(rbindlist(list(national, basin), use.names = TRUE),
               id.vars = c("Scope", "Basin", "Year"), variable.name = "Pollutant",
               value.name = "Concentration")
series <- series[is.finite(Concentration) & Concentration > 0]
derivatives <- series[, {
    if (.N >= 5L) {
        basis_size <- min(8L, .N - 1L)
        fit <- gam(log(Concentration) ~ s(Year, bs = "tp", k = basis_size), data = .SD, method = "REML")
        year <- seq(min(Year), max(Year))
        step <- 0.01
        plus <- predict(fit, data.frame(Year = year + step), type = "lpmatrix")
        minus <- predict(fit, data.frame(Year = year - step), type = "lpmatrix")
        design <- (plus - minus) / (2 * step)
        derivative <- drop(design %*% coef(fit))
        se <- sqrt(pmax(0, rowSums((design %*% vcov(fit, unconditional = TRUE)) * design)))
        data.table(Year = year, first_derivative = derivative, derivative_se = se,
                   annual_change_pct = 100 * expm1(derivative),
                   lo = 100 * expm1(derivative - 1.96 * se),
                   hi = 100 * expm1(derivative + 1.96 * se))
    }
}, by = .(Scope, Area = Basin, Pollutant)]
fwrite(derivatives, file.path(out, "S3_temporal_GAM_derivatives.csv"))
