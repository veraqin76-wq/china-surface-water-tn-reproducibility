#!/usr/bin/env Rscript
suppressPackageStartupMessages({library(mgcv); library(data.table)})
source("r/cp_predict.R")
args<-commandArgs(trailingOnly=TRUE); input<-ifelse(length(args)>=1,args[1],"results/02_cp/model_data/cp_model_panel.csv"); out<-ifelse(length(args)>=2,args[2],"results/02_cp/tables/S5_blocked_CV.csv")
d<-fread(input); d<-d[is.finite(r_TN) & COD_lag1 > 0 & TP_lag1 > 0 & is.finite(AirTemperature) & is.finite(Precipitation)]; d[,`:=`(logCOD=log(COD_lag1),logTP=log(TP_lag1),StationID=factor(StationID),YearRE=factor(Year))]
d[,Fold:=pmin(5L,pmax(1L,ceiling(5*frank(Year,ties.method="dense")/.N))),by=StationID]
control <- c("s(AirTemperature, bs='tp', k=6)", "s(Precipitation, bs='tp', k=6)")

randoms<-c("s(StationID,bs='re')","s(YearRE,bs='re')")
rhs<-list(M0=c(control,randoms),MC=c(control,"s(logCOD,bs='tp',k=8)",randoms),MP=c(control,"s(logTP,bs='tp',k=8)",randoms),M1=c(control,"s(logCOD,bs='tp',k=8)","s(logTP,bs='tp',k=8)",randoms),M2=c(control,"s(logCOD,bs='tp',k=8)","s(logTP,bs='tp',k=8)","ti(logCOD,logTP,bs=c('tp','tp'),k=c(8,8))",randoms))
ans<-list(); k<-1
for(m in names(rhs)) for(f in 1:5){tr<-d[Fold!=f]; te<-d[Fold==f]; fit<-gam(as.formula(paste("r_TN~",paste(rhs[[m]],collapse="+"))),data=tr,method="REML",select=TRUE); pr<-predict_cp(fit,te); ok<-is.finite(pr); y<-te$r_TN[ok]; pr<-pr[ok]; ans[[k]]<-data.table(Model=m,Fold=f,n=length(y),R2=1-sum((y-pr)^2)/sum((y-mean(y))^2),RMSE=sqrt(mean((y-pr)^2)),MAE=mean(abs(y-pr))); k<-k+1 }
fwrite(rbindlist(ans),out); cat("Blocked CV complete\n")

