#!/usr/bin/env python3
"""
瞬时相位跟踪（Hilbert 变换）
从黑子数据提取 U(1) 瞬时相位 φ(t) → 预测下一个极小/极大年。

原理：
    黑子数据是窄带信号（主周期 ~11 年）。
    Hilbert 变换提取瞬时相位 φ(t) ∈ [0, 2π)，
    跟踪其在 U(1) 圆上的位置，外推未来极小/极大。

输出：
    - 当前相位 φ_now (deg)
    - 下一个极小（φ=0）的预测年份
    - 下一个极大（φ=π）的预测年份
"""

import argparse
import numpy as np
import csv
from scipy.signal import hilbert, butter, filtfilt


# ============ 共享数据工具函数 ============

def read_sunspot_csv(data_file):
    """读取黑子数据
    
    另见: rotation_phase_map (re-exports this same function)
    test_prediction (tests both imports)
    
    Parameters:
    -----------
    data_file : str
        CSV 路径（year, month, sunspot_number）
    
    Returns:
    --------
    years : np.ndarray
        时间（年，浮点）
    ssn : np.ndarray
        黑子数
    """
    years = []
    ssn = []
    try:
        with open(data_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                t = float(row['year']) + float(row['month']) / 12.0
                years.append(t)
                ssn.append(float(row['sunspot_number']))
    except FileNotFoundError:
        print(f"[ERROR] 文件不存在: {data_file}")
        return None, None
    except Exception as e:
        print(f"[ERROR] 读取失败: {e}")
        return None, None
    
    return np.array(years), np.array(ssn)


def bandpass_filter(ssn, low_freq=1/15, high_freq=1/8, fs=12):
    """带通滤波保留太阳周期频段（8-15 年）
    
    Parameters:
    -----------
    ssn : np.ndarray
        原始黑子数（月度）
    low_freq : float
        低频截止（1/15 cycles/year ≈ 15 年周期）
    high_freq : float
        高频截止（1/8 cycles/year ≈ 8 年周期）
    fs : float
        采样率（12 samples/year = 月度数据）
    
    Returns:
    --------
    ssn_filtered : np.ndarray
        滤波后的黑子数
    """
    nyquist = fs / 2
    low = low_freq / nyquist
    high = high_freq / nyquist
    b, a = butter(4, [low, high], btype='band')
    return filtfilt(b, a, ssn)


def track_phase(years, ssn, predict_years=5):
    """跟踪瞬时相位并预测
    
    Parameters:
    -----------
    years : np.ndarray
        时间数组（年）
    ssn : np.ndarray
        黑子数
    predict_years : float
        预测未来年数
    
    Returns:
    --------
    results : dict
        相位跟踪和预测结果
    """
    # 1. 带通滤波
    ssn_filt = bandpass_filter(ssn)
    
    # 2. Hilbert 变换 → 解析信号
    analytic = hilbert(ssn_filt)
    phase = np.angle(analytic)  # [-π, π]
    amplitude = np.abs(analytic)
    
    # 3. 解卷绕相位（去跳变）
    phase_unwrapped = np.unwrap(phase)
    
    # 4. 对相位做线性拟合 → 平均角频率 ω_avg
    # 相位 ≈ ω_avg * t + φ_0
    coeffs = np.polyfit(years, phase_unwrapped, 1)
    omega_avg = coeffs[0]      # rad/year
    phi_0 = coeffs[1]          # rad
    
    T_avg = 2 * np.pi / omega_avg  # 平均周期（年）
    
    # 5. 当前相位（折叠到 [0, 2π)）
    phase_now = phase_unwrapped[-1]
    phase_now_mod = phase_now % (2 * np.pi)
    
    # 当前年份
    t_now = years[-1]
    
    # 6. 预测下一个极小（φ ≡ 0 mod 2π）和极大（φ ≡ π mod 2π）
    # φ_unwrapped(t) = ω_avg * t + φ_0
    # 下一个极小：φ_unwrapped(t) = 2π * k, k = ceil(phase_now / 2π)
    
    k_now = phase_now / (2 * np.pi)
    
    next_min_years = []
    next_max_years = []
    
    k_min = int(np.ceil(k_now))
    k_max = int(np.ceil(k_now - 0.5))  # π 是半个周期
    
    for k in [k_min, k_min + 1]:
        t = (0 - phi_0 + 2 * np.pi * k) / omega_avg
        if t > t_now + 1e-6:
            next_min_years.append(t)
            break
    
    for k in [k_max, k_max + 1]:
        t = (np.pi - phi_0 + 2 * np.pi * k) / omega_avg
        if t > t_now + 1e-6:
            next_max_years.append(t)
            break
    
    # 也预测第25周期极大（如果当前是周期24-25的过渡期）
    cycle_25_max = None
    if next_min_years and next_max_years:
        # 假设次序：...极小 → 极大 → 极小...
        # 最接近的两个预测
        pass
    
    next_min = next_min_years[0] if next_min_years else None
    next_max = next_max_years[0] if next_max_years else None
    
    # 7. 输出
    print("=" * 60)
    print("瞬时相位跟踪（Hilbert 变换）")
    print("=" * 60)
    print(f"数据时间跨度: {years[0]:.0f} - {years[-1]:.0f} ({len(years)} 个月)")
    print(f"平均周期 T_avg = {T_avg:.3f} 年")
    print(f"当前相位 (t={t_now:.0f}): {np.degrees(phase_now_mod):.1f} deg")
    print(f"  -> {'极小附近' if phase_now_mod < 0.5 or phase_now_mod > 5.8 else '上升期' if phase_now_mod < 2.5 else '极大附近' if abs(phase_now_mod - np.pi) < 0.5 else '下降期'}")
    if next_min:
        delta_min = next_min - t_now
        print(f"预测下一个极小: {next_min:.1f} 年 ({delta_min:.1f} 年后)")
    if next_max:
        delta_max = next_max - t_now
        print(f"预测下一个极大: {next_max:.1f} 年 ({delta_max:.1f} 年后)")
    print("=" * 60)
    
    return {
        'years': years,
        'ssn_filtered': ssn_filt,
        'phase': phase,
        'phase_unwrapped': phase_unwrapped,
        'amplitude': amplitude,
        'omega_avg': omega_avg,
        'T_avg': T_avg,
        'phase_now': phase_now_mod,
        'next_min_year': next_min,
        'next_max_year': next_max,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='瞬时相位跟踪与预测')
    parser.add_argument('--data', type=str, required=True, help='黑子数据 CSV')
    parser.add_argument('--predict', type=float, default=5, help='预测未来年数')
    args = parser.parse_args()
    
    years, ssn = read_sunspot_csv(args.data)
    if years is not None and ssn is not None:
        track_phase(years, ssn, predict_years=args.predict)
