#!/usr/bin/env python3
"""
太阳自转拟合（U(1) 时间周期）
拟合 Ω(θ) = Ω_eq - ΔΩ * sin²θ
"""

import argparse
import numpy as np
import csv
from scipy.optimize import curve_fit

def differential_rotation(latitude, omega_eq, delta_omega):
    """较差自转公式"""
    theta = np.deg2rad(latitude)
    return omega_eq - delta_omega * np.sin(theta)**2

def fit_solar_rotation(data_file):
    """拟合太阳自转数据"""
    # 读取数据
    latitudes = []
    rotation_rates = []
    with open(data_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            latitudes.append(float(row['latitude']))
            rotation_rates.append(float(row['rotation_rate']))
    
    latitudes = np.array(latitudes)
    rotation_rates = np.array(rotation_rates)
    
    # 曲线拟合
    popt, pcov = curve_fit(differential_rotation, latitudes, rotation_rates, p0=[14.5, 3.5])
    omega_eq_fit, delta_omega_fit = popt
    
    # 输出结果
    print("=== 太阳自转拟合结果 ===")
    print(f"Ω_eq (赤道角速度) = {omega_eq_fit:.3f} deg/day")
    print(f"ΔΩ (纬度差) = {delta_omega_fit:.3f} deg/day")
    print(f"极区角速度 = {omega_eq_fit - delta_omega_fit:.3f} deg/day")
    
    return omega_eq_fit, delta_omega_fit

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='太阳自转拟合（U(1) 时间周期）')
    parser.add_argument('--data', type=str, default='../data/solar_rotation_sim.csv', help='数据文件路径')
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    fit_solar_rotation(args.data)

if __name__ == '__main__':
    main()
