#!/usr/bin/env python3
"""
太阳自转拟合（U(1) 时间周期）
拟合 omega(theta) = omega_eq - delta_omega * sin^2(theta)

支持两种数据格式：
1. 模拟数据：latitude, omega (模拟)
2. 实测数据：latitude, omega, omega_err (HMI 观测)
"""

import argparse
import numpy as np
import csv
from scipy.optimize import curve_fit


def differential_rotation(theta, omega_eq, delta_omega):
    """较差自转公式（U(1) 时间周期）"""
    return omega_eq - delta_omega * np.sin(theta)**2


def fit_solar_rotation(data_file, data_type='simulated'):
    """拟合太阳自转数据
    
    Parameters:
    -----------
    data_file : str
        CSV 文件路径
    data_type : str
        'simulated' (latitude, omega) 或 'observed' (latitude, omega, omega_err)
    
    Returns:
    --------
    omega_eq_fit, delta_omega_fit : float
        拟合参数
    """
    # 读取数据
    latitudes = []
    omegas = []
    omega_errs = None
    
    try:
        with open(data_file, 'r') as f:
            reader = csv.DictReader(f)
            
            if data_type == 'simulated':
                for row in reader:
                    latitudes.append(float(row['latitude']))
                    omegas.append(float(row['omega']))
                omega_errs = None
            
            elif data_type == 'observed':
                for row in reader:
                    latitudes.append(float(row['latitude']))
                    omegas.append(float(row['omega']))
                if 'omega_err' in row:
                    # Need to re-read for errors
                    f.seek(0)
                    reader = csv.DictReader(f)
                    omega_errs = []
                    for row in reader:
                        omega_errs.append(float(row['omega_err']))
                    omega_errs = np.array(omega_errs)
    except FileNotFoundError:
        print(f"[ERROR] 文件不存在: {data_file}")
        return None, None
    except Exception as e:
        print(f"[ERROR] 读取数据失败: {e}")
        return None, None
    
    latitudes = np.array(latitudes)
    omegas = np.array(omegas)
    
    if len(latitudes) < 3 or len(omegas) < 3:
        print(f"[ERROR] 数据点不足 ({len(latitudes)} 个)，至少需要 3 个点")
        return None, None
    
    # 初始猜测
    omega_eq_guess = 14.5  # deg/day
    delta_omega_guess = 3.5   # deg/day
    
    # 曲线拟合
    try:
        if omega_errs is not None:
            weights = 1.0 / omega_errs
            popt, pcov = curve_fit(differential_rotation, latitudes, omegas, 
                                   p0=[omega_eq_guess, delta_omega_guess],
                                   sigma=weights, absolute_sigma=True)
        else:
            popt, pcov = curve_fit(differential_rotation, latitudes, omegas, 
                                   p0=[omega_eq_guess, delta_omega_guess])
        
        omega_eq_fit, delta_omega_fit = popt
        
        print("=" * 60)
        print("太阳自转拟合结果（U(1) 时间周期）")
        print("=" * 60)
        print(f"omega_eq (赤道角速度) = {omega_eq_fit:.3f} deg/day")
        print(f"delta_omega (较差自转参数) = {delta_omega_fit:.3f} deg/day")
        print(f"极区角速度 = {omega_eq_fit - delta_omega_fit:.3f} deg/day")
        print("=" * 60)
        
        return omega_eq_fit, delta_omega_fit
        
    except Exception as e:
        print(f"[ERROR] 拟合失败: {e}")
        return None, None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='太阳自转拟合（U(1) 时间周期）')
    parser.add_argument('--data', type=str, required=True, help='数据文件路径')
    parser.add_argument('--type', type=str, default='simulated', 
                       choices=['simulated', 'observed'], help='数据类型')
    args = parser.parse_args()
    
    fit_solar_rotation(args.data, data_type=args.type)
