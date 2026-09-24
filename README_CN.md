# 中国地表水 TN 研究：Methods/SI 复现代码

## 最终版本状态

本版本为面向GitHub与期刊审稿的1.0.1版。随包合成数据上的Python流程和R/`mgcv`独立演示流程均已确认能够完成运行并生成预期输出。该确认说明代码工作流可执行，不表示合成数据复现了论文中的样本量、阈值、效应值或流域差异。

本仓库按论文当前 Methods 与 Supplementary Methods S1–S6 组织，而不是按图号组织。

## 软件分工

- Python：字段标准化、数据质控、月度至年度聚合、R1/R2/R3、平衡断面与等权敏感性、对数分解、Mann–Kendall/Sen、同断面配对改善、经验四状态、二维分箱、聚类 bootstrap、治理变量趋势检验、Source Data 与 ArcGIS 连接表。
- R (`mgcv`)：正文 COD–TP tensor-product GAM、M0–M2、REML、随机效应、诊断、响应面；省级治理措施 GAM、反事实与 Duan smearing。
- Origin：只读取 `results/source_data` 进行正式排版，不参与统计估计。
- ArcGIS 10.5：只读取 `results/arcgis_join_tables` 进行空间连接和制图。

## 输入文件

默认文件见 `config.yml`。原始中文表头会自动映射为英文标准字段。正式分析不要求修改源 Excel。

站点月度表至少需要：`StationID, StationName, Basin, Province, Longitude, Latitude, Year, Month, COD, NH3N, TN, TP, DO, WaterTemp, Flu`。

治理表至少需要：`Year, Province, Region, Pipe, Capacity, EcoWater, GreenCover, NH3NEmission, TNEmission, TPEmission, CODEmission, CropArea, NFertIntensity, PFertIntensity, IrrigatedArea`。

治理 GAM 还需要省—年气温、降水以及拟纳入的其他控制变量。它们可放在单独的 `province_covariates.csv`，以 `Province + Year` 合并。

## 快速测试

```bash
python 00_generate_synthetic_data.py
python run_all.py --skip-r
```

最新统一入口建议使用：

```bash
python run_all.py --mode demo
python validation/validate_outputs.py --mode demo
```

完整运行需要 R 及 `mgcv`, `data.table`, `jsonlite`：

```bash
python run_all.py
```

## 重要方法口径

1. TN 年变化定义为 `log(TN_t / TN_t-1)`，负值表示下降；改善率另定义为 `log(TN_t-1 / TN_t)`，正值表示改善。
2. 只有同一断面连续两年均有效且相关浓度为正时才构造年度变化。
3. S4 的四状态采用长期中位数；S5 的模型预测状态采用第20/80百分位，两者不混用。
4. 正文 GAM 以薄板样条、`ti()`交互、站点/年份随机效应及 REML 为准。S5 的 M0–M2 已统一到同一建模框架。
5. 3σ筛查和线性插值均输出审计记录。默认只在同一断面、同一指标内插补单个月缺口，不跨年连续插补；可在配置中关闭。
6. 合成数据仅用于测试代码，不能复现论文数值或作为论文 Source Data。

## 尚需真实数据才能完成的部分

- 真实的省—年气温、降水、NDVI及投资变量；
- GAM转换位置敏感性分析所需的真实模型零等值线结果；
- 论文正式图与表的最终编号映射；
- ArcGIS工程中的边界来源、坐标系、分类断点和版式参数。

正式投稿前还应以真实受限数据运行`manuscript`模式，将最终图表数值放入`source_data/`，并保存完整运行日志、R session information和输出校验清单。
