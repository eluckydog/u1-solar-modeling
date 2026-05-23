#!/usr/bin/env python3
"""
太阳活动周期拟合（U(1) 时间对称）
拟合 R(t) = R0 + A * sin(2πt/T + φ)

支持两种数据格式：
1. 月度数据：year, month, sunspot_number
2. 年度数据：year, ssn
"""

import argparse
import numpy as np
import csv
from scipy.optimize import curve_fit

def solar_cycle(t, R0, A, T, phi):
    """太阳活动周期公式"""
    return R0 + A * np.sin(2 * np.pi * t / T + phi)

def fit_solar_cycle(data_file, freq='monthly'):
    """拟合太阳活动周期数据
    
    Parameters:
    -----------
    data_file : str
        CSV 文件路径
    freq : str
        'monthly' (year, month, sunspot_number) 或 'annual' (year, ssn)
    
    Returns:
    --------
    R0_fit, A_fit, T_fit, phi_fit : float
        拟合参数
    """
    # 读取数据
    years = []
    sunspot_numbers = []
    
    try:
        with open(data_file, 'r') as f:
            reader = csv.DictReader(f)
            
            if freq == 'monthly':
                for row in reader:
                    year = float(row['year'])
                    month = float(row['month'])
                    t = year + month / 12.0
                    years.append(t)
                    sunspot_numbers.append(float(row['sunspot_number']))
            
            elif freq == 'annual':
                for row in reader:
                    year = float(row['year'])
                    years.append(year)
                    sunspot_numbers.append(float(row['ssn']))
    except FileNotFoundError:
        print(f"[ERROR] 文件不存在: {data_file}")
        return None, None, None, None
    except Exception as e:
        print(f"[ERROR] 读取数据失败: {e}")
        return None, None, None, None
    
    years = np.array(years)
    sunspot_numbers = np.array(sunspot_numbers)
    
    if len(years) < 4 or len(sunspot_numbers) < 4:
        print(f"[ERROR] 数据点不足 ({len(years)} 个)，至少需要 4 个点")
        return None, None, None, None
    
    # 初始猜测
    T_guess = 11.0  # 11 年周期
    R0_guess = np.mean(sunspot_numbers)
    A_guess = (max(sunspot_numbers) - min(sunspot_numbers)) / 2.0
    phi_guess = 0.0
    
    # 曲线拟合
    try:
        popt, pcov = curve_fit(solar_cycle, years, sunspot_numbers, p0=[R0_guess, A_guess, T_guess, phi_guess])
        R0_fit, A_fit, T_fit, phi_fit = popt
        
        # 计算拟合曲线
        sunspot_fit = solar_cycle(years, R0_fit, A_fit, T_fit, phi_fit)
        
        # 输出结果
        print("=" * 60)
        print("太阳活动周期拟合结果（U(1) 时间对称）")
        print("=" * 60)
        print(f"R0 (基线) = {R0_fit:.3f}")
        print(f"A (振幅) = {A_fit:.3f}")
        print(f"T (周期) = {T_fit:.3f} 年")
        print(f"phi (相位) = {phi_fit:.3f} rad")
        print("=" * 60)
        
        return R0_fit, A_fit, T_fit, phi_fit
        
    except Exception as e:
        print(f"[ERROR] 拟合失败: {e}")
        return None, None, None, None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='太阳活动周期拟合（U(1) 时间对称）')
    parser.add_argument('--data', type=str, required=True, help='数据文件路径')
    parser.add_argument('--freq', type=str, default='monthly', choices=['monthly', 'annual'], help='数据频率')
    args = parser.parse_args()
    
    fit_solar_cycle(args.data, freq=args.freq)
