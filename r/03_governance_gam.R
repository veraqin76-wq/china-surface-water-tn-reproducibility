#!/usr/bin/env Rscript
suppressPackageStartupMessages({library(mgcv);library(data.table)})
args<-commandArgs(trailingOnly=TRUE); input<-ifelse(length(args)>=1,args[1],"results/03_governance/model_data/province_year_panel.csv"); outdir<-ifelse(length(args)>=2,args[2],"results/03_governance")
dir.create(file.path(outdir,"tables"),recursive=TRUE,showWarnings=FALSE);dir.create(file.path(outdir,"source_data"),recursive=TRUE,showWarnings=FALSE);dir.create(file.path(outdir,"models"),recursive=TRUE,showWarnings=FALSE)
d<-fread(input); setorder(d,Province,Year); measures<-c("Pipe","Capacity","EcoWater","GreenCover","CropArea","IrrigatedArea","NFertIntensity","PFertIntensity")
for(v in measures) d[,paste0(v,"_lag1"):=fifelse(Year-shift(Year)==1,shift(get(v)),NA_real_),by=Province]
d[,ProvinceF:=factor(Province)]; outcomes<-c("TN","NH3N","COD","TP"); ans<-list()
for(y in outcomes){dd<-d[is.finite(get(y))]; terms<-c("s(Year,bs='tp',k=8)",paste0("s(",measures,"_lag1,bs='tp',k=6)"),"s(Temperature,bs='tp',k=6)","s(Precipitation,bs='tp',k=6)","s(ProvinceF,bs='re')"); f<-as.formula(paste0("log(",y,")~",paste(terms,collapse="+"))); fit<-gam(f,data=dd,method="GCV.Cp",select=TRUE,na.action=na.exclude); saveRDS(fit,file.path(outdir,"models",paste0("governance_",y,".rds"))); smearing<-mean(exp(residuals(fit)),na.rm=TRUE); base<-summary(fit); ans[[y]]<-data.table(Outcome=y,AIC=AIC(fit),Adjusted_R2=base$r.sq,Deviance_explained=base$dev.expl,Duan_smearing=smearing)
 # Province-specific 2006 counterfactual, one measure at a time.
 observed<-predict(fit,newdata=dd,type="response"); for(v in measures){nd<-copy(dd); vv<-paste0(v,"_lag1"); b<-d[Year==min(d$Year),.(Province, baseline=get(v))]; nd[[vv]]<-b$baseline[match(nd$Province,b$Province)]; cf<-predict(fit,newdata=nd,type="response"); fwrite(data.table(Outcome=y,Measure=v,Province=nd$Province,Year=nd$Year,Observed=exp(observed)*smearing,Counterfactual=exp(cf)*smearing,Difference=exp(observed)*smearing-exp(cf)*smearing),file.path(outdir,"source_data",paste0("governance_counterfactual_",y,"_",v,".csv")))}}
fwrite(rbindlist(ans),file.path(outdir,"tables/governance_GAM_fit.csv"));cat("Governance GAM complete\n")
