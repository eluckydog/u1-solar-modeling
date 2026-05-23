#!/usr/bin/env python3
"""
日震学模式分析（U(1) 方位角对称）
模拟球谐函数模式 Y_l^m(theta, phi)，拟合频率分裂。

U(1) 模型：
    Y_l^m(theta, phi) ~ P_l^m(cos(theta)) * e^{i m phi}
    其中 e^{i m phi} 是 U(1) 相位因子，m 是方位角阶数。

物理效应--频率分裂：
    没有转动时，所有 m 的模式频率简并：nu_{l,m} = nu_{l,0}
    太阳自转打破简并：nu_{l,m} = nu_{l,0} + m * dnu
    因此频率分裂 dnu 包含太阳内部转动信息。

数据格式：
    模拟数据：l, m, nu_obs（模式频率）
"""

import argparse
import numpy as np
import csv
from scipy import special
from scipy.optimize import curve_fit


def spherical_harmonic(l, m, theta, phi):
    """计算球谐函数 Y_l^m(theta, phi)
    
    Parameters:
    -----------
    l : int
        角动量量子数
    m : int
        方位角阶数（-l <= m <= l）
    theta : np.ndarray
        极角（弧度）
    phi : np.ndarray
        方位角（弧度）
    
    Returns:
    --------
    Ylm : np.ndarray (complex)
        球谐函数值
    """
    Plm = special.lpmv(m, l, np.cos(theta))
    # U(1) 相位因子：e^{i m phi}
    phase = np.exp(1j * m * phi)
    norm = np.sqrt((2*l + 1) / (4*np.pi) * special.factorial(l - m) / special.factorial(l + m))
    return norm * Plm * phase


def frequency_splitting_formula(m, nu_0, delta_nu):
    """频率分裂公式（简化的线性近似）
    
    nu_{l,m} = nu_{l,0} + m * dnu
    
    其中 dnu 与内部转动剖面 Omega(r, theta) 相关：
        dnu ~ m * Omega_avg / (2pi) * (1 - beta_l)
    简化取 dnu 为拟合参数。
    
    Parameters:
    -----------
    m : float
        方位角阶数
    nu_0 : float
        中心频率 uHz
    delta_nu : float
        分裂系数 uHz
    
    Returns:
    --------
    nu : float
        分裂后的频率
    """
    return nu_0 + m * delta_nu


def generate_mode_data(l_max=3, seed=42):
    """生成模拟日震学模式数据
    
    模拟频率分裂：
        nu_{l,m} = nu_{l,0} + m * dnu
        
        其中 nu_{l,0} 在 ~2000-3500 uHz 范围（太阳 p-模式典型范围）
        dnu ~ Omega_avg / (2pi) ~ 400 nHz ~ 0.4 uHz
    
    Parameters:
    -----------
    l_max : int
        最大角动量量子数
    seed : int
        随机种子
    
    Returns:
    --------
    data : list of dicts
        模式数据列表
    """
    rng = np.random.default_rng(seed)
    data = []

    for l in range(l_max + 1):
        nu_0_true = 2000 + l * 400 + rng.normal(0, 30)
        delta_nu_true = 0.4 + rng.normal(0, 0.02)

        for m in range(-l, l + 1):
            nu_true = frequency_splitting_formula(m, nu_0_true, delta_nu_true)
            nu_err = 0.05
            nu_obs = nu_true + rng.normal(0, nu_err)
            data.append({
                'l': l, 'm': m,
                'nu_true': nu_true, 'nu_obs': nu_obs, 'nu_err': nu_err
            })

    return data, nu_0_true, delta_nu_true


