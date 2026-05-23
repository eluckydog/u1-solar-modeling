#!/usr/bin/env python3
"""
太阳活动周期拟合（U(1) 时间对称）
拟合 R(t) = R0 + A * sin(2πt/T + φ)
"""

import argparse
import numpy as np
import csv
from scipy.optimize import curve_fit

def solar_cycle(t, R0, A, T, phi):
    """太阳活动周期公式"""
    return R0 + A * np.sin(2 * np.pi * t / T + phi)

def fit_solar_cycle(data_file):
    """拟合太阳活动周期数据"""
    # 读取数据
    years = []
    sunspot_numbers = []
    with open(data_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            year = float(row['year'])
            month = float(row['month'])
            t = year + month / 12.0
            years.append(t)
            sunspot_numbers.append(float(row['sunspot_number']))
    
    years = np.array(years)
    sunspot_numbers = np.array(sunspot_numbers)
    
    # 初始猜测
    T_guess = 11.0  # 11 年周期
    R0_guess = np.mean(sunspot_numbers)
    A_guess = (max(sunspot_numbers) - min(sunspot_numbers)) / 2.0
    phi_guess = 0.0
    
    # 曲线拟合
    popt, pcov = curve_fit(solar_cycle, years, sunspot_numbers, p0=[R0_guess, A_guess, T_guess, phi_guess])
    R0_fit, A_fit, T_fit, phi_fit = popt
    
    # 输出结果
    print("=== 太阳活动周期拟合结果 ===")
    print(f"R0 (基线) = {R0_fit:.3f}")
    print(f"A (振幅) = {A_fit:.3f}")
    print(f"T (周期) = {T_fit:.3f} 年")
    print(f"φ (相位) = {phi_fit:.3f} rad")
    
    return R0_fit, A_fit, T_fit, phi_fit

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='太阳活动周期拟合（U(1) 时间对称）')
    parser.add_argument('--data', type=str, default='../data/sunspot_number.csv', help='数据文件路径')
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    fit_solar_cycle(args.data)

if __name__ == '__main__':
    main()
