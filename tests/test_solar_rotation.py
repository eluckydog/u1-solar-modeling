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

class TestDifferentialRotation:
    """测试较差自转公式"""
    
    def test_equator(self):
        """测试赤道（θ=0）"""
        omega_eq = 14.5
        delta_omega = 3.5
        result = differential_rotation(0, omega_eq, delta_omega)
        expected = omega_eq  # sin(0)=0
        assert np.isclose(result, expected, atol=1e-6), f"赤道角速度错误: {result} != {expected}"
    
    def test_pole(self):
        """测试极区（θ=90°）"""
        omega_eq = 14.5
        delta_omega = 3.5
        result = differential_rotation(np.pi/2, omega_eq, delta_omega)
        expected = omega_eq - delta_omega  # sin(π/2)=1
        assert np.isclose(result, expected, atol=1e-6), f"极区角速度错误: {result} != {expected}"
    
    def test_mid_latitude(self):
        """测试中纬度（θ=45°）"""
        omega_eq = 14.5
        delta_omega = 3.5
        result = differential_rotation(np.pi/4, omega_eq, delta_omega)
        expected = omega_eq - delta_omega * 0.5  # sin²(π/4)=0.5
        assert np.isclose(result, expected, atol=1e-6), f"中纬度角速度错误: {result} != {expected}"
    
    def test_negative_delta_omega(self):
        """测试负 Δω（反向较差自转）"""
        omega_eq = 14.5
        delta_omega = -3.5  # 极区转得更快
        result = differential_rotation(np.pi/4, omega_eq, delta_omega)
        expected = omega_eq - delta_omega * 0.5
        assert np.isclose(result, expected, atol=1e-6), f"负 Δω 错误: {result} != {expected}"
    
    def test_zero_delta_omega(self):
        """测试零 Δω（刚性自转）"""
        omega_eq = 14.5
        delta_omega = 0.0
        result = differential_rotation(np.pi/4, omega_eq, delta_omega)
        expected = omega_eq  # 所有纬度角速度相同
        assert np.isclose(result, expected, atol=1e-6), f"零 Δω 错误: {result} != {expected}"

class TestFitSolarRotation:
    """测试太阳自转拟合"""
    
    def test_fit_simulated_data(self):
        """测试模拟数据拟合"""
        # 生成模拟数据
        theta = np.linspace(0, np.pi/2, 50)
        omega_eq_true = 14.5
        delta_omega_true = 3.5
        omega = differential_rotation(theta, omega_eq_true, delta_omega_true)
        
        # 保存为 CSV
        data_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'solar_rotation_sim.csv')
        with open(data_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['latitude', 'omega'])
            for i in range(len(theta)):
                writer.writerow([theta[i], omega[i]])
        
        # 拟合
        omega_eq_fit, delta_omega_fit = fit_solar_rotation(data_file, data_type='simulated')
        
        # 检查拟合参数
        assert omega_eq_fit is not None, "拟合失败"
        assert np.isclose(omega_eq_fit, omega_eq_true, rtol=0.1), f"ω_eq 拟合错误: {omega_eq_fit} != {omega_eq_true}"
        assert np.isclose(delta_omega_fit, delta_omega_true, rtol=0.1), f"Δω 拟合错误: {delta_omega_fit} != {delta_omega_true}"
    
    def test_file_not_found(self):
        """测试文件不存在"""
        omega_eq_fit, delta_omega_fit = fit_solar_rotation('nonexistent.csv')
        assert omega_eq_fit is None, "文件不存在时应返回 None"
    
    def test_empty_file(self):
        """测试空文件"""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('latitude,omega\n')
            temp_file = f.name
        
        omega_eq_fit, delta_omega_fit = fit_solar_rotation(temp_file)
        assert omega_eq_fit is None, "空文件拟合应失败"
        
        os.unlink(temp_file)

if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
