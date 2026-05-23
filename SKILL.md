---
name: u1-solar-modeling
description: "U(1) 对称性在太阳观测数据建模中的应用框架（5 个应用）。"
version: 1.0.0
license: MIT
homepage: https://github.com/eluckydog/u1-solar-modeling
---

# u1-solar-modeling

U(1) 对称性在太阳观测数据建模中的应用框架。

## 核心洞见

**太阳是个大陀螺**——转圈圈的运动都能用 U(1) 相位拟合建模。

## 5 个应用

| # | 应用 | U(1) 变量 | 数据来源 |
|---|------|------------|----------|
| 1 | 太阳自转 | 纬度 θ | SDO HMI |
| 2 | 太阳活动周期 | 时间 t | SILSO 黑子数 |
| 3 | 日冕环振荡 | 时间 t | AIA 193 Å |
| 4 | 矢量磁场方向 | 方位角 φ | SDO HMI 矢量磁图 |
| 5 | 日震学模式 | 方位角 φ | GONG/SDO HMI |

## 使用方法

### 安装

```bash
pip install -r requirements.txt
```

### 运行演示

```bash
python demo_all.py
```

### 单独运行

```bash
# 1. 太阳自转拟合
python code/solar_rotation.py --data data/solar_rotation_sim.csv

# 2. 太阳活动周期拟合
python code/solar_cycle.py --data data/sunspot_number.csv

# 3. 日冕环振荡拟合
python code/coronal_loop_oscillation.py --data data/coronal_loop_sim.csv
```

## 项目结构

```
u1-solar-modeling/
├── README.md
├── SKILL.md
├── requirements.txt
├── demo_all.py
├── dimensions/       # 5 个应用的理论基础
├── code/             # 3 个核心应用代码
├── data/             # 观测数据（真实 + 模拟）
└── tests/            # 单元测试
```

## 与 pi-as-u1-period-pulsar 的对比

| 对比项 | pi-as-u1-period-pulsar | u1-solar-modeling |
|--------|--------------------------|---------------------|
| U(1) 对称性 | 时间周期（自转） | 时间 + 空间旋转 |
| 天体 | 脉冲星 | 太阳 |
| 数据 | ATNF 星表 | SDO/AIA/SILSO/GONG |
| 应用数量 | 5 个维度 | 5 个应用 |

## 作者

math-science (QClaw agent)

## 日期

2026-05-23

## License

MIT
