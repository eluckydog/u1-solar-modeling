#!/usr/bin/env python3
"""测试 Dst 预测 + CME 传播模型"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code', 'prediction'))
import pytest
import numpy as np

# ===== Dst 模型 =====
from dst_model import burton_step, bz_south, classify_storm, estimate_recovery_time

def test_bz_south():
    assert bz_south(-5) == 5.0
    assert bz_south(5) == 0.0
    assert bz_south(0) == 0.0

def test_burton_quiet():
    d = burton_step(1.0, 330, 0.3, -1)
    assert -5 < d < 0

def test_burton_storm():
    d = burton_step(1.0, 500, 15.0, -10)
    assert d < -10  # Dst 下降

def test_burton_sustained_storm():
    d = -10
    for _ in range(6):
        d = burton_step(1.0, 600, 20.0, d)
    assert d < -150  # 持续强驱动 -> 强风暴

def test_burton_recovery():
    d = burton_step(1.0, 400, 0, -50)  # Bs=0, 只有恢复
    assert d > -50  # 回升

def test_classify_storm():
    assert 'G0' in classify_storm(-20)[0]
    assert 'G1' in classify_storm(-40)[0]
    assert 'G2' in classify_storm(-80)[0]
    assert 'G3' in classify_storm(-150)[0]
    assert 'G4' in classify_storm(-250)[0]
    assert 'G5' in classify_storm(-400)[0]

def test_recovery_time():
    t = estimate_recovery_time(-100)
    assert t > 0
    assert estimate_recovery_time(-20) == 0

# ===== CME 模型 =====
from cme_model import DragBasedModel as CME

def test_cme_init():
    c = CME(1000)
    assert c.v0 == 1000
    assert c.dv == 600  # 1000 - 400

def test_cme_tau():
    c = CME(1000)
    assert c.tau_hours > 0

def test_cme_no_drive():
    c = CME(300, vsw=400)  # 慢于背景风, 被 clamp 到 401
    assert c.v0 == 401
    assert c.tau_hours > 0

def test_cme_arrival_time():
    c = CME(1000)
    t = c.arrival_time()
    assert 20 < t < 100  # 合理的到达时间范围

def test_cme_corrected():
    c = CME(2000)
    t = c.arrival_time_corrected()
    assert 10 < t < 50  # 快速 CME 应更早到达

def test_cme_historical():
    """验证校正后与历史误差 < 30%"""
    cases = [(2500, 17.5), (1900, 19), (1800, 26), (700, 38)]
    for v0, known in cases:
        c = CME(v0)
        t = c.arrival_time_corrected()
        err = abs(t - known) / known * 100
        assert err < 30, f"V0={v0}: T={t:.0f}h, known={known:.0f}h, err={err:.0f}%"

def test_geomagnetic_potential():
    c = CME(2000)
    assert 0 <= c.geomagnetic_potential() <= 10

def test_halo_factor():
    ch = CME(500, halo=True)
    cn = CME(500, halo=False)
    assert ch.geomagnetic_potential() >= cn.geomagnetic_potential()
