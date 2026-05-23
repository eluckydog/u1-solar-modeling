#!/usr/bin/env python3
"""
测试 solar_cycle.py
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'code'))

import numpy as np
import csv
from solar_cycle import solar_cycle, fit_solar_cycle

def test_solar_cycle():
    """测试太阳活动周期公式"""
    # 测试已知输入
    R0 = 50.0
    A = 100.0
    T = 11.0
    phi = 0.0
    
    # t = 0 时，sin(0) = 0，所以 R(0) = R0
    result = solar_cycle(0, R0, A, T, phi)
    expected = R0
    assert np.isclose(result, expected, atol=1e-6), f"t=0 错误: {result} != {expected}"
    
    # t = T/4 时，sin(π/2) = 1，所以 R(T/4) = R0 + A
    result = solar_cycle(T/4, R0, A, T, phi)
    expected = R0 + A
    assert np.isclose(result, expected, atol=1e-6), f"t=T/4 错误: {result} != {expected}"
    
    print("✅ test_solar_cycle passed")

def test_fit_solar_cycle():
    """测试太阳活动周期拟合"""
    data_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'sunspot_number.csv')
    R0_fit, A_fit, T_fit, phi_fit = fit_solar_cycle(data_file)
    
    # 检查拟合结果是否合理
    assert 0 < R0_fit < 200, f"基线不合理: {R0_fit}"
    assert 0 < A_fit < 200, f"振幅不合理: {A_fit}"
    assert 9 < T_fit < 13, f"周期不合理: {T_fit}"  # 11 年周期 ±2 年
    
    print("✅ test_fit_solar_cycle passed")

if __name__ == '__main__':
    test_solar_cycle()
    test_fit_solar_cycle()
    print("=== 所有测试通过 ===")
