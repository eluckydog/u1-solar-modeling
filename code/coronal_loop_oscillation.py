#!/usr/bin/env python3
"""
日冕环振荡拟合（U(1) 周期性）
拟合 d(t) = A * sin(ωt + φ)
"""

import argparse
import numpy as np
import csv
from scipy.optimize import curve_fit

def coronal_loop_oscillation(t, A, omega, phi):
    """日冕环振荡公式"""
    return A * np.sin(omega * t + phi)

def fit_coronal_loop_oscillation(data_file):
    """拟合日冕环振荡数据"""
    # 读取数据
    times = []
    displacements = []
    with open(data_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            times.append(float(row['time']))
            displacements.append(float(row['displacement']))
    
    times = np.array(times)
    displacements = np.array(displacements)
    
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
    popt, pcov = curve_fit(coronal_loop_oscillation, times, displacements, p0=[A_guess, omega_guess, phi_guess])
    A_fit, omega_fit, phi_fit = popt
    
    # 计算周期
    P_fit = 2 * np.pi / omega_fit
    
    # 估计日冕磁场（简化公式）
    # B ≈ (2π/L) * sqrt(μ0 ρ) * (A/ω)
    # 假设 L = 100 Mm, ρ = 1.67e-12 kg/m^3
    L = 100e6  # 100 Mm -> m
    rho = 1.67e-12  # kg/m^3
    mu0 = 4 * np.pi * 1e-7
    B_estimate = (2 * np.pi / L) * np.sqrt(mu0 * rho) * (A_fit / omega_fit)
    
    # 输出结果
    print("=== 日冕环振荡拟合结果 ===")
    print(f"A (振幅) = {A_fit:.3f} km")
    print(f"ω (角频率) = {omega_fit:.3f} rad/s")
    print(f"P (周期) = {P_fit:.3f} s")
    print(f"φ (相位) = {phi_fit:.3f} rad")
    print(f"B_estimate (日冕磁场估计) = {B_estimate:.3e} T")
    
    return A_fit, omega_fit, phi_fit, P_fit, B_estimate

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='日冕环振荡拟合（U(1) 周期性）')
    parser.add_argument('--data', type=str, default='../data/coronal_loop_sim.csv', help='数据文件路径')
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    fit_coronal_loop_oscillation(args.data)

if __name__ == '__main__':
    main()