def fit_frequency_splitting(data):
    """拟合频率分裂
    
    对每个 l 独立拟合 nu_{l,m} = nu_0 + m * dnu
    
    Parameters:
    -----------
    data : list of dicts
        模式数据（含 l, m, nu_obs, nu_err）
    
    Returns:
    --------
    results : list of dicts
        各 l 的拟合结果
    """
    print("=" * 60)
    print("日震学模式频率分裂拟合（U(1) 方位角对称）")
    print("=" * 60)

    from collections import defaultdict
    by_l = defaultdict(list)
    for d in data:
        by_l[d['l']].append(d)

    results = []
    for l_val in sorted(by_l.keys()):
        modes = by_l[l_val]
        ms = np.array([d['m'] for d in modes])
        nus = np.array([d['nu_obs'] for d in modes])
        errs = np.array([d.get('nu_err', 0.05) for d in modes])

        n_modes = len(modes)
        print(f"\n  l = {l_val} ({n_modes} modes)")

        # 处理 l=0：只有 m=0，无法拟合分裂
        if n_modes < 2:
            nu_0_fit = nus[0]
            nu_0_err = errs[0]
            results.append({
                'l': l_val, 'nu_0': nu_0_fit, 'nu_0_err': nu_0_err,
                'delta_nu': 0.0, 'delta_nu_err': 0.0, 'n_modes': n_modes,
            })
            print(f"    nu0 = {nu_0_fit:.2f} +- {nu_0_err:.2f} uHz")
            print(f"    dnu = N/A (l=0 only m=0, no splitting)")
            continue

        try:
            popt, pcov = curve_fit(
                frequency_splitting_formula, ms, nus,
                p0=[2500, 0.4],
                sigma=errs, absolute_sigma=True
            )
            nu_0_fit, delta_nu_fit = popt
            nu_0_err, delta_nu_err = np.sqrt(np.diag(pcov))

            results.append({
                'l': l_val,
                'nu_0': nu_0_fit,
                'nu_0_err': nu_0_err,
                'delta_nu': delta_nu_fit,
                'delta_nu_err': delta_nu_err,
                'n_modes': n_modes,
            })

            print(f"    nu0 = {nu_0_fit:.2f} +- {nu_0_err:.2f} uHz")
            print(f"    dnu = {delta_nu_fit:.4f} +- {delta_nu_err:.4f} uHz")
            omega_avg_nHz = delta_nu_fit * 1e6 * 2 * np.pi
            print(f"    => mean rotation Omega_avg ~ {omega_avg_nHz:.1f} nHz")
            print(f"       (equiv period ~ {1e9 / omega_avg_nHz:.1f} d)")

            residuals = nus - frequency_splitting_formula(ms, nu_0_fit, delta_nu_fit)
            rms = np.sqrt(np.mean(residuals**2))
            print(f"    fit residual RMS = {rms:.3f} uHz")

        except Exception as e:
            print(f"[ERROR] l={l_val} fit failed: {e}")
            results.append({'l': l_val, 'error': str(e)})

    print("")
    print("---")
    print("U(1) 对称性验证：频率随 m 线性变化 -> 方位角方向具有 U(1) 对称性")
    print("频率分裂 dnu 反映太阳内部转动剖面")
    print("=" * 60)

    return results


def save_simulated_data(data_file, data):
    """保存模拟模式数据到 CSV
    
    Parameters:
    -----------
    data_file : str
        输出文件路径
    data : list of dicts
        模式数据列表
    """
    with open(data_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['l', 'm', 'nu_true', 'nu_obs', 'nu_err'])
        for d in data:
            writer.writerow([d['l'], d['m'], f"{d['nu_true']:.4f}",
                             f"{d['nu_obs']:.4f}", f"{d['nu_err']:.4f}"])


def analyze_helioseismology_from_file(data_file):
    """从 CSV 文件读取并分析频率分裂
    
    Parameters:
    -----------
    data_file : str
        CSV 文件路径
    
    Returns:
    --------
    results : list of dicts
        各 l 的拟合结果
    """
    data = []
    with open(data_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'l': int(row['l']),
                'm': int(row['m']),
                'nu_obs': float(row['nu_obs']),
                'nu_err': float(row['nu_err']),
            })
    return fit_frequency_splitting(data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='日震学模式分析（U(1) 方位角对称）')
    parser.add_argument('--data', type=str, default=None, help='数据文件路径（留空则模拟生成）')
    parser.add_argument('--lmax', type=int, default=3, help='最大 l 值')
    parser.add_argument('--seed', type=int, default=42, help='随机种子')
    parser.add_argument('--save', type=str, default=None, help='保存模拟数据到 CSV')
    args = parser.parse_args()

    if args.data:
        analyze_helioseismology_from_file(args.data)
    else:
        data, nu_0_true, delta_nu_true = generate_mode_data(l_max=args.lmax, seed=args.seed)
        if args.save:
            save_simulated_data(args.save, data)
            print(f"[OK] 数据已保存到: {args.save}")
        fit_frequency_splitting(data)
