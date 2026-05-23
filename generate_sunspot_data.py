#!/usr/bin/env python3
"""
生成太阳黑子数模拟数据（1750-2024，274 年）
使用 11 年周期正弦波 + 噪声
"""

import csv
import numpy as np

# 参数
R0 = 50.0  # 基线
A = 100.0  # 振幅
T = 11.0   # 周期（年）
phi = 0.0   # 相位

# 生成数据
start_year = 1750
end_year = 2024
data = []

for year in range(start_year, end_year + 1):
    for month in range(1, 13):
        t = year + month / 12.0
        # 正弦波 + 噪声
        R = R0 + A * np.sin(2 * np.pi * t / T + phi) + np.random.normal(0, 10)
        # 确保非负
        R = max(R, 0)
        data.append([year, month, R])

# 写入 CSV
with open('data/sunspot_number.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['year', 'month', 'sunspot_number'])
    writer.writerows(data)

print(f"[OK] Generated {len(data)} data points ({start_year}-{end_year})")
