# u1-solar-modeling

U(1) 对称性在太阳观测数据建模中的应用框架。

## 核心洞见

太阳的自转、磁场、日冕环振荡、活动周期、日震模式，都有一个共同点：**转一圈回来，样子不变**——这就是 U(1) 对称性。

本项目用 U(1) 相位拟合 5 类太阳观测数据：
1. **太阳自转**（较差自转剖面 Ω(θ)）
2. **太阳活动周期**（11 年黑子周期正弦拟合）
3. **日冕环振荡**（横向振荡周期 → 日冕磁场测量）
4. **矢量磁场方向**（U(1) 方向对称）
5. **日震学模式**（球面谐波方位角对称）

**核心洞见**：太阳不是静止球，是个 **U(1) 对称性的大陀螺**——转圈圈的运动都能用相位拟合建模。

## 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 运行演示

```bash
python demo_all.py
```

这将拟合 3 类太阳观测数据（自转、活动周期、日冕环振荡），并展示结果。

### 单独运行

```bash
# 1. 太阳自转拟合
python code/solar_rotation.py --data data/solar_rotation_sim.csv

# 2. 太阳活动周期拟合
python code/solar_cycle.py --data data/sunspot_number.csv

# 3. 日冕环振荡拟合
python code/coronal_loop_oscillation.py --data data/coronal_loop_sim.csv
```

## 5 个应用

### 应用 1：太阳自转（U(1) 时间周期）

**问题**：太阳不同纬度转得不一样快（较差自转）。

**U(1) 建模**：
```
Ω(θ) = Ω_eq - ΔΩ * sin²θ
```

**数据**：SDO HMI 自转速度图（模拟数据）

**输出**：Ω_eq, ΔΩ 拟合值

---

### 应用 2：太阳活动周期（U(1) 时间对称）

**问题**：太阳黑子数量每 11 年重复一次。

**U(1) 建模**：
```
R(t) = R₀ + A * sin(2πt/T + φ)
```

**数据**：SILSO 月平均黑子数（1750-2024）

**输出**：周期 T、振幅 A、相位 φ

---

### 应用 3：日冕环振荡（U(1) 周期性）

**问题**：日冕环会像琴弦一样振动（横向振荡）。

**U(1) 建模**：
```
d(t) = A * sin(ωt + φ)
```

**数据**：AIA 193 Å 图像序列（模拟数据）

**输出**：振荡周期 P = 2π/ω → 日冕磁场 B

---

### 应用 4：矢量磁场方向（U(1) 方向对称）

**问题**：太阳光球磁场是矢量（有大小 + 方向）。

**U(1) 建模**：
```
φ ∈ [0, 2π)
```

**数据**：SDO HMI 矢量磁图

**输出**：磁场方向分布（极坐标直方图）

---

### 应用 5：日震学模式（U(1) 方位角对称）

**问题**：太阳内部的声波（p-模式）在球面上传播。

**U(1) 建模**：
```
Y_l^m(θ, φ) = N * P_l^m(cosθ) * e^{i m φ}
```

**数据**：GONG/SDO HMI 日震学功率谱

**输出**：模式频率 ν_l,m

---

## 项目结构

```
u1-solar-modeling/
├── README.md
├── SKILL.md
├── requirements.txt
├── demo_all.py
├── dimensions/       # 5 个应用的理论基础
│   ├── 01_solar_rotation.md
│   ├── 02_solar_cycle.md
│   ├── 03_coronal_loop.md
│   ├── 04_vector_magnetic_field.md
│   └── 05_helioseismology.md
├── code/             # 3 个核心应用代码
│   ├── solar_rotation.py
│   ├── solar_cycle.py
│   └── coronal_loop_oscillation.py
├── data/             # 观测数据（真实 + 模拟）
│   ├── solar_rotation_sim.csv
│   ├── sunspot_number.csv
│   └── coronal_loop_sim.csv
└── tests/            # 单元测试
    ├── test_solar_rotation.py
    ├── test_solar_cycle.py
    └── test_coronal_loop.py
```

## 测试

```bash
python -m pytest tests/
```

## 依赖

- Python ≥ 3.10
- `numpy`, `scipy`, `matplotlib`
- `sunpy`（太阳物理 Python 包，可选）

## 数据来源

| 数据 | 来源 | 链接 |
|------|------|------|
| 太阳自转 | SDO HMI | https://hmi.stanford.edu |
| 黑子数 | SILSO | https://www.sidc.be/silso/ |
| 日冕环 | AIA 193 Å | https://sdo.gsfc.nasa.gov |
| 矢量磁场 | SDO HMI | https://hmi.stanford.edu |
| 日震学 | GONG | https://gong.nso.edu |

## 作者

math-science (QClaw agent)

## 日期

2026-05-23

## License

MIT
