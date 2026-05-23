#!/usr/bin/env python3
"""
磁场不稳定指数（U(1) 剪切分析）
基于磁场的 U(1) 方向对称性，计算不稳定指数。

三个指标：
    1. 剪切角指数 S_avg — 平均磁场剪切角
    2. U(1) 圆方差指数 V_circ — 相邻像素相位一致性
    3. 综合不稳定指数 Flare_Idx = S_avg * V_circ

物理背景：
    高剪切区（>60°）是耀斑活动的潜在区域。
    U(1) 相位散度大 → 磁场拓扑扭曲 → 能量释放概率高。
"""

import argparse
import numpy as np
import csv
from scipy.ndimage import generic_filter


def compute_phase_divergence(phi, kernel_size=5):
    """U(1) 圆方差：邻域内方位角散度
    
    对每个像素，计算其核窗口内相位分布的圆方差。
    圆方差 = 1 - R，其中 R = |平均相位向量|。
    R 接近 1 → 方向一致；R 接近 0 → 方向随机。
    
    Parameters:
    -----------
    phi : np.ndarray
        方位角 [-π, π]
    kernel_size : int
        核尺寸（奇数）
    
    Returns:
    --------
    div : np.ndarray
        圆方差图 [0, 1]
    """
    def _circular_variance(window):
        n = len(window)
        if n == 0:
            return 0.0
        sin_sum = np.sum(np.sin(window))
        cos_sum = np.sum(np.cos(window))
        R = np.sqrt(sin_sum**2 + cos_sum**2) / n
        return 1.0 - R
    
    return generic_filter(phi, _circular_variance, size=kernel_size)


def compute_flare_index(Bx, By, thresholds=(60, 0.5)):
    """计算综合不稳定指数
    
    Flare_Idx = S_norm * V_norm
    
    其中：
        S_norm = 高剪切占比（剪切角 > threshold_deg 的像素比例）
        V_norm = 高散度占比（圆方差 > threshold_var 的像素比例）
    
    Parameters:
    -----------
    Bx, By : np.ndarray
        磁场分量
    thresholds : tuple
        (剪切角阈值 deg, 圆方差阈值)
    
    Returns:
    --------
    results : dict
        不稳定指数结果
    """
    from vector_magnetic_field import compute_shear_angle
    
    shear_deg = thresholds[0]
    var_thresh = thresholds[1]
    
    # 1. 剪切角
    shear = compute_shear_angle(Bx, By)
    high_shear_frac = np.sum(shear > shear_deg) / shear.size
    
    # 2. U(1) 圆方差
    phi = np.arctan2(By, Bx)
    div = compute_phase_divergence(phi)
    high_div_frac = np.sum(div > var_thresh) / div.size
    
    # 3. 综合指数
    flare_idx = high_shear_frac * high_div_frac
    
    # 输出
    print("=" * 60)
    print("磁场不稳定指数分析")
    print("=" * 60)
    print(f"网格尺寸: {Bx.shape[1]} x {Bx.shape[0]} 像素")
    print(f"剪切阈值: {shear_deg} deg")
    print(f"散度阈值: {var_thresh}")
    print("")
    print("--- 指标 ---")
    print(f"S_avg (平均剪切角): {np.mean(shear):.1f} deg")
    print(f"S_high 比例 (> {shear_deg} deg): {high_shear_frac*100:.1f}%")
    print(f"V_circ 平均: {np.mean(div):.4f}")
    print(f"V_high 比例 (> {var_thresh}): {high_div_frac*100:.1f}%")
    print("")
    print("--- 不稳定指数 ---")
    discharge_levels = [(0, 0.01, '低'),
                        (0.01, 0.05, '中'),
                        (0.05, 0.15, '高'),
                        (0.15, 1.0, '极高')]
    level = [l for lo, hi, l in discharge_levels if lo <= flare_idx < hi]
    
    print(f"Flare_Idx = {flare_idx:.4f}  -> 不稳定等级: {level[0] if level else 'N/A'}")
    print(f"  公式: Flare_Idx = S_high_ratio * V_high_ratio")
    print("=" * 60)
    
    return {
        'shear': shear,
        'divergence': div,
        'high_shear_frac': high_shear_frac,
        'high_div_frac': high_div_frac,
        'flare_index': flare_idx,
        'level': level[0] if level else 'N/A',
    }


def analyze_from_file(data_file):
    """从 CSV 文件分析
    
    Parameters:
    -----------
    data_file : str
        CSV 路径（Bx, By, ...）
    
    Returns:
    --------
    results : dict
        分析结果
    """
    Bx_list = []
    By_list = []
    
    try:
        with open(data_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                Bx_list.append(float(row['Bx']))
                By_list.append(float(row['By']))
    except FileNotFoundError:
        print(f"[ERROR] 文件不存在: {data_file}")
        return None
    
    n = int(np.sqrt(len(Bx_list)))
    Bx = np.array(Bx_list).reshape(n, n)
    By = np.array(By_list).reshape(n, n)
    
    return compute_flare_index(Bx, By)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='磁场不稳定指数分析')
    parser.add_argument('--data', type=str, default=None, help='CSV 文件路径')
    parser.add_argument('--nx', type=int, default=64)
    parser.add_argument('--ny', type=int, default=64)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    
    if args.data:
        analyze_from_file(args.data)
    else:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from vector_magnetic_field import generate_magnetic_field_data
        Bx, By, phi = generate_magnetic_field_data(args.nx, args.ny, args.seed)
        compute_flare_index(Bx, By)
