---
name: u1-solar-modeling
description: "U(1) 对称性在太阳观测数据建模中的应用框架：5个U(1)应用 + 面向耀斑/Dst/CME/太阳风的空间天气预测管线（Flare_Idx、Hilbert相位、Carrington相位、Burton地磁暴、DBM日冕物质抛射、NOAA实时数据管道）。82测试。"
version: 1.1.0
license: MIT
homepage: https://github.com/eluckydog/u1-solar-modeling
---

# u1-solar-modeling

U(1) 对称性在太阳观测数据建模中的应用框架 + 空间天气预测管线。

## 核心洞见

**太阳是个大陀螺**——转圈圈的运动都能用 U(1) 相位拟合建模。

## 全部 12 模块

### 5 个 U(1) 应用

| # | 应用 | U(1) 变量 | 数据来源 |
|---|------|------------|----------|
| 1 | 太阳自转 | 纬度 θ | SDO HMI |
| 2 | 太阳活动周期 | 时间 t | SILSO 黑子数 |
| 3 | 日冕环振荡 | 时间 t | AIA 193 Å |
| 4 | 矢量磁场方向 | 方位角 φ | SDO HMI 矢量磁图 |
| 5 | 日震学模式 | 方位角 φ | GONG/SDO HMI |

### 3 个预测模块

| # | 模块 | 功能 |
|---|------|------|
| 6 | Hilbert 相位跟踪 | 黑子瞬时相位 → 外推极小/极大年 |
| 7 | 自转相位日历 | Carrington 经度 → 活动经度识别 |
| 8 | 剪切耀斑指数 | U(1) 圆方差 × 剪切角 → 耀斑潜力 |

### 2 个空间天气模型

| # | 模块 | 功能 |
|---|------|------|
| 9 | Dst 地磁暴预报 | Burton 方程 + NOAA 实时太阳风 |
| 10 | CME 传播 | 解析 DBM + Gopalswamy 校正 + DONKI 实时数据 |

### 1 个综合验证 + 1 个核心模型

| # | 模块 | 功能 |
|---|------|------|
| 11 | Flare_Idx 验证 | HMI SHARP 磁图 → 极性分离剪切角 × 圆方差 |
| 12 | U(1) 时间耀斑模型 | 基于 334,123 事件的 von Mises 拟合 (R²=0.689) |

## 使用方法

### 安装

```bash
pip install -r requirements.txt
```

### 运行演示

```bash
python demo_all.py           # 全部 12 模块
python -m pytest tests/ -v   # 82 个测试
```

### 单独运行

```bash
# 5 应用
python code/solar_rotation.py --data data/solar_rotation_sim.csv
python code/solar_cycle.py --data data/sunspot_number.csv
python code/coronal_loop_oscillation.py --data data/coronal_loop_sim.csv

# 空间天气
python code/prediction/dst_model.py
python code/prediction/cme_model.py
```

## 项目结构

```
u1-solar-modeling/
├── README.md
├── SKILL.md
├── demo_all.py              # 12 模块端到端演示
├── dimensions/              # 5 应用理论基础
├── code/                    # 5 应用 + 核心模型 + 预测/空间天气
│   ├── prediction/          # 预测管线
│   │   ├── dst_model.py     # Dst 地磁暴预测
│   │   ├── cme_model.py     # CME 传播预测
│   │   ├── hilbert_phase.py # Hilbert 相位跟踪
│   │   ├── shear_flare_index.py
│   │   └── rotation_phase_map.py
│   ├── flare_idx.py         # HMI 验证
│   ├── u1_solar_model.py    # 核心时间模型
│   └── ...
├── data/                    # 观测/实时数据
├── docs/                    # 模型文档
└── tests/                   # 82 测试
```

## 核心模型参数

| 参数 | 值 | 含义 |
|------|-----|------|
| Φ_lag | 142.9° | 耀斑峰值在太阳极大后~3.2 年 |
| R² | 0.689 | von Mises 拟合优度 |
| 峰谷比 | 12.4× | 高活动vs低活动期耀斑倍率 |
| N | 334,123 | Plutino 拟合事件数 |
| 下一峰值 | 2034.6 年 | 预测 |

## 实时数据管道

- **NOAA SWPC**: `services.swpc.noaa.gov/json/` (太阳风、XRS、耀斑)
- **DONKI**: `kauai.ccmc.gsfc.nasa.gov/DONKI/` (CME 目录)
- **Plutino**: `data/real/plutino_FlareList_*.csv` (1986-2020, 207K 事件)

## 作者

math-science (QClaw agent) | 2026-05-23 | MIT
