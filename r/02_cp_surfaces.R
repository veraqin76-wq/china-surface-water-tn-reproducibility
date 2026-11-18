#!/usr/bin/env Rscript
suppressPackageStartupMessages(library(data.table))
suppressPackageStartupMessages(library(mgcv))
source("r/cp_support.R")
args <- commandArgs(trailingOnly = TRUE)
d <- fread(args[1])
out <- args[2]
d <- d[is.finite(r_TN) & COD_lag1 > 0 & TP_lag1 > 0 &
       is.finite(AirTemperature) & is.finite(Precipitation)]
national <- readRDS(file.path(out, "models", "cp_M0_M2.rds"))$M2

surface <- function(fit, observations, scope, area) {
    cod <- seq(quantile(observations$COD_lag1, .01), quantile(observations$COD_lag1, .99), length.out = 100L)
    tp <- seq(quantile(observations$TP_lag1, .01), quantile(observations$TP_lag1, .99), length.out = 100L)
    grid <- CJ(COD = cod, TP = tp)
    grid[, `:=`(Scope = scope, Area = area, logCOD = log(COD), logTP = log(TP),
                StationID = levels(fit$model$StationID)[1L], YearRE = levels(fit$model$YearRE)[1L],
                AirTemperature = median(observations$AirTemperature),
                Precipitation = median(observations$Precipitation))]
    prediction <- predict(fit, grid, type = "response", se.fit = TRUE,
                          exclude = c("s(StationID)", "s(YearRE)"))
    grid[, `:=`(fit = as.numeric(prediction$fit), se = as.numeric(prediction$se.fit))]
    grid[, `:=`(TN_change_pct = 100 * expm1(fit),
                lo = 100 * expm1(fit - 1.96 * se),
                hi = 100 * expm1(fit + 1.96 * se))]
    support <- joint_support(observations$COD_lag1, observations$TP_lag1, grid$COD, grid$TP)
    grid[, `:=`(joint_density = support$density, support_threshold = support$threshold,
                supported = support$supported)]
    masked <- grid$fit
    masked[!grid$supported] <- NA_real_
    lines <- contourLines(cod, tp, matrix(masked, nrow = length(cod), byrow = TRUE), levels = 0)
    contour <- data.table(Scope = character(), Area = character(), Segment = integer(),
                          Point = integer(), COD = numeric(), TP = numeric())
    for (i in seq_along(lines)) {
        contour <- rbind(contour, data.table(Scope = scope, Area = area, Segment = i,
                         Point = seq_along(lines[[i]]$x), COD = lines[[i]]$x, TP = lines[[i]]$y))
    }
    transition <- data.table(Scope = scope, Area = area, segments = length(lines),
                             COD_cut = if (nrow(contour)) min(contour$COD) else NA_real_,
                             TP_cut = if (nrow(contour)) min(contour$TP) else NA_real_)
    list(grid = grid, contour = contour, transition = transition)
}

results <- list(surface(national, d, "National", "China"))
for (basin in sort(unique(d$Basin))) {
    path <- file.path(out, "models", paste0("M2_basin_", basin, ".rds"))
    if (file.exists(path)) {
        results[[length(results) + 1L]] <- surface(readRDS(path), d[Basin == basin], "Basin", basin)
    }
}
fwrite(rbindlist(lapply(results, `[[`, "grid")), file.path(out, "source_data", "Fig2_S24_CP_surfaces.csv"))
fwrite(rbindlist(lapply(results, `[[`, "contour")), file.path(out, "source_data", "S10_zero_contour_coordinates.csv"))
fwrite(rbindlist(lapply(results, `[[`, "transition")), file.path(out, "tables", "S10_transition_positions.csv"))
