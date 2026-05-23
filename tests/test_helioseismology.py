#!/usr/bin/env python3
"""
测试：日震学模式分析（U(1) 方位角对称）
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
from helioseismology import (
    generate_mode_data,
    fit_frequency_splitting,
    frequency_splitting_formula,
    spherical_harmonic,
)


def test_generate_data_count():
    """测试生成的数据数量正确"""
    data, _, _ = generate_mode_data(l_max=2, seed=42)
    # l=0: 1 mode, l=1: 3 modes, l=2: 5 modes => total 9
    assert len(data) == 9, f"Expected 9 modes, got {len(data)}"
    print("[OK] test_generate_data_count")


def test_generate_data_keys():
    """测试数据包含必要字段"""
    data, _, _ = generate_mode_data(l_max=1, seed=42)
    for d in data:
        assert 'l' in d
        assert 'm' in d
        assert 'nu_obs' in d
        assert 'nu_err' in d
    print("[OK] test_generate_data_keys")


def test_generate_data_reproducible():
    """测试可重现性"""
    data1, _, _ = generate_mode_data(l_max=2, seed=42)
    data2, _, _ = generate_mode_data(l_max=2, seed=42)
    nu1 = [d['nu_obs'] for d in data1]
    nu2 = [d['nu_obs'] for d in data2]
    assert np.allclose(nu1, nu2), "Fixed seed should produce same output"
    print("[OK] test_generate_data_reproducible")


def test_m_range():
    """测试 m 在 [-l, l] 范围内"""
    data, _, _ = generate_mode_data(l_max=3, seed=42)
    for d in data:
        assert abs(d['m']) <= d['l'], f"m={d['m']} > l={d['l']}"
    print("[OK] test_m_range")


def test_frequency_splitting_formula_linear():
    """测试频率分裂是 m 的线性函数"""
    ms = np.array([-3, -2, -1, 0, 1, 2, 3])
    nus = frequency_splitting_formula(ms, 2000, 0.4)
    diffs = np.diff(nus)
    assert np.allclose(diffs, diffs[0]), "Should be linear in m"
    print("[OK] test_frequency_splitting_formula_linear")


def test_frequency_splitting_u1_symmetry():
    """测试 U(1) 对称性：m -> -m 对称（频率对 m=0 反对称）"""
    nu_0 = 2500
    dnu = 0.4
    nu_m3 = frequency_splitting_formula(-3, nu_0, dnu)
    nu_p3 = frequency_splitting_formula(3, nu_0, dnu)
    # nu(+3) - nu_0 = -(nu(-3) - nu_0)
    assert np.abs(nu_p3 - nu_0) == np.abs(nu_m3 - nu_0), "m -> -m symmetry violated"
    print("[OK] test_frequency_splitting_u1_symmetry")


def test_l0_handling():
    """测试 l=0 不会崩溃（只有 m=0）"""
    data, _, _ = generate_mode_data(l_max=0, seed=42)
    results = fit_frequency_splitting(data)
    # Allow print output but just check it returns
    assert len(results) > 0
    print("[OK] test_l0_handling")


def test_fit_recovers_true_params():
    """测试拟合能大致恢复真实参数"""
    data, true_nu0, true_dnu = generate_mode_data(l_max=2, seed=42)
    results = fit_frequency_splitting(data)
    for r in results:
        l_val = r['l']
        if l_val == 0:
            continue  # l=0 skips fitting
        if l_val >= 1:
            assert abs(r['delta_nu'] - true_dnu) < 0.1, f"l={l_val} dnu off: {r['delta_nu']} vs {true_dnu}"
    print("[OK] test_fit_recovers_true_params")


def test_spherical_harmonic_normalization():
    """测试球谐函数归一化"""
    theta = np.linspace(0.01, np.pi - 0.01, 100)
    phi = np.linspace(0, 2*np.pi, 100)
    TH, PH = np.meshgrid(theta, phi)
    Y = spherical_harmonic(2, 1, TH, PH)
    dtheta = theta[1] - theta[0]
    dphi = phi[1] - phi[0]
    integrand = np.abs(Y)**2 * np.sin(TH)
    norm = np.sum(integrand) * dtheta * dphi
    assert abs(norm - 1.0) < 0.15, f"Normalization off: {norm}"
    print("[OK] test_spherical_harmonic_normalization")


def test_spherical_harmonic_u1_phase():
    """测试 U(1) 相位因子：旋转 phi 后模方不变"""
    theta = np.array([0.5, 1.0, 1.5])
    phi1 = np.array([0.0, 1.0, 2.0])
    phi2 = np.array([2*np.pi, 1.0+2*np.pi, 2.0+2*np.pi])
    Y1 = spherical_harmonic(2, 1, theta, phi1)
    Y2 = spherical_harmonic(2, 1, theta, phi2)
    assert np.allclose(np.abs(Y1), np.abs(Y2)), "U(1) phase invariance violated"
    print("[OK] test_spherical_harmonic_u1_phase")


if __name__ == '__main__':
    test_generate_data_count()
    test_generate_data_keys()
    test_generate_data_reproducible()
    test_m_range()
    test_frequency_splitting_formula_linear()
    test_frequency_splitting_u1_symmetry()
    test_l0_handling()
    test_fit_recovers_true_params()
    test_spherical_harmonic_normalization()
    test_spherical_harmonic_u1_phase()
    print("\n[OK] All 10 tests passed!")
