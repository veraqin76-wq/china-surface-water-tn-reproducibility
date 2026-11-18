#!/usr/bin/env Rscript
suppressPackageStartupMessages({library(mgcv); library(data.table)})
source("r/cp_support.R")
set.seed(as.integer(Sys.getenv("NS_SEED", "20260924")))
args <- commandArgs(trailingOnly=TRUE)
input <- ifelse(length(args)>=1,args[1],"results/02_cp/model_data/cp_model_panel.csv")
outdir <- ifelse(length(args)>=2,args[2],"results/02_cp")
dir.create(file.path(outdir,"tables"),recursive=TRUE,showWarnings=FALSE)
dir.create(file.path(outdir,"source_data"),recursive=TRUE,showWarnings=FALSE)
dir.create(file.path(outdir,"models"),recursive=TRUE,showWarnings=FALSE)
d <- fread(input)
d <- d[is.finite(r_TN) & COD_lag1 > 0 & TP_lag1 > 0 & is.finite(AirTemperature) & is.finite(Precipitation)]
d[,`:=`(logCOD=log(COD_lag1),logTP=log(TP_lag1),StationID=factor(StationID),YearRE=factor(Year))]
controls <- c("s(AirTemperature, bs='tp', k=6)", "s(Precipitation, bs='tp', k=6)")

randoms <- c("s(StationID,bs='re')","s(YearRE,bs='re')")
rhs <- list(
 M0=c(controls,randoms),
 MC=c(controls,"s(logCOD,bs='tp',k=8)",randoms),
 MP=c(controls,"s(logTP,bs='tp',k=8)",randoms),
 M1=c(controls,"s(logCOD,bs='tp',k=8)","s(logTP,bs='tp',k=8)",randoms),
 M2=c(controls,"s(logCOD,bs='tp',k=8)","s(logTP,bs='tp',k=8)","ti(logCOD,logTP,bs=c('tp','tp'),k=c(8,8))",randoms))
fits <- lapply(rhs,function(x) gam(as.formula(paste("r_TN~",paste(x,collapse="+"))),data=d,family=gaussian(),method="REML",select=TRUE))
saveRDS(fits,file.path(outdir,"models/cp_M0_M2.rds"))
tab <- rbindlist(lapply(names(fits),function(n){s<-summary(fits[[n]]); data.table(Model=n,AIC=AIC(fits[[n]]),Adjusted_R2=s$r.sq,Deviance_explained=s$dev.expl,REML_score=fits[[n]]$gcv.ubre,EDF=sum(fits[[n]]$edf))}))
fwrite(tab,file.path(outdir,"tables/S5_model_fit.csv"))
m2_summary <- summary(fits$M2)
smooths <- as.data.table(m2_summary$s.table, keep.rownames = "Term")
fwrite(smooths, file.path(outdir, "tables/S6_national_M2_smooth_terms.csv"))
fwrite(data.table(n = nobs(fits$M2), AIC = AIC(fits$M2),
                  adjusted_R2 = m2_summary$r.sq, deviance_explained = m2_summary$dev.expl),
       file.path(outdir, "tables/S6_national_M2_summary.csv"))
diag <- capture.output({cat("=== gam.check M2 ===\n"); gam.check(fits$M2); cat("=== concurvity M2 ===\n"); print(concurvity(fits$M2,full=TRUE))})
writeLines(diag,file.path(outdir,"tables/S5_M2_diagnostics.txt"))

# Population-average surface: random effects excluded and covariates held at medians.
qcod <- quantile(d$COD_lag1,c(.01,.99),na.rm=TRUE); qtp <- quantile(d$TP_lag1,c(.01,.99),na.rm=TRUE)
grid <- CJ(COD=seq(qcod[1],qcod[2],length.out=100),TP=seq(qtp[1],qtp[2],length.out=100))
grid[,`:=`(logCOD=log(COD),logTP=log(TP),StationID=d$StationID[1],YearRE=d$YearRE[1])]
grid[, `:=`(AirTemperature = median(d$AirTemperature),
             Precipitation = median(d$Precipitation))]
pr <- predict(fits$M2,newdata=grid,type="link",se.fit=TRUE,exclude=c("s(StationID)","s(YearRE)"))
grid[,`:=`(fit=as.numeric(pr$fit),se=as.numeric(pr$se.fit),TN_change_pct=100*expm1(as.numeric(pr$fit)),lo=100*expm1(pr$fit-1.96*pr$se.fit),hi=100*expm1(pr$fit+1.96*pr$se.fit))]
fwrite(grid,file.path(outdir,"source_data/Fig2_national_CP_surface.csv"))

# Model-based four states at 20th/80th percentiles, marginal standardized over observed rows.
qc <- quantile(d$COD_lag1,c(.2,.8),na.rm=TRUE); qp <- quantile(d$TP_lag1,c(.2,.8),na.rm=TRUE)
states <- data.table(State=c("LL","LH","HL","HH"),COD=c(qc[1],qc[1],qc[2],qc[2]),TP=c(qp[1],qp[2],qp[1],qp[2]))
st <- rbindlist(lapply(1:nrow(states),function(j){nd<-copy(d); nd[,`:=`(logCOD=log(states$COD[j]),logTP=log(states$TP[j]))]; p<-predict(fits$M2,newdata=nd,type="response",exclude=c("s(StationID)","s(YearRE)")); data.table(State=states$State[j],COD=states$COD[j],TP=states$TP[j],mean_r=mean(p),TN_change_pct=100*expm1(mean(p))) }))
support <- joint_support(d$COD_lag1, d$TP_lag1, st$COD, st$TP)
st[, supported := support$supported]
st[supported == FALSE, `:=`(mean_r = NA_real_, TN_change_pct = NA_real_)]
fwrite(st,file.path(outdir,"tables/S5_four_state_predictions.csv"))
cat("CP GAM complete\n")

