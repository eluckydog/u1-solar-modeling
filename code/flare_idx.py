#!/usr/bin/env python3
"""
flare_idx.py — U(1) Flare_Idx 空间验证模块
=========================================
基于真实 HMI SHARP CEA 矢量磁图计算磁场拓扑不稳定指数。

核心概念:
  Flare_Idx = 高剪切占比 × U(1) 圆方差
  其中:
  - 高剪切占比 = 同极性内与中值方向夹角 > 60° 的像素比例
  - U(1) 圆方差 = 水平磁场方向在 U(1) 圆上的混乱度 (1-R), 0=完全对齐, 1=完全随机
  - Flare_Idx_v2 = 高剪切占比 × 圆方差 × (1 + 剪切部分圆方差)
    加入剪切部分的方向混乱度加权, 捕获"高剪切区域的拓扑复杂度"

支持:
  - SHARP CEA FITS (hmi.sharp_cea_720s: Bp/Bt/Br 格式)
  - M_720s LOS 磁图 (仅测试 Bz)
  - numpy 数组直接注入

用法:
  from flare_idx import compute_flare_idx_from_sharp
  
  # SHARP FITS
  result = compute_flare_idx_from_sharp(bp_path, bt_path, br_path, bitmap_path)

参考:
  - MohamedNedal/calculating-spaceweather-keywords (M. Bobra 等的 SWx 参数)
  - dfouhey/sdodemo (miniSDO 降采样 Bx/By/Bz)
"""

import numpy as np
from astropy.io import fits
import os

__version__ = "1.0.0"

# ============================================================
# 读取 SHARP CEA FITS
# ============================================================

MAX_FITS_PIXELS = 100_000_000  # ~800MB for float64

def _read_sharp_cea(path):
    """
    读取 SHARP CEA FITS, 自动处理 HDU 索引差异。
    返回 (data, header)
    
    安全限制: 拒绝 NAXIS1*NAXIS2 > MAX_FITS_PIXELS 的大文件。
    """
    hdul = fits.open(path)
    for i in range(len(hdul)):
        h = hdul[i]
        if h.data is not None and h.header.get('NAXIS', 0) == 2:
            npix = h.header.get('NAXIS1', 0) * h.header.get('NAXIS2', 0)
            if npix > MAX_FITS_PIXELS:
                hdul.close()
                raise ValueError(
                    f"FITS too large: {h.header['NAXIS1']}x{h.header['NAXIS2']} "
                    f"({npix} pixels, max {MAX_FITS_PIXELS})"
                )
            data = h.data.astype(np.float64)
            header = h.header
            hdul.close()
            return data, header
    hdul.close()
    raise ValueError(f"No 2D data found in {path}")


def load_sharp_vector(bp_path, bt_path, br_path, bitmap_path):
    """
    加载 SHARP CEA 矢量磁图全套数据。
    
    参数:
        bp_path: str — Bp (phi-component, Bx) FITS 路径
        bt_path: str — Bt (theta-component, By) FITS 路径
        br_path: str — Br (radial, Bz) FITS 路径
        bitmap_path: str — bitmap FITS 路径 (AR 掩膜)
    
    返回:
        dict: {bx, by, bz, bitmap, header, shape, n_active}
    """
    bp, hdr = _read_sharp_cea(bp_path)
    bt, _ = _read_sharp_cea(bt_path)
    br, _ = _read_sharp_cea(br_path)
    bitmap, _ = _read_sharp_cea(bitmap_path)
    
    # 确保尺寸一致
    if not (bp.shape == bt.shape == br.shape == bitmap.shape):
        raise ValueError(
            f"Shape mismatch: Bp={bp.shape}, Bt={bt.shape}, "
            f"Br={br.shape}, bitmap={bitmap.shape}"
        )
    
    mask = bitmap > 0
    
    return {
        'bx': bp, 'by': bt, 'bz': br,
        'bitmap': bitmap.astype(int),
        'header': hdr,
        'shape': bp.shape,
        'n_active': int(mask.sum()),
    }


