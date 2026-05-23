#!/usr/bin/env python3
"""
测试 coronal_loop_oscillation.py
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'code'))

import numpy as np
import csv
from coronal_loop_oscillation import coronal_loop_oscillation, estimate_b_field, fit_coronal_loop_oscillation

class TestCoronalLoopOscillation:
    """测试日冕环振荡公式"""
    
    def test_amplitude(self):
        """测试振幅"""
        t = np.linspace(0, 100, 1000)
        A = 5.0
        omega = 2 * np.pi / 10.0  # 10s 周期
        phi = 0.0
        d = coronal_loop_oscillation(t, A, omega, phi)
        assert np.isclose(np.max(d), A, atol=0.01), f"振幅错误: {np.max(d)} != {A}"
    
    def test_maximum(self):
        """测试最大值"""
        t = np.linspace(0, 100, 1000)
        A = 5.0
        omega = 2 * np.pi / 10.0
        phi = 0.0
        d = coronal_loop_oscillation(t, A, omega, phi)
        assert np.isclose(np.max(d), A, atol=0.01), f"最大值错误: {np.max(d)} != {A}"
    
    def test_minimum(self):
        """测试最小值"""
        t = np.linspace(0, 100, 1000)
        A = 5.0
        omega = 2 * np.pi / 10.0
        phi = 0.0
        d = coronal_loop_oscillation(t, A, omega, phi)
        assert np.isclose(np.min(d), -A, atol=0.01), f"最小值错误: {np.min(d)} != {-A}"
    
    def test_periodicity(self):
        """测试周期性"""
        t = np.linspace(0, 100, 1000)
        A = 5.0
        omega = 2 * np.pi / 10.0  # 10s 周期
        phi = 0.0
        d = coronal_loop_oscillation(t, A, omega, phi)
        # 检查周期性：d(t + T) 应与 d(t) 近似相等
        T = 2 * np.pi / omega
        # 在多个时间点检查周期性
        for t0 in [1.0, 5.0, 12.7, 30.0]:
            idx1 = np.searchsorted(t, t0)
            idx2 = np.searchsorted(t, t0 + T)
            if idx1 < len(t) and idx2 < len(t):
                assert np.isclose(d[idx1], d[idx2], atol=0.05), f"t={t0} 周期性错误: {d[idx1]} != {d[idx2]}"
    
    def test_phase_shift(self):
        """测试相位偏移"""
        t = np.linspace(0, 100, 1000)
        A = 5.0
        omega = 2 * np.pi / 10.0
        phi1 = 0.0
        phi2 = np.pi / 2.0
        d1 = coronal_loop_oscillation(t, A, omega, phi1)
        d2 = coronal_loop_oscillation(t, A, omega, phi2)
        # 相位偏移 π/2 应该使正弦变余弦
        assert np.isclose(d1[0], 0.0, atol=0.01), f"相位 0 错误: {d1[0]} != 0"
        assert np.isclose(d2[0], A, atol=0.01), f"相位 π/2 错误: {d2[0]} != {A}"
    
    def test_zero_amplitude(self):
        """测试零振幅"""
        t = np.linspace(0, 100, 1000)
        A = 0.0
        omega = 2 * np.pi / 10.0
        phi = 0.0
        d = coronal_loop_oscillation(t, A, omega, phi)
        assert np.allclose(d, 0.0), f"零振幅错误: {d}"

class TestFitCoronalLoopOscillation:
    """测试日冕环振荡拟合"""
    
    def test_fit_simulated_data(self):
        """测试模拟数据拟合"""
        # 生成模拟数据
        t = np.linspace(0, 120, 1200)
        A_true = 5.0
        omega_true = 2 * np.pi / 10.0  # 10s 周期
        phi_true = 0.0
        d = coronal_loop_oscillation(t, A_true, omega_true, phi_true)
        
        # 保存为 CSV
        data_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'coronal_loop_sim.csv')
        with open(data_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['time', 'displacement'])
            for i in range(len(t)):
                writer.writerow([t[i], d[i]])
        
        # 拟合
        A_fit, omega_fit, phi_fit = fit_coronal_loop_oscillation(data_file, data_type='simulated')
        
        # 检查拟合参数
        assert A_fit is not None, "拟合失败"
        assert np.isclose(A_fit, A_true, rtol=0.1), f"振幅拟合错误: {A_fit} != {A_true}"
        assert np.isclose(omega_fit, omega_true, rtol=0.1), f"频率拟合错误: {omega_fit} != {omega_true}"
    
    def test_file_not_found(self):
        """测试文件不存在"""
        A_fit, omega_fit, phi_fit = fit_coronal_loop_oscillation('nonexistent.csv')
        assert A_fit is None, "文件不存在时应返回 None"
    
    def test_empty_file(self):
        """测试空文件"""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('time,displacement\n')
            temp_file = f.name
        
        A_fit, omega_fit, phi_fit = fit_coronal_loop_oscillation(temp_file)
        assert A_fit is None, "空文件拟合应失败"
        
        os.unlink(temp_file)
    
    def test_b_field_estimate(self):
        """测试磁场强度估算"""
        A = 5.0  # km
        omega = 2 * np.pi / 10.0  # rad/s
        B = estimate_b_field(A, omega)
        assert B > 0, f"磁场强度应 > 0: {B}"
        assert B < 2000, f"磁场强度应 < 2000 G: {B}"

if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
