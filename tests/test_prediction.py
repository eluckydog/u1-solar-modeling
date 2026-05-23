#!/usr/bin/env python3
"""
测试：预测模块（hilbert_phase, rotation_phase_map, shear_flare_index）
"""

import sys, os
import numpy as np

# 添加预测模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code', 'prediction'))

from prediction.hilbert_phase import read_sunspot_csv, track_phase, bandpass_filter
from prediction.rotation_phase_map import read_sunspot_csv as read_rot_csv
from prediction.rotation_phase_map import time_to_carrington_phase, build_phase_activity_map
from prediction.shear_flare_index import compute_flare_index, compute_phase_divergence


# ========== Hilbert Phase Tests ==========

def test_read_sunspot_success():
    """测试读取黑子数据"""
    years, ssn = read_sunspot_csv(
        os.path.join(os.path.dirname(__file__), '..', 'data', 'sunspot_number.csv'))
    assert years is not None, "读取失败"
    assert len(years) > 3000, f"数据点不足: {len(years)}"
    assert len(years) == len(ssn)
    print("[OK] test_read_sunspot_success")


def test_read_sunspot_not_found():
    """测试文件不存在"""
    years, ssn = read_sunspot_csv('nonexistent.csv')
    assert years is None
    print("[OK] test_read_sunspot_not_found")


def test_bandpass_filter_shape():
    """测试滤波器保持形状"""
    ssn = np.random.randn(1200)
    filtered = bandpass_filter(ssn)
    assert len(filtered) == len(ssn), "滤波改变形状"
    print("[OK] test_bandpass_filter_shape")


def test_track_phase_returns_keys():
    """测试相位跟踪返回正确字段"""
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    years, ssn = read_sunspot_csv(os.path.join(data_dir, 'sunspot_number.csv'))
    result = track_phase(years, ssn)
    required_keys = ['years', 'ssn_filtered', 'phase', 'amplitude', 
                     'omega_avg', 'T_avg', 'phase_now']
    for k in required_keys:
        assert k in result, f"缺字段: {k}"
    print("[OK] test_track_phase_returns_keys")


def test_track_phase_period_reasonable():
    """测试周期在合理范围（8-15 年）"""
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    years, ssn = read_sunspot_csv(os.path.join(data_dir, 'sunspot_number.csv'))
    result = track_phase(years, ssn)
    assert 8 < result['T_avg'] < 15, f"周期异常: {result['T_avg']}"
    print("[OK] test_track_phase_period_reasonable")


def test_track_phase_phase_range():
    """测试当前相位在 [0, 2π)"""
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    years, ssn = read_sunspot_csv(os.path.join(data_dir, 'sunspot_number.csv'))
    result = track_phase(years, ssn)
    phase = result['phase_now']
    assert 0 <= phase < 2 * np.pi, f"相位越界: {phase}"
    print("[OK] test_track_phase_phase_range")


# ========== Rotation Phase Map Tests ==========

def test_carrington_phase_range():
    """测试 Carrington 相位在 [0, 2π)"""
    phase = time_to_carrington_phase(2000.0)
    assert 0 <= phase < 2 * np.pi, f"相位越界: {phase}"
    print("[OK] test_carrington_phase_range")


def test_carrington_phase_periodic():
    """测试 Carrington 相位的周期性"""
    # 27 天后相位应变化 ~2π
    p1 = time_to_carrington_phase(2000.0)
    p2 = time_to_carrington_phase(2000.0 + 27.3/365.25)
    diff = (p2 - p1) % (2 * np.pi)
    assert np.isclose(diff, 0, atol=0.1), f"周期性误差: {diff}"
    print("[OK] test_carrington_phase_periodic")


def test_phase_activity_map_keys():
    """测试活动分布返回正确字段"""
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    years, ssn = read_rot_csv(os.path.join(data_dir, 'sunspot_number.csv'))
    result = build_phase_activity_map(years, ssn, nbins=18)
    required_keys = ['bin_centers', 'activity_ratio', 'circular_var', 'phase_now']
    for k in required_keys:
        assert k in result, f"缺字段: {k}"
    assert len(result['bin_centers']) == 18
    print("[OK] test_phase_activity_map_keys")


# ========== Shear Flare Index Tests ==========

def test_compute_phase_divergence_shape():
    """测试圆方差形状匹配"""
    np.random.seed(42)
    phi = np.random.uniform(-np.pi, np.pi, (32, 32))
    div = compute_phase_divergence(phi, kernel_size=3)
    assert div.shape == (32, 32), f"形状不匹配: {div.shape}"
    print("[OK] test_compute_phase_divergence_shape")


def test_phase_divergence_uniform():
    """测试均匀随机相位的圆方差接近 1"""
    np.random.seed(42)
    phi = np.random.uniform(-np.pi, np.pi, (64, 64))
    div = compute_phase_divergence(phi, kernel_size=5)
    mean_div = np.mean(div)
    assert mean_div > 0.5, f"均匀相位圆方差偏低: {mean_div}"
    print("[OK] test_phase_divergence_uniform")


def test_phase_divergence_aligned():
    """测试对齐相位的圆方差接近 0"""
    phi = np.zeros((32, 32))  # 所有方向相同
    div = compute_phase_divergence(phi, kernel_size=3)
    mean_div = np.mean(div)
    assert mean_div < 0.01, f"对齐相位圆方差偏高: {mean_div}"
    print("[OK] test_phase_divergence_aligned")


def test_compute_flare_index():
    """测试不稳定指数返回合理值"""
    np.random.seed(42)
    Bx = np.random.normal(0, 50, (32, 32))
    By = np.random.normal(0, 50, (32, 32))
    result = compute_flare_index(Bx, By)
    assert 'flare_index' in result
    assert 0 <= result['flare_index'] <= 1, f"Flare_Idx 越界: {result['flare_index']}"
    print("[OK] test_compute_flare_index")


if __name__ == '__main__':
    test_read_sunspot_success()
    test_read_sunspot_not_found()
    test_bandpass_filter_shape()
    test_track_phase_returns_keys()
    test_track_phase_period_reasonable()
    test_track_phase_phase_range()
    test_carrington_phase_range()
    test_carrington_phase_periodic()
    test_phase_activity_map_keys()
    test_compute_phase_divergence_shape()
    test_phase_divergence_uniform()
    test_phase_divergence_aligned()
    test_compute_flare_index()
    print("\n[OK] All 13 prediction tests passed!")
