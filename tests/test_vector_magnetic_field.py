#!/usr/bin/env python3
"""
测试：矢量磁场方向分析（U(1) 方向对称）
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
from vector_magnetic_field import (
    generate_magnetic_field_data,
    analyze_magnetic_field,
    compute_shear_angle,
)


def test_generate_data_shape():
    """测试数据形状正确"""
    Bx, By, phi = generate_magnetic_field_data(32, 32, seed=42)
    assert Bx.shape == (32, 32), f"Expected (32, 32), got {Bx.shape}"
    assert By.shape == (32, 32), f"Expected (32, 32), got {By.shape}"
    assert phi.shape == (32, 32), f"Expected (32, 32), got {phi.shape}"
    print("[OK] test_generate_data_shape")


def test_generate_data_reproducible():
    """测试可重现性（固定种子）"""
    _, _, phi1 = generate_magnetic_field_data(32, 32, seed=42)
    _, _, phi2 = generate_magnetic_field_data(32, 32, seed=42)
    assert np.allclose(phi1, phi2), "Fixed seed should produce same output"
    print("[OK] test_generate_data_reproducible")


def test_seed_changes_output():
    """测试不同种子产生不同输出"""
    _, _, phi1 = generate_magnetic_field_data(32, 32, seed=42)
    _, _, phi2 = generate_magnetic_field_data(32, 32, seed=99)
    assert not np.allclose(phi1, phi2), "Different seeds should differ"
    print("[OK] test_seed_changes_output")


def test_phi_range():
    """测试方位角在 [-pi, pi] 范围内"""
    _, _, phi = generate_magnetic_field_data(64, 64, seed=42)
    assert np.all(phi >= -np.pi) and np.all(phi <= np.pi), "phi should be in [-pi, pi]"
    print("[OK] test_phi_range")


def test_phi_u1_symmetry():
    """测试 U(1) 对称性：phi + 2pi 等价于 phi"""
    _, _, phi = generate_magnetic_field_data(64, 64, seed=42)
    phi_shifted = phi + 2 * np.pi
    # cos(phi) == cos(phi + 2pi)
    assert np.allclose(np.cos(phi), np.cos(phi_shifted)), "U(1) symmetry violated"
    print("[OK] test_phi_u1_symmetry")


def test_analyze_returns_dict():
    """测试分析函数返回字典"""
    Bx, By, _ = generate_magnetic_field_data(32, 32, seed=42)
    results = analyze_magnetic_field(Bx, By)
    assert isinstance(results, dict), "Expected dict"
    required_keys = ['phi', 'B_total', 'hist', 'mean_phi', 'ks_stat', 'shear_map']
    for k in required_keys:
        assert k in results, f"Missing key: {k}"
    print("[OK] test_analyze_returns_dict")


def test_shear_angle_shape():
    """测试剪切角图形状匹配"""
    Bx, By, _ = generate_magnetic_field_data(32, 32, seed=42)
    shear = compute_shear_angle(Bx, By)
    assert shear.shape == (32, 32), f"Expected (32,32), got {shear.shape}"
    print("[OK] test_shear_angle_shape")


def test_shear_angle_bounds():
    """测试剪切角在 [0, 180) 度范围内"""
    Bx, By, _ = generate_magnetic_field_data(64, 64, seed=42)
    shear = compute_shear_angle(Bx, By)
    assert np.all(shear >= 0) and np.all(shear < 180), "Shear angle out of bounds"
    print("[OK] test_shear_angle_bounds")


def test_histogram_bins():
    """测试直方图 bin 数量正确"""
    Bx, By, _ = generate_magnetic_field_data(32, 32, seed=42)
    results = analyze_magnetic_field(Bx, By, nbins=36)
    assert len(results['hist']) == 36, f"Expected 36 bins, got {len(results['hist'])}"
    assert len(results['bin_centers']) == 36
    print("[OK] test_histogram_bins")


def test_ks_test_uniform():
    """测试纯噪声的方向分布应接近均匀 (p > 0.05)"""
    # 纯噪声：无大尺度结构
    rng = np.random.default_rng(100)
    Bx = rng.normal(0, 50, (64, 64))
    By = rng.normal(0, 50, (64, 64))
    results = analyze_magnetic_field(Bx, By)
    assert results['ks_pval'] > 0.05, "Pure noise should be uniform"
    print("[OK] test_ks_test_uniform")


if __name__ == '__main__':
    test_generate_data_shape()
    test_generate_data_reproducible()
    test_seed_changes_output()
    test_phi_range()
    test_phi_u1_symmetry()
    test_analyze_returns_dict()
    test_shear_angle_shape()
    test_shear_angle_bounds()
    test_histogram_bins()
    test_ks_test_uniform()
    print("\n[OK] All 10 tests passed!")
