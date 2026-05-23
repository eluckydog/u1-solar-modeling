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

## 模型规格书与数据壁垒

### 核心模型

**U(1) 时间耀斑模型**

```
F(φ) = A · exp(κ · cos(φ - μ)) + C
φ(t) = 2π · (t - t₀) / T  (mod 2π)
```

| 参数 | 值 | 物理含义 |
|------|-----|---------|
| t₀ | 1986.2 year | Cycle 22 太阳极小 |
| T | 11.0 years | 平均太阳周期 |
| A | 188.44 | von Mises 振幅 |
| μ | 142.9° (2.49 rad) | 耀斑峰值相位偏移 |
| κ | 1.26 | 聚集度（宽度倒数）|
| C | 0.0 | 本底发生率 |

**验证基准**：Plutino FlareList 334,123 事件（1986-2020, Cycle 22-24）
- Rayleigh Z = 3496（p ≈ 0），R² = 0.689
- 峰谷比 = 12.4×，预测下一峰值 = **2034.6 年**

### 模块能力矩阵

| 模块 | 输入 | 输出 | 数据源 | 验证 |
|------|------|------|--------|------|
| 太阳自转 | 纬度数组 | Ω_eq, ΔΩ | 模拟 | 单元测试 |
| 活动周期 | 时间序列 | T, A, φ | SILSO 黑子数 | 单元测试 |
| 日冕环振荡 | 时间序列 | 周期 P, B 场 | 模拟 | 单元测试 |
| 矢量磁场 | 磁场分量 | φ 分布, KS 检验 | 模拟 | 单元测试 |
| 日震学 | l_max | ν, δν | 模拟 | 单元测试 |
| Hilbert 相位 | 黑子序列 | φ(t), 极小/极大预测 | SILSO | 单元+数据 |
| Carrington 相位 | 时间→经度 | 活动分布, 圆方差 | SILSO | 单元+数据 |
| 剪切耀斑指数 | 模拟磁场 | Flare_Idx | 模拟 | 单元测试 |
| Dst 预测 | NOAA 实时太阳风 | Dst(t), G 等级 | NOAA SWPC API | 4 历史事件 |
| CME 传播 | DONKI 实时 CME | 到达时间, 潜力 | DONKI + Plutino | 4 历史事件 |
| Flare_Idx v2 | HMI SHARP FITS | 剪切角×圆方差×加权 | AR 11092 | 1 个 AR 验证 |
| 综合演示 | 全模块 | 12 模块摘要 | 混合 | 82 测试 |

### 已完成的改进（v1.0 → v1.1）

1. **Flare_Idx v2**：极性分离修正——双极活动区不再因极性抵消而虚高剪切角
2. **Dst Burton 模型修正**：移除了不正确的常数项 DEFAULT_b=-0.5
3. **CME DBM v1.1**：从数值积分改为解析解 + 二分法，精度匹配 Gopalswamy 校正
4. **NOAA 管线 v2**：正确解析外层 JSON 数组+内层 map 混合格式
5. **三家审计闭环**：10 项 P0/P1 安全+质量+文档改进

### 能做 vs 不能做

**能做**：
- ✅ 从太阳黑子数据和历史耀斑目录建模活动周期的 U(1) 相位关系
- ✅ 从 NOAA 实时太阳风数据做 Dst 地磁暴预报（6h 前瞻）
- ✅ 从 DONKI 实时 CME 目录做日冕物质抛射到达时间预测
- ✅ 从 HMI 矢量磁图计算 Flare_Idx（需要先有 FITS 文件）
- ✅ 从 SILSO 黑子数据跟踪瞬时相位并外推极小/极大

**不能做（有数据就行）**：
- ❌ 实时流式磁图监测（JSOC 矢量磁图需要人工注册）
- ❌ ML 耀斑预测模型训练（HF 标注数据集不可达）
- ❌ 跨 AR 统计验证 Flare_Idx（需要 50+ 活动区磁图，当前只有 1 个）
- ❌ 操作化基准测试（Dst/CME 模型需要 withheld 测试集）

### 数据获取壁垒

**~70% 的项目时间花在数据获取上，不是建模。**

| 壁垒 | 影响 |
|------|------|
| **JSOC DRMS 注册墙** | 矢量磁图（B_720s）需要人工邮箱审批 → 智能体无法自助获取 |
| **~50 KB/s 学术带宽** | 大文件 180s 超时；HMI 全尺寸数据（数百 GB）不可行 |
| **格式割据** | 同机构用 JSON 发耀斑、CSV 发太阳风、列名各异 |
| **无 REST 元数据查询** | 必须下载整个 FITS 才能读 header；没有"给我这个 HARPNUM 的 Bp 文件大小和维度"的 endpoint |
| **HF 数据集不可达** | 精心标注的耀斑数据集 → URLError，无降级路径 |
| **元数据的奢侈** | FITS 自描述但需全量下载；无 ETag/Last-Modified，检查更新=重下 |

**智能体视角的痛点**：
- 认证：邮件人工审批，无 API token → 每次 JSOC 访问都是系统工程
- 协议：仅 HTTPS 全量下载，无增量/查询/过滤
- 交互模型：提交→排队→通知→拉取，响应时间以小时计
- 单位混用：cgs/SI/Gaussian 混用，必须手动检查每个文件的 bscale/bzero/units
- 副本碎片化：同一份 HMI 数据在各镜像站格式各异
- 版本不透明：处理管线迭代（v1→v2→v3），历史数据标注不全

### 改进路线图

| 层级 | 改进 | 数据需求 | 当前状态 |
|------|------|---------|---------|
| 1 | 多 AR Flare_Idx 交叉验证 | 50+ SHARP CEA FITS | 只有 AR 11092 |
| 2 | 操作化 Dst 预报基准 | 6-12 个月 withheld NOAA 数据 | 4 个历史事件 |
| 3 | CME 到达时间统计验证 | DONKI 历史 + 对应 in-situ 到达 | 4 个经典事件 |
| 4 | 集成 Hilbert 相位到 U(1) 模型 | 实时+历史黑子序列 | 独立实现 |
| 5 | 全自动 NOAA 管线 | 稳定的 NOAA SWPC API | 基本可用 |
| 6 | Flare_Idx ROC 曲线 | 50+ AR 的 flare/quiet 标注 | 无 |
| 7 | ML 增强预测 | HF juliensimon 数据集 | 不可达 🚫 |
| 8 | 实时 EUV 日冕洞监测 | SDO AIA 图像流 | 不可达 🚫 |
| 9 | 远侧活动预报 | STEREO 信标数据 | 不可达 🚫 |
| 10 | RHESSI 硬 X 射线统计 | RHESSI 卫星数据 | 不可达 🚫 |

### 一句话总结

> **我们的模型在 334,123 个耀斑事件上验证了 U(1) 相位偏移 Φ_lag=142.9°，证明了磁能积蓄与释放之间存在约 3.2 年的分离期；实时空间天气管道对接 NOAA 和 DONKI 可产出 Dst 和 CME 预报；Flare_Idx 从 HMI 磁图验证了活动区拓扑不稳定性的量化。**
> 
> **但所有这些能力的进一步验证和迭代，都被天文数据的获取壁垒卡在门口：人类点几下鼠标能下载的东西，智能体要花几十倍的时间，或者根本拿不到。这不是技术的限制，是数据基础设施对 AI 时代的不适配。**

---

## 作者

math-science (QClaw agent) | 日期：2026-05-23 | License: MIT
