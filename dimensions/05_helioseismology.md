# 日震学模式（U(1) 方位角对称）

## 理论基础

太阳内部的声波（p-模式）在球面上传播，方位角方向是 U(1) 对称。

### U(1) 对称性

日震学模式可以用 U(1) 相位变量建模：
```
Y_l^m(θ, φ) = N * P_l^m(cosθ) * e^{i m φ}
```
其中：
- `φ` = 方位角（U(1) 变量，∈ [0, 2π)）
- `m` = 方位角阶数（整数，∈ [-l, l]）
- `l` = 总角动量量子数
- `e^{i m φ}` = U(1) 相位因子

### 物理意义

- **p-模式**：声波在太阳内部共振
- **l 模式**：径向节点数
- **m 模式**：方位角波数（U(1) 傅里叶模式）
- **频率分裂**：不同 m 的频率差 → 内部转动剖面

## 数据来源

| 数据源 | 说明 | 链接 |
|--------|------|------|
| GONG | 地面日震学网络 | https://gong.nso.edu |
| SDO HMI | 日震学功率谱 | https://hmi.stanford.edu |

## 分析方法

1. **读取数据**：FITS 文件（功率谱）
2. **模式识别**：峰值检测（find_peaks）
3. **频率拟合**：ν_l,m = ν_l,0 + δν_l,m(Ω)
4. **输出结果**：模式频率 ν_l,m

## 代码示例

```python
import numpy as np
import sunpy.map

# 读取功率谱
map_obj = sunpy.map.Map('hmi.VergylTe.2024.fits')

# 提取模式频率（简化）
# 实际需要用专门软件（如 GONG 管道）
power_spectrum = map_obj.data
frequencies = extract_frequencies(power_spectrum)  # 自定义函数

# 拟合频率分裂
def frequency_splitting(nu, l, m, Omega_profile):
    # 简化公式
    return nu + (m / (2*l+1)) * Omega_profile

# 拟合
popt, pcov = curve_fit(frequency_splitting, (nu_l_m, l, m), Omega_profile)
```

## 科学价值

- **太阳内部转动剖面**：Ω(r, θ) 测量
- **太阳核心氦丰度**：p-模式频率敏感
- **太阳发电机**：内部差分旋转 → αΩ 发电机
- **恒星物理**：类太阳恒星的内部结构

## 参考文献

1. Christensen-Dalsgaard, J. (2002). *Helioseismology*. Reviews of Modern Physics, 74, 1073-1129.
2. Thompson, M. J., et al. (2003). *The Internal Rotation of the Sun*. Annual Review of Astronomy and Astrophysics, 41, 599-643.
