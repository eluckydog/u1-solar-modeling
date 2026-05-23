#!/usr/bin/env python3
"""
测试 coronal_loop_oscillation.py
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'code'))

import numpy as np
import csv
from coronal_loop_oscillation import coronal_loop_oscillation, fit_coronal_loop_oscillation

def test_coronal_loop_oscillation():
    """测试日冕环振荡公式"""
    # 测试已知输入
    A = 1.0
    omega = 2 * np.pi / 60.0  # 周期 60s
    phi = 0.0
    
    # t = 0 时，sin(0) = 0，所以 d(0) = 0
    result = coronal_loop_oscillation(0, A, omega, phi)
    expected = 0.0
    assert np.isclose(result, expected, atol=1e-6), f"t=0 错误: {result} != {expected}"
    
    # t = T/4 时，sin(π/2) = 1，所以 d(T/4) = A
    T = 2 * np.pi / omega
    result = coronal_loop_oscillation(T/4, A, omega, phi)
    expected = A
    assert np.isclose(result, expected, atol=1e-6), f"t=T/4 错误: {result} != {expected}"
    
    print("✅ test_coronal_loop_oscillation passed")

def test_fit_coronal_loop_oscillation():
    """测试日冕环振荡拟合"""
    data_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'coronal_loop_sim.csv')
    A_fit, omega_fit, phi_fit, P_fit, B_estimate = fit_coronal_loop_oscillation(data_file)
    
    # 检查拟合结果是否合理
    assert 0 < A_fit < 10, f"振幅不合理: {A_fit}"
    assert 0 < omega_fit < 1, f"角频率不合理: {omega_fit}"
    assert 0 < P_fit < 1000, f"周期不合理: {P_fit}"
    assert 0 < B_estimate < 1e-6, f"日冕磁场估计不合理: {B_estimate}"
    
    print("✅ test_fit_coronal_loop_oscillation passed")

if __name__ == '__main__':
    test_coronal_loop_oscillation()
    test_fit_coronal_loop_oscillation()
    print("=== 所有测试通过 ===")
