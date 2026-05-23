# 太阳活动周期（U(1) 时间对称）

## 理论基础

太阳黑子数量每 11 年重复一次（施瓦贝周期）。

### U(1) 对称性

太阳活动周期可以用 U(1) 相位变量建模：
```
R(t) = R₀ + A * sin(2πt/T + φ)
```
其中：
- `t` = 时间（年，U(1) 变量）
- `T` = 周期（≈ 11 年）
- `φ` = 相位（U(1) 变量）
- `R₀` = 基线
- `A` = 振幅

### 物理意义

- **11 年周期**：太阳发电机振荡
- **施瓦贝周期**：1755 年以来已观测到 24 个周期
- **不对称**：上升相比下降相更陡

## 数据来源

| 数据源 | 说明 | 链接 |
|--------|------|------|
| SILSO | 月平均黑子数（1750-至今） | https://www.sidc.be/silso/ |
| NOAA | 太阳活动指标 | https://www.swpc.noaa.gov |

## 拟合方法

1. **读取数据**：CSV 文件（year, month, sunspot_number）
2. **FFT 估计周期**：`scipy.fft.fft`
3. **曲线拟合**：`scipy.optimize.curve_fit`
4. **输出结果**：T, A, φ

## 代码示例

```python
import numpy as np
from scipy.optimize import curve_fit

def solar_cycle(t, R0, A, T, phi):
    return R0 + A * np.sin(2 * np.pi * t / T + phi)

# 拟合
popt, pcov = curve_fit(solar_cycle, years, sunspot_numbers)
R0_fit, A_fit, T_fit, phi_fit = popt
```

## 科学价值

- **空间任务规划**：下一个周期峰值预测
- **太阳发电机理论**：αΩ 发电机振荡
- **气候研究**：太阳活动对气候的影响

## 参考文献

1. Hathaway, D. H. (2015). *The Solar Cycle*. Living Reviews in Solar Physics, 12, 4.
2. Charbonneau, P. (2020). *Dynamo Models of the Solar Cycle*. Living Reviews in Solar Physics, 17, 4.
