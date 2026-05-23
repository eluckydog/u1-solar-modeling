# 太阳自转（U(1) 时间周期）

## 理论基础

太阳不是刚体——不同纬度转得不一样快（较差自转）。

### U(1) 对称性

太阳自转可以用 U(1) 相位变量建模：
```
Ω(θ) = Ω_eq - ΔΩ * sin²θ
```
其中：
- `θ` = 纬度（U(1) 变量，∈ [0, π/2]）
- `Ω_eq` = 赤道角速度
- `ΔΩ` = 极区与赤道差

### 物理意义

- **赤道转得快**（≈ 14.5 deg/day）
- **极区转得慢**（≈ 11.9 deg/day）
- **差转产生剪切**（太阳发电机关键）

## 数据来源

| 数据源 | 说明 | 链接 |
|--------|------|------|
| SDO HMI | 日震学自转剖面 | https://hmi.stanford.edu |
| SoHO MDI | 历史自转数据 | https://sohowww.nascom.nasa.gov |

## 拟合方法

1. **读取数据**：CSV 文件（latitude, rotation_rate）
2. **曲线拟合**：`scipy.optimize.curve_fit`
3. **输出结果**：Ω_eq, ΔΩ

## 代码示例

```python
import numpy as np
from scipy.optimize import curve_fit

def differential_rotation(latitude, omega_eq, delta_omega):
    theta = np.deg2rad(latitude)
    return omega_eq - delta_omega * np.sin(theta)**2

# 拟合
popt, pcov = curve_fit(differential_rotation, latitudes, rotation_rates)
omega_eq_fit, delta_omega_fit = popt
```

## 科学价值

- **空间天气预警**：自转剖面影响太阳风速度
- **太阳发电机理论**：差转是 αΩ 发电机关键
- **恒星物理**：类太阳恒星的自转演化

## 参考文献

1. Thompson, M. J., et al. (2003). *The Internal Rotation of the Sun*. Annual Review of Astronomy and Astrophysics, 41, 599-643.
2. Howe, R. (2009). *Solar Internal Rotation and Dynamo Waves*. Living Reviews in Solar Physics, 6, 1.
