#!/usr/bin/env python3
"""
日冕环振荡拟合（U(1) 周期性）
拟合 d(t) = A * sin(ωt + φ)

支持两种数据格式：
1. 模拟数据：time, displacement
2. 实测数据：time, displacement, displacement_err (AIA 193 Å)
"""

import argparse
import numpy as np
import csv
from scipy.optimize import curve_fit

def coronal_loop_oscillation(t, A, omega, phi):
    """日冕环振荡公式"""
    return A * np.sin(omega * t + phi)

def estimate_b_field(A, omega, n_e=1e15, L=100e6):
    """估算磁场强度 B
    
    Parameters:
    -----------
    A : float
        振幅 (km)
    omega : float
        角频率 (rad/s)
    n_e : float
        电子密度 (m^-3)，默认 1e15
    L : float
        环路长度 (m)，默认 100 Mm
    
    Returns:
    --------
    B : float
        磁场强度 (G)
    """
    from scipy.constants import mu_0, m_p
    
    P = 2 * np.pi / omega  # 周期 (s)
    rho = n_e * m_p  # 密度 (kg/m^3)
    
    B = (2 * np.pi * L / P) * np.sqrt(mu_0 * rho)
    B_G = B * 1e4  # T -> G
    
    return B_G

def fit_coronal_loop_oscillation(data_file, data_type='simulated'):
    """拟合日冕环振荡数据
    
    Parameters:
    -----------
    data_file : str
        CSV 文件路径
    data_type : str
        'simulated' (time, displacement) 或 'observed' (time, displacement, displacement_err)
    
    Returns:
    --------
    A_fit, omega_fit, phi_fit : float
        拟合参数
    """
    # 读取数据
    times = []
    displacements = []
    displacement_errs = None
    
    try:
        with open(data_file, 'r') as f:
            reader = csv.DictReader(f)
            
            if data_type == 'simulated':
                for row in reader:
                    times.append(float(row['time']))
                    displacements.append(float(row['displacement']))
                displacement_errs = None
            
            elif data_type == 'observed':
                for row in reader:
                    times.append(float(row['time']))
                    displacements.append(float(row['displacement']))
                
                f.seek(0)
                reader = csv.DictReader(f)
                displacement_errs = []
                for row in reader:
                    displacement_errs.append(float(row['displacement_err']))
                displacement_errs = np.array(displacement_errs)
    except FileNotFoundError:
        print(f"[ERROR] 文件不存在: {data_file}")
        return None, None, None
    except Exception as e:
        print(f"[ERROR] 读取数据失败: {e}")
        return None, None, None
    
    times = np.array(times)
    displacements = np.array(displacements)
    
    if len(times) < 3 or len(displacements) < 3:
        print(f"[ERROR] 数据点不足 ({len(times)} 个)，至少需要 3 个点")
        return None, None, None
    
    # 初始猜测
    A_guess = max(abs(displacements))
    
    # 从 FFT 估计频率
    from scipy.fft import fft, fftfreq
    N = len(times)
    dt = times[1] - times[0]
    yf = fft(displacements)
    xf = fftfreq(N, dt)
    idx = np.argmax(np.abs(yf[:N//2]))
    freq_guess = abs(xf[idx])
    omega_guess = 2 * np.pi * freq_guess
    
    phi_guess = 0.0
    
    # 曲线拟合
    try:
        if displacement_errs is not None:
            weights = 1.0 / displacement_errs
            popt, pcov = curve_fit(coronal_loop_oscillation, times, displacements, 
                                   p0=[A_guess, omega_guess, phi_guess],
                                   sigma=weights, absolute_sigma=True)
        else:
            popt, pcov = curve_fit(coronal_loop_oscillation, times, displacements, 
                                   p0=[A_guess, omega_guess, phi_guess])
        
        A_fit, omega_fit, phi_fit = popt
        
        P_fit = 2 * np.pi / omega_fit
        B_fit = estimate_b_field(A_fit, omega_fit)
        
        print("=" * 60)
        print("日冕环振荡拟合结果（U(1) 周期性）")
        print("=" * 60)
        print(f"A (振幅) = {A_fit:.3f} km")
        print(f"omega (角频率) = {omega_fit:.6f} rad/s")
        print(f"P (周期) = {P_fit:.2f} s")
        print(f"phi (相位) = {phi_fit:.3f} rad")
        print(f"B (估算磁场) = {B_fit:.1f} G")
        print("=" * 60)
        
        return A_fit, omega_fit, phi_fit
        
    except Exception as e:
        print(f"[ERROR] 拟合失败: {e}")
        return None, None, None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='日冕环振荡拟合（U(1) 周期性）')
    parser.add_argument('--data', type=str, required=True, help='数据文件路径')
    parser.add_argument('--type', type=str, default='simulated', 
                       choices=['simulated', 'observed'], help='数据类型')
    args = parser.parse_args()
    
    fit_coronal_loop_oscillation(args.data, data_type=args.type)
