# Product Gaussian KDE in standardized log-COD/log-TP coordinates.
joint_support <- function(observed_cod, observed_tp, target_cod, target_tp) {
    observed <- scale(cbind(log(observed_cod), log(observed_tp)))
    center <- attr(observed, "scaled:center")
    spread <- attr(observed, "scaled:scale")
    target <- sweep(sweep(cbind(log(target_cod), log(target_tp)), 2, center), 2, spread, "/")
    bandwidth <- apply(observed, 2, bw.nrd0)
    if (any(!is.finite(bandwidth)) || any(bandwidth <= 0)) {
        stop("Joint support requires variation in both log COD and log TP.")
    }
    density <- function(points) {
        vapply(seq_len(nrow(points)), function(i) {
            mean(dnorm((points[i, 1] - observed[, 1]) / bandwidth[1]) *
                 dnorm((points[i, 2] - observed[, 2]) / bandwidth[2])) / prod(bandwidth)
        }, numeric(1))
    }
    threshold <- unname(quantile(density(observed), .05))
    value <- density(target)
    list(density = value, threshold = threshold, supported = value >= threshold)
}
