# Preserve fitted group effects for known levels and use zero effects for new levels.
predict_cp <- function(fit, newdata) {
    data <- copy(newdata)
    unknown_station <- !as.character(data$StationID) %in% levels(fit$model$StationID)
    unknown_year <- !as.character(data$YearRE) %in% levels(fit$model$YearRE)
    data[unknown_station, StationID := levels(fit$model$StationID)[1L]]
    data[unknown_year, YearRE := levels(fit$model$YearRE)[1L]]
    result <- rep(NA_real_, nrow(data))
    for (station in c(FALSE, TRUE)) for (year in c(FALSE, TRUE)) {
        selected <- which(unknown_station == station & unknown_year == year)
        if (!length(selected)) next
        excluded <- c(if (station) "s(StationID)", if (year) "s(YearRE)")
        result[selected] <- predict(fit, data[selected], type = "response", exclude = excluded)
    }
    result
}
