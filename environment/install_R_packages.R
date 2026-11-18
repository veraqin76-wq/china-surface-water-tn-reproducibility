repos <- "https://cloud.r-project.org"
needed <- c("mgcv", "data.table", "jsonlite")
missing <- needed[!vapply(needed, requireNamespace, logical(1), quietly=TRUE)]
if(length(missing)) install.packages(missing, repos=repos)
writeLines(capture.output(sessionInfo()), "environment/R_sessionInfo.txt")