# ============================================================
# 核心 Flare_Idx 计算
# ============================================================

def compute_flare_idx(bx, by, bz, mask=None):
    """
    计算 U(1) Flare_Idx。
    
    参数:
        bx, by, bz: ndarray — 磁场分量 (任意单位, 只需方向一致)
        mask: ndarray, optional — 布尔掩膜 (例如活动区像素)
    
    返回:
        dict:
          - mean_shear_deg: 同极性内与中值方向的平均偏离角 (°)
          - high_shear_frac: 剪切角 > 60° 的占比
          - circ_variance: U(1) 圆方差 (1-R), 水平方向混乱度
          - circ_variance_sheared: 剪切部分的圆方差
          - flare_idx: 原始 Flare_Idx = high_shear_frac × circ_variance
          - flare_idx_v2: 增强版 Flare_Idx = orig × (1 + circ_variance_sheared)
          - level: 不稳定等级 (稳定/注意/耀斑潜力/活跃)
    
    物理:
        Flare_Idx 测量"磁场在这个区域内有多乱":
        - 高剪切占比 → 磁能储存了多少 (场强差异大)
        - 圆方差     → 储存的磁能能否集中释放 (方向混乱)
        两者乘积 = 耀斑潜力。
    """
    # 掩膜
    if mask is not None:
        Bx = bx[mask].copy()
        By = by[mask].copy()
        Bz = bz[mask].copy()
    else:
        Bx, By, Bz = bx.copy(), by.copy(), bz.copy()
    
    # 去除无效值
    valid = (~np.isnan(Bx)) & (~np.isnan(By)) & (~np.isnan(Bz))
    Bx, By, Bz = Bx[valid], By[valid], Bz[valid]
    
    if len(Bx) < 10:
        return None
    
    # 场强
    B = np.sqrt(Bx**2 + By**2 + Bz**2)
    B[B < 1] = 1  # 避免方向除以极小的场
    
    # 单位方向矢量
    ux, uy, uz = Bx/B, By/B, Bz/B
    
    # ===== 极性分离分析 =====
    pos = Bz > 0
    neg = Bz < 0
    
    all_shear = np.array([], dtype=np.float64)
    all_phi = np.array([], dtype=np.float64)
    high_shear_flags = np.array([], dtype=bool)
    
    for polarity_mask, label in [(pos, '+'), (neg, '-')]:
        n = polarity_mask.sum()
        if n < 5:
            continue
        
        pu = ux[polarity_mask]
        pv = uy[polarity_mask]
        pw = uz[polarity_mask]
        pp = Bx[polarity_mask]  # for phi computation
        
        # 中值方向
        um = np.median(pu)
        vm = np.median(pv)
        wm = np.median(pw)
        nm = np.sqrt(um**2 + vm**2 + wm**2)
        if nm > 0:
            um /= nm; vm /= nm; wm /= nm
        else:
            continue
        
        # 剪切角
        dot = np.clip(pu*um + pv*vm + pw*wm, -1, 1)
        shear = np.degrees(np.arccos(dot))
        
        # 水平方向 (U(1) 圆)
        phi = np.arctan2(pp, By[polarity_mask])
        
        all_shear = np.concatenate([all_shear, shear])
        all_phi = np.concatenate([all_phi, phi])
        high_shear_flags = np.concatenate([high_shear_flags, shear > 60])
    
    if len(all_shear) < 10:
        return None
    
    # ===== 统计量 =====
    mean_shear = float(np.mean(all_shear))
    high_shear_frac = float(np.mean(high_shear_flags))
    
    # U(1) 圆方差 (所有像素)
    cos_phi = np.cos(all_phi)
    sin_phi = np.sin(all_phi)
    R = np.sqrt(np.sum(cos_phi)**2 + np.sum(sin_phi)**2) / len(all_phi)
    circ_var = float(1 - R)
    
    # 剪切部分的圆方差
    hs = high_shear_flags
    if hs.sum() > 1:
        cos_h = np.cos(all_phi[hs])
        sin_h = np.sin(all_phi[hs])
        Rh = np.sqrt(np.sum(cos_h)**2 + np.sum(sin_h)**2) / hs.sum()
        circ_var_s = float(1 - Rh)
    else:
        circ_var_s = 0.0
    
    # Flare_Idx
    fi = high_shear_frac * circ_var
    fi_v2 = fi * (1 + circ_var_s)
    
    # 分级 (基于 AR 11092 验证)
    if fi_v2 < 0.15:
        level = "低 (稳定)"
    elif fi_v2 < 0.30:
        level = "中 (注意)"
    elif fi_v2 < 0.50:
        level = "高 (耀斑潜力)"
    else:
        level = "极高 (活跃)"
    
    return {
        'n_pixels': len(all_shear),
        'mean_shear_deg': round(mean_shear, 1),
        'high_shear_frac': round(high_shear_frac, 4),
        'circ_variance': round(circ_var, 4),
        'circ_variance_sheared': round(circ_var_s, 4),
        'flare_idx': round(fi, 4),
        'flare_idx_v2': round(fi_v2, 4),
        'level': level,
    }


