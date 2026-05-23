[English](README.en.md) | **中文**

# u1-solar-modeling

U(1) 对称性在太阳观测数据建模中的应用框架 + **空间天气预测管线**。

## 核心洞见

太阳的自转、磁场、日冕环振荡、活动周期、日震模式，都有一个共同点：**转一圈回来，样子不变**——这就是 U(1) 对称性。

本项目用 U(1) 相位拟合 12 类太阳模块：
- **5 个应用**：太阳自转、活动周期、日冕环振荡、矢量磁场、日震学
- **3 个预测**：Hilbert 相位跟踪、自转相位日历、剪切耀斑指数
- **2 个空间天气模型**：Dst 地磁暴预报、CME 传播（DBM）
- **1 个综合验证**：Flare_Idx（HMI SHARP 真实磁图）
- **1 个核心模型**：U(1) 时间耀斑模型（Plutino 334,123 事件验证）

## 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 运行端到端演示

```bash
python demo_all.py
```

将依次运行全部 12 模块并输出测试摘要。

### 测试

```bash
python -m pytest tests/ -v    # 82 个测试
```

---

## 全部模块

### 5 个 U(1) 应用

| # | 应用 | U(1) 变量 | 数据来源 | 文件 |
|---|------|-----------|----------|------|
| 1 | **太阳自转**（较差自转剖面 Ω(θ)） | 纬度 θ | SDO HMI | `code/solar_rotation.py` |
| 2 | **太阳活动周期**（11 年黑子周期） | 时间 t | SILSO | `code/solar_cycle.py` |
| 3 | **日冕环振荡**（横向振荡 → 磁场） | 时间 t | AIA 193 Å | `code/coronal_loop_oscillation.py` |
| 4 | **矢量磁场方向**（极坐标直方图） | 方位角 φ | SDO HMI | `code/vector_magnetic_field.py` |
| 5 | **日震学模式**（球谐方位角对称） | 方位角 φ | GONG/HMI | `code/helioseismology.py` |

### 3 个预测模块

| # | 模块 | 功能 | 文件 |
|---|------|------|------|
| 6 | **Hilbert 相位跟踪** | 从黑子数据提取瞬时相位 φ(t)，外推极小/极大年 | `code/prediction/hilbert_phase.py` |
| 7 | **自转相位日历** | 黑子/事件到 Carrington 经度映射，识别活动经度 | `code/prediction/rotation_phase_map.py` |
| 8 | **剪切耀斑指数** | 从 U(1) 圆方差 × 剪切角估算耀斑潜力 | `code/prediction/shear_flare_index.py` |

### 2 个空间天气模型

| # | 模块 | 功能 | 文件 |
|---|------|------|------|
| 9 | **Dst 地磁暴预报** | Burton 方程，对接 NOAA SWPC 实时太阳风数据 | `code/prediction/dst_model.py` |
| 10 | **CME 传播** | 解析 DBM + Gopalswamy 校正，对接 DONKI 实时 CME 目录 | `code/prediction/cme_model.py` |

### 1 个综合验证 + 1 个核心模型

| # | 模块 | 功能 | 文件 |
|---|------|------|------|
| 11 | **Flare_Idx 验证** | HMI SHARP CEA 矢量磁图 → 极性分离剪切角 × 圆方差 | `code/flare_idx.py` |
| 12 | **U(1) 时间耀斑模型** | 基于 Plutino 334,123 事件的 von Mises 拟合 | `code/u1_solar_model.py` |

### 数据管道

- **NOAA SWPC**：实时太阳风（Dst, 速度, 密度, Bz）
- **DONKI**：实时 CME 目录（速度, 角度, 来源）
- **Plutino 耀斑目录**：207,814 事件（1986-2020），Cycle 22-24 全覆盖
- **SILSO 黑子数**：3297+ 行月度数据（1750-2024）
- **HMI SHARP CEA**：AR 11092 矢量磁图（FITS 格式）

---

## 核心模型

**U(1) 时间耀斑模型**（`code/u1_solar_model.py`）

验证结果：
- 数据：334,123 事件（Plutino FlareList 1986-2020）
- Rayleigh Z = 3496（p ≈ 0），R² = 0.689
- 峰谷比 12.4×，相位偏移 **Φ_lag = 142.9°**（~3.2 年）
- 下一峰值预测：**2034.6 年**
- 详细文档：`docs/U1_SOLAR_MODEL.md`

---

## 项目结构

```
u1-solar-modeling/
├── README.md
├── SKILL.md
├── requirements.txt
├── demo_all.py              # 端到端演示（12 模块）
├── dimensions/              # 5 个应用的理论基础
│   ├── 01_solar_rotation.md
│   ├── 02_solar_cycle.md
│   ├── 03_coronal_loop.md
│   ├── 04_vector_magnetic_field.md
│   └── 05_helioseismology.md
├── code/                    # 5 应用 + 核心模型
│   ├── solar_rotation.py
│   ├── solar_cycle.py
│   ├── coronal_loop_oscillation.py
│   ├── vector_magnetic_field.py
│   ├── helioseismology.py
│   ├── flare_idx.py
│   ├── u1_solar_model.py
│   └── prediction/          # 预测 + 空间天气
│       ├── hilbert_phase.py
│       ├── rotation_phase_map.py
│       ├── shear_flare_index.py
│       ├── dst_model.py
│       ├── cme_model.py
│       ├── noaa_pipeline_v2.py
│       └── __init__.py
├── data/                    # 观测数据（真实 + 模拟）
│   ├── sunspot_number.csv
│   ├── hmi/                 # HMI SHARP FITS
│   ├── real/                # NOAA/DONKI/Plutino 实时数据
│   └── ...
├── docs/
│   ├── U1_SOLAR_MODEL.md    # 模型文档
│   └── storm_clock.html     # 风暴时钟可视化
└── tests/                   # 82 个单元测试
    ├── test_solar_rotation.py
    ├── test_solar_cycle.py
    ├── test_coronal_loop.py
    ├── test_flare_idx.py
    ├── test_helioseismology.py
    ├── test_vector_magnetic_field.py
    ├── test_prediction.py
    └── test_swx_models.py
```

## 数据来源

| 数据 | 来源 | API/路径 |
|------|------|----------|
| 太阳自转 | SDO HMI | `data/solar_rotation_sim.csv`（模拟）|
| 黑子数 | SILSO | `data/sunspot_number.csv` |
| 日冕环 | AIA 193 Å | `data/coronal_loop_sim.csv`（模拟）|
| 矢量磁场 | SDO HMI | `data/hmi/*.fits` |
| 日震学 | GONG | `data/helioseismology_modes.csv`（模拟）|
| **实时太阳风** | NOAA SWPC | `services.swpc.noaa.gov/json/` |
| **实时 CME** | DONKI | `kauai.ccmc.gsfc.nasa.gov/DONKI/` |
| **耀斑目录** | Plutino | `data/real/plutino_FlareList_*.csv` |

## 依赖

- Python ≥ 3.10
- `numpy`, `scipy`, `matplotlib`
- `astropy`（FITS 读取）
- `sunpy`（可选，太阳物理）

## 作者

math-science (QClaw agent) | 日期：2026-05-23 | License: MIT
