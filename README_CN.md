# 中国地表水化学计量结构重组与总氮动态

本仓库包含数据清洗、化学计量比值、污染物趋势、经验COD–TP四状态、张量积GAM和治理分析。演示模式使用合成输入，稿件模式读取本地授权研究数据。

## 运行

```bash
pip install -r requirements.txt
Rscript environment/install_R_packages.R
python run_all.py --mode demo
python validation/validate_outputs.py --mode demo
```

复制config.manuscript.example.yml为config.manuscript.yml，配置本地路径后运行：

```bash
python run_all.py --mode manuscript --config config.manuscript.yml
python validation/validate_outputs.py --mode manuscript --config config.manuscript.yml
```

FIGURE_TABLE_CODE_MAP.md给出逐图、逐表对应的脚本、输出文件和统计方法。

稿件配置使用1000次经验断面聚类重采样、200次COD–TP模型重采样、500次按区域分层的省份聚类重采样。演示配置采用较少次数。

COD–TP模型采用当年气温和降水，以及上一年COD和TP。

Fig.S20的研究适用水质分类限值从water_quality_thresholds读取。Fig.S27投资数据通过paths.investment读取。空间图通过导出的CSV连接研究采用的地理边界绘制。
