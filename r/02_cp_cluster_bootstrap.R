#!/usr/bin/env Rscript
suppressPackageStartupMessages({library(mgcv);library(data.table)})
args<-commandArgs(trailingOnly=TRUE);input<-args[1];outdir<-args[2];B<-as.integer(args[3]);seed<-as.integer(args[4]);set.seed(seed)
d<-fread(input);d<-d[is.finite(r_TN) & COD_lag1 > 0 & TP_lag1 > 0 & is.finite(AirTemperature) & is.finite(Precipitation)];d[,`:=`(logCOD=log(COD_lag1),logTP=log(TP_lag1),StationID=factor(StationID),YearRE=factor(Year))]
controls <- c("s(AirTemperature, bs='tp', k=6)", "s(Precipitation, bs='tp', k=6)")
form<-as.formula(paste("r_TN~",paste(c(controls,"s(logCOD,bs='tp',k=8)","s(logTP,bs='tp',k=8)","ti(logCOD,logTP,bs=c('tp','tp'),k=c(8,8))","s(StationID,bs='re')","s(YearRE,bs='re')"),collapse="+")))
qc<-quantile(d$COD_lag1,c(.2,.8));qp<-quantile(d$TP_lag1,c(.2,.8));states<-data.table(State=c("LL","LH","HL","HH"),COD=c(qc[1],qc[1],qc[2],qc[2]),TP=c(qp[1],qp[2],qp[1],qp[2]));ids<-unique(as.character(d$StationID));ans<-list()
for(b in 1:B){pick<-sample(ids,length(ids),replace=TRUE);x<-rbindlist(lapply(seq_along(pick),function(j){q<-copy(d[as.character(StationID)==pick[j]]);q[,StationID:=factor(paste0("B",j))];q}));fit<-try(gam(form,data=x,method="REML",select=TRUE),silent=TRUE);if(inherits(fit,"try-error"))next;ans[[b]]<-rbindlist(lapply(1:4,function(j){nd<-copy(x);nd[,`:=`(logCOD=log(states$COD[j]),logTP=log(states$TP[j]))];p<-predict(fit,newdata=nd,exclude=c("s(StationID)","s(YearRE)"));data.table(bootstrap=b,State=states$State[j],TN_change_pct=100*expm1(mean(p,na.rm=TRUE)))}))}
if (!length(ans)) stop("All CP bootstrap fits failed.")
raw<-rbindlist(ans);fwrite(raw,file.path(outdir,"tables/S5_cluster_bootstrap_raw.csv"));ci<-raw[,.(estimate=median(TN_change_pct),lo=quantile(TN_change_pct,.025),hi=quantile(TN_change_pct,.975),successful=.N),by=State];fwrite(ci,file.path(outdir,"tables/S5_cluster_bootstrap_CI.csv"));cat("CP cluster bootstrap complete\n")


source("r/cp_support.R")
support <- joint_support(d$COD_lag1, d$TP_lag1, states$COD, states$TP)
ci[, supported := support$supported[match(State, states$State)]]
ci[supported == FALSE, `:=`(estimate = NA_real_, lo = NA_real_, hi = NA_real_)]
fwrite(ci, file.path(outdir, "tables/S5_cluster_bootstrap_CI.csv"))
