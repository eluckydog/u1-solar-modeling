#!/usr/bin/env python3
"""
测试 solar_rotation.py
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'code'))

import numpy as np
import csv
from solar_rotation import differential_rotation, fit_solar_rotation

def test_differential_rotation():
    """测试较差自转公式"""
    # 测试赤道（θ=0）
    omega_eq = 14.5
    delta_omega = 3.5
    result = differential_rotation(0, omega_eq, delta_omega)
    expected = omega_eq  # sin(0)=0
    assert np.isclose(result, expected, atol=1e-6), f"赤道角速度错误: {result} != {expected}"
    
    # 测试极区（θ=90）
    result = differential_rotation(90, omega_eq, delta_omega)
    expected = omega_eq - delta_omega  # sin(90°)=1
    assert np.isclose(result, expected, atol=1e-6), f"极区角速度错误: {result} != {expected}"
    
    print("✅ test_differential_rotation passed")

def test_fit_solar_rotation():
    """测试太阳自转拟合"""
    data_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'solar_rotation_sim.csv')
    omega_eq_fit, delta_omega_fit = fit_solar_rotation(data_file)
    
    # 检查拟合结果是否合理
    assert 14.0 < omega_eq_fit < 15.0, f"赤道角速度不合理: {omega_eq_fit}"
    assert 2.0 < delta_omega_fit < 3.0, f"纬度差不合理: {delta_omega_fit}"
    
    print("✅ test_fit_solar_rotation passed")

if __name__ == '__main__':
    test_differential_rotation()
    test_fit_solar_rotation()
    print("=== 所有测试通过 ===")
