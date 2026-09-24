# Data dictionary

## Station-month input

One row is one section in one month. Chinese headings are standardized automatically.

| Standard name | Source heading | Unit/type | Required | Role |
|---|---|---|---|---|
| `StationID` | 断面编码 | text | yes | Cluster identifier |
| `StationName` | 断面名称 | text | no | Audit only |
| `StationType` | 断面类型 | text | no | Metadata |
| `WatershedUnit` | 所属流域 | text | no | Control-unit metadata |
| `Basin` | 流域 | text | yes | Ten-basin stratification |
| `River` | 所在河流 | text | no | Metadata |
| `Province` | 责任省份 | text | yes | Province aggregation |
| `City` | 责任城市 | text | no | Metadata |
| `Longitude`, `Latitude` | 经度, 纬度 | decimal degrees | maps only | ArcGIS join |
| `Year`, `Month` | 年, 月 | integer | yes | Time keys |
| `COD`, `NH3N`, `TN`, `TP`, `DO` | corresponding heading | mg L-1 | yes except optional controls | Water quality |
| `WaterTemp` | Watertem | degrees C | COD–TP GAM | Lagged control |
| `Flu` | flu | documented source unit | sensitivity | Hydrological control |

Non-positive TN/COD/TP values are invalid for log ratios. Duplicate section–month records are recorded before averaging. Annual means require the configured minimum valid months separately for each variable.

## Province-year input

| Standard name | Unit | National/region aggregation |
|---|---|---|
| `Pipe` | 10,000 km | Sum |
| `Capacity` | 10,000 m3 d-1 | Sum |
| `EcoWater` | 100 million m3 | Sum |
| `GreenCover` | % | Mean |
| `CropArea` | 1,000 ha | Sum |
| `IrrigatedArea` | 1,000 ha | Sum |
| `NFertIntensity` | t per 1,000 ha | Mean |
| `PFertIntensity` | t per 1,000 ha | Mean |
| `NH3NEmission`, `TNEmission`, `TPEmission`, `CODEmission` | 10,000 t | Descriptive/control |
| `Temperature` | degrees C | Province-year mean |
| `Precipitation` | mm | Province-year mean |
| `NDVI` | unitless | Province-year mean |

Yearbook accounting-scope changes must be documented and harmonized before concatenation.

