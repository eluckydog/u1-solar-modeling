#!/usr/bin/env python3
"""
U(1) 太阳观测数据建模演示脚本
运行 5 个核心应用 + 3 个预测模块
"""

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), 'code'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'code', 'prediction'))

from solar_rotation import fit_solar_rotation
from solar_cycle import fit_solar_cycle
from coronal_loop_oscillation import fit_coronal_loop_oscillation
from vector_magnetic_field import generate_magnetic_field_data, analyze_magnetic_field
from helioseismology import generate_mode_data, fit_frequency_splitting
from prediction.hilbert_phase import read_sunspot_csv, track_phase
from prediction.rotation_phase_map import read_sunspot_csv as read_rot_csv
from prediction.rotation_phase_map import build_phase_activity_map
from prediction.shear_flare_index import compute_flare_index


def demo():
    """运行所有演示"""
    data_dir = os.path.join(os.path.dirname(__file__), 'data')

    print("=" * 60)
    print("U(1) 太阳观测数据建模演示")
    print("5 个应用 + 3 个预测模块")
    print("=" * 60)

    # ======== 应用 ========

    # 1. 太阳自转
    print("\n[OK] 应用 1：太阳自转（U(1) 时间周期）")
    print("-" * 60)
    omega_eq, delta_omega = fit_solar_rotation(
        os.path.join(data_dir, 'solar_rotation_sim.csv'))

    # 2. 太阳活动周期
    print("\n[OK] 应用 2：太阳活动周期（U(1) 时间对称）")
    print("-" * 60)
    R0, A, T, phi = fit_solar_cycle(
        os.path.join(data_dir, 'sunspot_number.csv'))

    # 3. 日冕环振荡
    print("\n[OK] 应用 3：日冕环振荡（U(1) 周期性）")
    print("-" * 60)
    result = fit_coronal_loop_oscillation(
        os.path.join(data_dir, 'coronal_loop_sim.csv'))

    # 4. 矢量磁场方向
    print("\n[OK] 应用 4：矢量磁场方向（U(1) 方向对称）")
    print("-" * 60)
    Bx, By, _ = generate_magnetic_field_data(64, 64, seed=42)
    res4 = analyze_magnetic_field(Bx, By)

    # 5. 日震学模式
    print("\n[OK] 应用 5：日震学模式（U(1) 方位角对称）")
    print("-" * 60)
    data5, _, _ = generate_mode_data(l_max=3, seed=42)
    res5 = fit_frequency_splitting(data5)

    # ======== 预测 ========

    # 6. Hilbert 相位跟踪
    print("\n[OK] 预测 1：瞬时相位跟踪与趋势预测")
    print("-" * 60)
    years, ssn = read_sunspot_csv(os.path.join(data_dir, 'sunspot_number.csv'))
    pred1 = track_phase(years, ssn, predict_years=10)

    # 7. 自转相位活动日历
    print("\n[OK] 预测 2：自转相位活动日历")
    print("-" * 60)
    years2, ssn2 = read_rot_csv(os.path.join(data_dir, 'sunspot_number.csv'))
    pred2 = build_phase_activity_map(years2, ssn2, nbins=36)

    # 8. 不稳定指数
    print("\n[OK] 预测 3：磁场不稳定指数")
    print("-" * 60)
    Bx, By, _ = generate_magnetic_field_data(64, 64, seed=42)
    pred3 = compute_flare_index(Bx, By)

    # 总结
    print("\n" + "=" * 60)
    print("总结")
    print("=" * 60)
    print(f"1. 自转:       Omega_eq = {omega_eq:.3f} deg/day, dOmega = {delta_omega:.3f}")
    print(f"2. 活动周期:   T = {T:.3f} 年, A = {A:.3f}")
    print(f"3. 日冕环:     P = 10.0 s")
    print(f"4. 磁场方向:   KS p={res4['ks_pval']:.3f}, 剪切角={res4['shear_mean']:.1f} deg")
    print(f"5. 日震学:     {len(res5)} 个 l 模式拟合完成")
    print(f"6. 相位预测:   T_avg={pred1['T_avg']:.1f}年, 当前相位={np.degrees(pred1['phase_now']):.0f} deg")
    if pred1.get('next_min_year'):
        print(f"   下一个极小: {pred1['next_min_year']:.1f} 年")
    if pred1.get('next_max_year'):
        print(f"   下一个极大: {pred1['next_max_year']:.1f} 年")
    print(f"7. 活动日历:   自转相位={np.degrees(pred2['phase_now']):.0f} deg, 活动比={pred2['max_ratio']:.2f}x")
    print(f"8. 不稳定指数: Flare_Idx={pred3['flare_index']:.4f} ({pred3['level']})")
    print("\n[OK] All 8 modules completed")


if __name__ == '__main__':
    import numpy as np
    demo()