def compute_flare_idx_from_sharp(bp_path, bt_path, br_path, bitmap_path):
    """
    便捷函数: 从 SHARP CEA FITS 文件路径计算 Flare_Idx。
    
    返回: 同 compute_flare_idx 的 dict
    """
    data = load_sharp_vector(bp_path, bt_path, br_path, bitmap_path)
    mask = data['bitmap'] > 0
    return compute_flare_idx(data['bx'], data['by'], data['bz'], mask)


# ============================================================
# 命令行
# ============================================================

def print_report(result, title=""):
    """格式化输出 Flare_Idx 报告"""
    if result is None:
        print("  [!] 无法计算 (像素太少)")
        return
    
    lines = [
        f"  {'='*45}",
        f"  {title}" if title else "",
        f"  {'='*45}",
        f"  活动区像素    : {result['n_pixels']}",
        f"  平均剪切角 (°) : {result['mean_shear_deg']}",
        f"  高剪切占比     : {result['high_shear_frac']*100:.2f}%",
        f"  U(1) 圆方差   : {result['circ_variance']}",
        f"  剪切圆方差     : {result['circ_variance_sheared']}",
        f"  ───────────────────────────────",
        f"  Flare_Idx     : {result['flare_idx']}",
        f"  Flare_Idx v2  : {result['flare_idx_v2']}",
        f"  不稳定等级     : {result['level']}",
        f"  {'='*45}",
    ]
    print('\n'.join(l for l in lines if l))


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 5:
        r = compute_flare_idx_from_sharp(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
        print_report(r)
    else:
        # Demo: 从已知测试文件运行 (使用相对路径)
        _script_dir = os.path.dirname(os.path.abspath(__file__))
        d = os.path.join(_script_dir, '..', 'data', 'hmi')
        bp = os.path.join(d, 'hmi.sharp_cea_720s.377.20110215_020000_TAI.Bp.fits')
        bt = os.path.join(d, 'hmi.sharp_cea_720s.377.20110215_020000_TAI.Bt.fits')
        br = os.path.join(d, 'hmi.sharp_cea_720s.377.20110215_020000_TAI.Br.fits')
        bm = os.path.join(d, 'hmi.sharp_cea_720s.377.20110215_020000_TAI.bitmap.fits')
        
        if not all(os.path.exists(p) for p in [bp, bt, br, bm]):
            print("[!] HMI FITS 未完全下载, 运行 generate_data 或从 MohamedNedal GitHub 获取")
        else:
            result = compute_flare_idx_from_sharp(bp, bt, br, bm)
            print_report(result, "AR 11092 (2011-02-15, X3.2 flare)")
