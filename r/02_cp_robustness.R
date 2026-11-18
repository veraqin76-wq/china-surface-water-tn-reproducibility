#!/usr/bin/env Rscript
suppressPackageStartupMessages({library(mgcv);library(data.table);library(MASS)})
source("r/cp_predict.R")
args<-commandArgs(trailingOnly=TRUE); input<-args[1]; outdir<-args[2]; d<-fread(input)
d<-d[is.finite(r_TN) & COD_lag1 > 0 & TP_lag1 > 0 & is.finite(AirTemperature) & is.finite(Precipitation)];d[,`:=`(logCOD=log(COD_lag1),logTP=log(TP_lag1),StationID=factor(StationID),YearRE=factor(Year))]
controls <- c("s(AirTemperature, bs='tp', k=6)", "s(Precipitation, bs='tp', k=6)")

rhs<-paste(c(controls,"s(logCOD,bs='tp',k=8)","s(logTP,bs='tp',k=8)","ti(logCOD,logTP,bs=c('tp','tp'),k=c(8,8))","s(StationID,bs='re')","s(YearRE,bs='re')"),collapse="+"); form<-as.formula(paste("r_TN~",rhs))
# Station holdout, with population-average predictions excluding unseen station effects.
set.seed(as.integer(Sys.getenv("NS_SEED", "20260924"))); ids<-sample(unique(d$StationID)); folds<-setNames(rep(1:5,length.out=length(ids)),ids);ans<-list()
for(f in 1:5){teids<-names(folds)[folds==f];tr<-d[!StationID%in%teids];te<-d[StationID%in%teids];fit<-gam(form,data=tr,method="REML",select=TRUE);p<-predict_cp(fit,te);ok<-is.finite(p);y<-te$r_TN[ok];p<-p[ok];ans[[f]]<-data.table(Scheme="station_holdout",Fold=f,n=length(y),R2=1-sum((y-p)^2)/sum((y-mean(y))^2),RMSE=sqrt(mean((y-p)^2)),MAE=mean(abs(y-p)))}
# Rolling temporal extrapolation.
for(ycut in 2019:2023){tr<-d[Year<=ycut];te<-d[Year==ycut+1];if(nrow(te)<10)next;fit<-gam(form,data=tr,method="REML",select=TRUE);p<-predict_cp(fit,te);ok<-is.finite(p);y<-te$r_TN[ok];p<-p[ok];ans[[length(ans)+1]]<-data.table(Scheme="rolling_time",Fold=ycut+1,n=length(y),R2=1-sum((y-p)^2)/sum((y-mean(y))^2),RMSE=sqrt(mean((y-p)^2)),MAE=mean(abs(y-p)))}
fwrite(rbindlist(ans),file.path(outdir,"tables/S5_holdout_and_rolling_CV.csv"))
# Basin-specific fits and diagnostics.
btab<-list();for(b in unique(d$Basin)){x<-d[Basin==b];if(nrow(x)<100)next;fit<-try(gam(form,data=x,method="REML",select=TRUE),silent=TRUE);if(inherits(fit,"try-error"))next;s<-summary(fit);saveRDS(fit,file.path(outdir,"models",paste0("M2_basin_",b,".rds")));btab[[b]]<-data.table(Basin=b,n=nrow(x),AIC=AIC(fit),Adjusted_R2=s$r.sq,Deviance_explained=s$dev.expl,EDF=sum(fit$edf))};fwrite(rbindlist(btab),file.path(outdir,"tables/S5_basin_model_fit.csv"))
cat("CP robustness complete\n")

