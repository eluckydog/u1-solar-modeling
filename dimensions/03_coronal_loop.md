# 日冕环振荡（U(1) 周期性）

## 理论基础

日冕环会像琴弦一样振动（横向振荡），周期与日冕磁场强度相关。

### U(1) 对称性

日冕环振荡可以用 U(1) 相位变量建模：
```
d(t) = A * sin(ωt + φ)
```
其中：
- `t` = 时间（U(1) 变量）
- `ω` = 角频率（U(1) 相位速度）
- `φ` = 初始相位（U(1) 变量）
- `A` = 振幅

### 物理意义

- **周期 P = 2π/ω**
- **日冕磁场 B ≈ (2π/L) * √(μ₀ρ) * (A/ω)**（简化公式）
- **日冕震学**：通过振荡测量日冕磁场（无法用磁场仪直接测量）

## 数据来源

| 数据源 | 说明 | 链接 |
|--------|------|------|
| AIA 193 Å | 日冕环图像序列 | https://sdo.gsfc.nasa.gov |
| AIA 171 Å | 日冕环图像序列 | https://sdo.gsfc.nasa.gov |

## 拟合方法

1. **读取数据**：CSV 文件（time, displacement）
2. **FFT 估计频率**：`scipy.fft.fft`
3. **曲线拟合**：`scipy.optimize.curve_fit`
4. **输出结果**：ω, P, B_estimate

## 代码示例

```python
import numpy as np
from scipy.optimize import curve_fit

def coronal_loop_oscillation(t, A, omega, phi):
    return A * np.sin(omega * t + phi)

# 拟合
popt, pcov = curve_fit(coronal_loop_oscillation, times, displacements)
A_fit, omega_fit, phi_fit = popt

# 计算周期
P_fit = 2 * np.pi / omega_fit
```

## 科学价值

- **日冕磁场测量**：唯一能测量日冕磁场的方法
- **波能量传输**：理解日冕加热问题
- **空间天气预警**：日冕物质抛射（CME）预测

## 参考文献

1. Nakariakov, V. M., & Kola, L. (2020). *Coronal Seismology*. Living Reviews in Solar Physics, 17, 3.
2. Aschwanden, M. J. (2009). *Coronal Seismology*. Space Science Reviews, 149, 31-64.
