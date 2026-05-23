# 矢量磁场方向（U(1) 方向对称）

## 理论基础

太阳光球磁场是矢量（有大小 + 方向）。方向是 U(1) 变量。

### U(1) 对称性

磁场方向可以用 U(1) 相位变量建模：
```
φ ∈ [0, 2π)
```
其中：
- `φ` = 磁场方位角（U(1) 变量）
- 转 2π 回来，方向不变

### 物理意义

- **磁极性反转**：太阳周期中 φ 翻转 180°
- **磁场剪切**：日冕环足点 φ 差 → 能量存储
- **耀斑预测**：φ 快速变化 → 可能爆发

## 数据来源

| 数据源 | 说明 | 链接 |
|--------|------|------|
| SDO HMI | 矢量磁图（视向场 + 横向场） | https://hmi.stanford.edu |
| SOLIS | 矢量磁图 | https://nso.edu/solis/ |

## 分析方法

1. **读取数据**：FITS 文件（B_los, B_transverse）
2. **计算方向**：φ = arctan2(B_y, B_x)
3. **统计分布**：φ 的极坐标直方图
4. **输出结果**：方向分布、剪切角

## 代码示例

```python
import numpy as np
import sunpy.map

# 读取矢量磁图
map_obj = sunpy.map.Map('hmi.B_720s.vector.fits')

# 计算方位角
Bx = map_obj.data[0]  # 横向场 x 分量
By = map_obj.data[1]  # 横向场 y 分量
phi = np.arctan2(By, Bx)  # 方位角 ∈ [-π, π]

# 极坐标直方图
hist, bins = np.histogram(phi, bins=36, range=(-np.pi, np.pi))
```

## 科学价值

- **耀斑预测**：磁场剪切角 > 60° → 高概率爆发
- **日冕加热**：光球磁场耗散 → 日冕能量输入
- **太阳发电机**：表面磁场方向分布 → 内部发电机信息

## 参考文献

1. Scherrer, P. H., et al. (2012). *The Helioseismic and Magnetic Imager (HMI)*. Solar Physics, 275, 207-227.
2. Borrero, J. M., et al. (2011). *VFISV: Very Fast Inversion of the Stokes Vector*. Solar Physics, 273, 267-293.
