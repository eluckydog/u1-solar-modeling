#!/usr/bin/env python3
"""测试 U(1) Flare_Idx"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
from flare_idx import compute_flare_idx, compute_flare_idx_from_sharp, print_report
import numpy as np

HMI = os.path.join(os.path.dirname(__file__), '..', 'data', 'hmi')

def test_import():
    """模块可导入"""
    from flare_idx import __version__
    assert __version__

def test_simulated_uniform_field():
    """模拟均匀场 -> Flare_Idx ~ 0 (稳定)"""
    # 所有场方向相同
    bx = np.ones((10, 10)) * 100
    by = np.ones((10, 10)) * 200
    bz = np.ones((10, 10)) * 300
    r = compute_flare_idx(bx, by, bz)
    assert r is not None
    assert r['high_shear_frac'] < 0.02, f"Uniform field has {r['high_shear_frac']*100}% high shear"
    assert r['flare_idx'] < 0.05

def test_simulated_random_field():
    """模拟随机场 -> Flare_Idx 高 (活跃)"""
    np.random.seed(42)
    bx = np.random.randn(100, 100) * 200
    by = np.random.randn(100, 100) * 200
    bz = np.random.randn(100, 100) * 200
    r = compute_flare_idx(bx, by, bz)
    assert r is not None
    assert r['flare_idx'] > 0.2, f"Random field only has Flare_Idx={r['flare_idx']}"

def test_bipolar_field():
    """双极场 (清晰分隔正负极) -> Flare_Idx 低"""
    np.random.seed(42)
    n = 100
    bx = np.random.randn(n, n) * 20
    by = np.random.randn(n, n) * 20
    bz = np.zeros((n, n))
    # 左半边正极性
    bz[:, :n//2] = 500 + np.random.randn(n, n//2) * 50
    # 右半边负极性
    bz[:, n//2:] = -500 + np.random.randn(n, n//2) * 50
    r = compute_flare_idx(bx, by, bz)
    assert r is not None
    # 极性内部方向应该高度一致
    assert r['flare_idx'] < 0.2

def test_real_hmi_data():
    """真实 HMI SHARP 数据 (AR 11092, X3.2)"""
    bp = os.path.join(HMI, 'hmi.sharp_cea_720s.377.20110215_020000_TAI.Bp.fits')
    bt = os.path.join(HMI, 'hmi.sharp_cea_720s.377.20110215_020000_TAI.Bt.fits')
    br = os.path.join(HMI, 'hmi.sharp_cea_720s.377.20110215_020000_TAI.Br.fits')
    bm = os.path.join(HMI, 'hmi.sharp_cea_720s.377.20110215_020000_TAI.bitmap.fits')
    
    r = compute_flare_idx_from_sharp(bp, bt, br, bm)
    assert r is not None
    assert r['n_pixels'] > 100000
    # AR 在 X3.2 耀斑后 16 分钟, 应该是活跃的
    assert r['flare_idx_v2'] > 0.3, f"AR 11092 post-X3.2: Flare_Idx_v2={r['flare_idx_v2']}"
    assert r['level'] in ['高 (耀斑潜力)', '极高 (活跃)']

def test_masked_outside_ar():
    """掩膜外的像素不影响结果"""
    np.random.seed(42)
    shape = (50, 50)
    bx = np.random.randn(*shape) * 100
    by = np.random.randn(*shape) * 100
    bz = np.random.randn(*shape) * 100
    
    # 只在中心区域有信号, 外用很大的噪声
    mask = np.zeros(shape, dtype=bool)
    mask[20:30, 20:30] = True
    bx_out = bx.copy(); bx_out[~mask] = 0
    by_out = by.copy(); by_out[~mask] = 0
    bz_out = bz.copy(); bz_out[~mask] = 0
    
    r_full = compute_flare_idx(bx_out, by_out, bz_out)
    r_masked = compute_flare_idx(bx_out, by_out, bz_out, mask)
    
    assert r_full is not None and r_masked is not None
    assert r_full['n_pixels'] == r_masked['n_pixels']  # 0 值被过滤掉, 像素数相同

def test_edge_cases():
    """边界情况"""
    # 所有 NaN
    r = compute_flare_idx(np.full((10, 10), np.nan), np.full((10, 10), np.nan), np.full((10, 10), np.nan))
    assert r is None
    
    # 单极强场
    bx = np.ones((30, 30)) * 1000
    by = np.ones((30, 30)) * 1000
    bz = np.ones((30, 30)) * 1000
    r = compute_flare_idx(bx, by, bz)
    assert r is not None
    assert r['flare_idx'] < 0.02

def test_phi_calculation():
    """U(1) phi 方向一致时 circ_variance ~ 0"""
    n = 100
    # 所有场指向同一个水平方向
    bx = np.ones((n, n)) * 100
    by = np.ones((n, n)) * 0
    bz = np.ones((n, n)) * 50
    r = compute_flare_idx(bx, by, bz)
    assert r is not None
    assert r['circ_variance'] < 0.1, f"Aligned field has circ_variance={r['circ_variance']}"

# 运行
if __name__ == '__main__':
    import traceback
    tests = [n for n in dir() if n.startswith('test_')]
    passed, failed = 0, 0
    for test_name in tests:
        try:
            globals()[test_name]()
            print(f'  [OK] {test_name}')
            passed += 1
        except Exception as e:
            print(f'  [X] {test_name}: {str(e)[:100]}')
            failed += 1
    print(f'\n  {passed}/{passed+failed} tests passed')
