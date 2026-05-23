#!/usr/bin/env python3
"""
U(1) 太阳观测数据建模演示脚本
运行 3 个核心应用（太阳自转、活动周期、日冕环振荡）
"""

import sys
import os

# 添加 code/ 到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'code'))

from solar_rotation import fit_solar_rotation
from solar_cycle import fit_solar_cycle
from coronal_loop_oscillation import fit_coronal_loop_oscillation

def demo():
    """运行所有演示"""
    print("=" * 60)
    print("U(1) 太阳观测数据建模演示")
    print("=" * 60)
    
    # 1. 太阳自转拟合
    print("\n【应用 1】太阳自转（U(1) 时间周期）")
    print("-" * 60)
    data_file_1 = os.path.join(os.path.dirname(__file__), 'data', 'solar_rotation_sim.csv')
    omega_eq, delta_omega = fit_solar_rotation(data_file_1)
    
    # 2. 太阳活动周期拟合
    print("\n【应用 2】太阳活动周期（U(1) 时间对称）")
    print("-" * 60)
    data_file_2 = os.path.join(os.path.dirname(__file__), 'data', 'sunspot_number.csv')
    R0, A, T, phi = fit_solar_cycle(data_file_2)
    
    # 3. 日冕环振荡拟合
    print("\n【应用 3】日冕环振荡（U(1) 周期性）")
    print("-" * 60)
    data_file_3 = os.path.join(os.path.dirname(__file__), 'data', 'coronal_loop_sim.csv')
    A_fit, omega_fit, phi_fit, P_fit, B_estimate = fit_coronal_loop_oscillation(data_file_3)
    
    # 总结
    print("\n" + "=" * 60)
    print("总结")
    print("=" * 60)
    print(f"1. 太阳自转: Ω_eq = {omega_eq:.3f} deg/day, ΔΩ = {delta_omega:.3f} deg/day")
    print(f"2. 太阳活动周期: T = {T:.3f} 年, A = {A:.3f}")
    print(f"3. 日冕环振荡: P = {P_fit:.3f} s, B_estimate = {B_estimate:.3e} T")
    print("\n[OK] All applications completed")

if __name__ == '__main__':
    demo()
