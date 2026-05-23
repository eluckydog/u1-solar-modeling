#!/usr/bin/env python3
"""
自转相位活动日历（Carrington 坐标系）
将黑子/事件映射到太阳自转相位，识别活动经度。

原理：
    太阳自转周期 ~27.27 天（Carrington 自转）。
    某些经度区的活动概率是其他区的 3-5 倍（活动经度）。
    
    将每月黑子数按时间换算为 Carrington 相位：
        φ_rot = 2π * (t - t₀) / P_rot  (mod 2π)
    
    叠加多年的活动 → 相位概率密度 → 活动经度识别。

输出：
    - 活动经度相位分布
    - 活跃区数量（显著性）
    - 当前最活跃经度区间
"""

import argparse
import numpy as np
import csv
import os


# Carrington 自转参数
CARRINGTON_PERIOD = 27.2753  # 天
CARRINGTON_EPOCH = 1853.0     # Carrington 编号 1 起始年

# 太阳赤道自转（deg/day，与 solar_rotation 一致）
EQUATORIAL_ROTATION = 14.5  # deg/day → ~24.8 天极区周期


# 共享工具函数: 从 hilbert_phase 导入以避免重复
from prediction.hilbert_phase import read_sunspot_csv  # noqa: F401


def time_to_carrington_phase(year):
    """时间 → Carrington 自转相位 φ ∈ [0, 2π)
    
    相位 0 对应 Carrington 经度 0（太阳正面中央）。
    
    Parameters:
    -----------
    year : float
        儒略年
    
    Returns:
    --------
    phase : float
        自转相位 [0, 2π)
    """
    days_since_epoch = (year - CARRINGTON_EPOCH) * 365.25
    phase_rad = 2 * np.pi * days_since_epoch / CARRINGTON_PERIOD
    return phase_rad % (2 * np.pi)


def build_phase_activity_map(years, ssn, nbins=36):
    """建立自转相位活动分布图
    
    对每个时间点：
        1. 计算自转相位 φ_rot
        2. 按相位累加黑子数（权重）
    
    Parameters:
    -----------
    years : np.ndarray
        时间（年）
    ssn : np.ndarray
        黑子数
    nbins : int
        相位区间数（默认 36 = 10°/bin）
    
    Returns:
    --------
    results : dict
        活动分布结果
    """
    bin_edges = np.linspace(0, 2 * np.pi, nbins + 1)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    activity_sum = np.zeros(nbins)
    activity_count = np.zeros(nbins)
    
    for i in range(len(years)):
        phase = time_to_carrington_phase(years[i])
        idx = np.digitize(phase, bin_edges[:-1]) - 1
        idx = min(idx, nbins - 1)
        activity_sum[idx] += ssn[i]
        activity_count[idx] += 1.0
    
    # 平均活动/相位区间
    mean_activity = np.divide(activity_sum, activity_count,
                              out=np.zeros_like(activity_sum),
                              where=activity_count > 0)
    
    # 背景活动（均匀分布期望）
    bg_activity = np.mean(mean_activity)
    
    # 活动经度显著性
    activity_ratio = mean_activity / bg_activity
    max_ratio_idx = np.argmax(activity_ratio)
    max_ratio = activity_ratio[max_ratio_idx]
    
    # 托内方差（Circular variance of activity）
    # 高值 → 活动集中在某些相位
    sin_sum = np.sum(mean_activity * np.sin(bin_centers))
    cos_sum = np.sum(mean_activity * np.cos(bin_centers))
    R = np.sqrt(sin_sum**2 + cos_sum**2) / np.sum(mean_activity)
    circular_var = 1 - R  # 0=均匀, 1=完全集中
    
    # 输出
    print("=" * 60)
    print("自转相位活动日历（Carrington 坐标系）")
    print("=" * 60)
    print(f"数据跨度: {years[0]:.0f} - {years[-1]:.0f}")
    print(f"相位区间: {360/nbins:.1f} deg/bin")
    print(f"总样本: {len(years)} 个月")
    print("")
    print("--- 活动经度分布 ---")
    print(f"最大活动经度: {np.degrees(bin_centers[max_ratio_idx]):.0f} deg" +
          f"  (是背景的 {max_ratio:.2f} 倍)")
    print(f"最小活动经度: {np.degrees(bin_centers[np.argmin(activity_ratio)]):.0f} deg" +
          f"  (是背景的 {np.min(activity_ratio):.2f} 倍)")
    print(f"圆方差: {circular_var:.4f}" +
          f"  ({'活动分散' if circular_var < 0.2 else '存在活动经度'})")
    print("")
    
    # 找显著性活动经度区间
    threshold = bg_activity * 1.2  # 比背景高 20%
    active_bins = np.where(mean_activity > threshold)[0]
    print(f"显著活动经度区间 (>20% 背景): {len(active_bins)}/{nbins} 个区间")
    if len(active_bins) > 0:
        active_deg = np.degrees(bin_centers[active_bins])
        print(f"  相位范围: {active_deg[0]:.0f} - {active_deg[-1]:.0f} deg")
    
    # 当前自转相位
    t_now = years[-1]
    phase_now = time_to_carrington_phase(t_now)
    now_deg = np.degrees(phase_now)
    now_idx = np.digitize(phase_now, bin_edges[:-1]) - 1
    now_idx = min(now_idx, nbins - 1)
    current_activity_ratio = activity_ratio[now_idx]
    print("")
    print(f"当前 (t={t_now:.0f}): 自转相位 = {now_deg:.0f} deg")
    print(f"  当前区间活动比 = {current_activity_ratio:.2f}x 背景")
    print(f"  -> {'活动经度活跃' if current_activity_ratio > 1.2 else '安静经度' if current_activity_ratio < 0.8 else '中等'}")
    print("=" * 60)
    
    return {
        'bin_edges': bin_edges,
        'bin_centers': bin_centers,
        'mean_activity': mean_activity,
        'activity_sum': activity_sum,
        'activity_count': activity_count,
        'activity_ratio': activity_ratio,
        'circular_var': circular_var,
        'max_ratio_idx': max_ratio_idx,
        'max_ratio': max_ratio,
        'phase_now': phase_now,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='自转相位活动日历')
    parser.add_argument('--data', type=str, required=True, help='黑子数据 CSV')
    parser.add_argument('--nbins', type=int, default=36, help='相位区间数')
    args = parser.parse_args()
    
    years, ssn = read_sunspot_csv(args.data)
    if years is not None and ssn is not None:
        build_phase_activity_map(years, ssn, nbins=args.nbins)
