#!/usr/bin/env python3
"""
矢量磁场方向分析（U(1) 方向对称）
计算磁场方位角 φ = arctan2(By, Bx)，分析极坐标分布和剪切角。

U(1) 相位模型：
    磁场方位角 φ ∈ [0, 2π) 是一个 U(1) 变量。
    转 2π 回来，方向不变。

物理应用：
    1. 磁场剪切角 → 耀斑预测（剪切 > 60 deg → 高概率爆发）
    2. 极性反转 → 太阳周期
    3. 方向分布均匀性 → 发电机模型验证

数据格式：
    模拟数据：Bx, By（光球磁场横向分量）
"""

import argparse
import numpy as np
import csv
import os


def generate_magnetic_field_data(nx=64, ny=64, seed=42):
    """生成模拟矢量磁图数据
    
    模型：高斯随机场 + 大尺度结构（活动区偶极子）
    
    Parameters:
    -----------
    nx, ny : int
        网格尺寸（arcsec 像素）
    seed : int
        随机种子
    
    Returns:
    --------
    Bx, By : np.ndarray
        横向磁场分量（Gauss）
    phi : np.ndarray
        方位角（弧度，[-π, π]）
    """
    rng = np.random.default_rng(seed)

    # 1. 小尺度随机噪声（湍流）
    noise_level = 50  # Gauss
    Bx_noise = rng.normal(0, noise_level, (ny, nx))
    By_noise = rng.normal(0, noise_level, (ny, nx))

    # 2. 大尺度活动区结构（两个极性相反的偶极子）
    xx, yy = np.meshgrid(np.arange(nx), np.arange(ny))
    cx1, cy1 = nx // 3, ny // 2       # 第一个活动区中心
    cx2, cy2 = 2 * nx // 3, ny // 2   # 第二个活动区中心
    sigma = nx // 8                    # 活动区尺度

    # 偶极子：从中心向外辐射的磁场
    r1 = np.sqrt((xx - cx1)**2 + (yy - cy1)**2)
    r2 = np.sqrt((xx - cx2)**2 + (yy - cy2)**2)

    # 径向分量（用高斯包络）
    B_strength = 500  # Gauss
    Bx_large = (
        -B_strength * (xx - cx1) / (sigma + r1) * np.exp(-r1**2 / (2 * sigma**2))
        + B_strength * (xx - cx2) / (sigma + r2) * np.exp(-r2**2 / (2 * sigma**2))
    )
    By_large = (
        -B_strength * (yy - cy1) / (sigma + r1) * np.exp(-r1**2 / (2 * sigma**2))
        + B_strength * (yy - cy2) / (sigma + r2) * np.exp(-r2**2 / (2 * sigma**2))
    )

    Bx = Bx_noise + Bx_large
    By = By_noise + By_large
    phi = np.arctan2(By, Bx)  # [-pi, pi]

    return Bx, By, phi


def compute_shear_angle(Bx, By, kernel_size=3):
    """计算磁场剪切角（相邻像素方向差）
    
    剪切角 = 相邻像素磁场方位角的绝对差
    高剪切区域（>60 deg）是耀斑活动的潜在区域。
    
    Parameters:
    -----------
    Bx, By : np.ndarray
        磁场分量
    kernel_size : int
        卷积核尺寸（默认为 3×3）
    
    Returns:
    --------
    shear_map : np.ndarray
        剪切角图（度）
    """
    from scipy.ndimage import generic_filter

    phi = np.arctan2(By, Bx)

    def _mean_angular_diff(window):
        """窗口内平均方位角差"""
        center = window[len(window) // 2]
        # 计算角度差，处理周期性
        diffs = np.arctan2(np.sin(window - center), np.cos(window - center))
        return np.mean(np.abs(diffs))

    shear_map = generic_filter(phi, _mean_angular_diff, size=kernel_size)
    return np.degrees(shear_map)


def analyze_magnetic_field(Bx, By, nbins=36):
    """分析矢量磁场方向分布
    
    Parameters:
    -----------
    Bx, By : np.ndarray
        磁场分量
    nbins : int
        方位角直方图 bin 数
    
    Returns:
    --------
    results : dict
        分析结果
    """
    phi = np.arctan2(By, Bx)
    B_total = np.sqrt(Bx**2 + By**2)

    # 1. 方位角极坐标分布
    hist, bin_edges = np.histogram(phi, bins=nbins, range=(-np.pi, np.pi))
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0

    # 2. 方向均匀性检验（KS 检验 vs 均匀分布）
    from scipy import stats
    # phi 范围 [-pi, pi]，均匀分布对应的 CDF
    uniform_cdf = stats.uniform(loc=-np.pi, scale=2*np.pi)
    ks_stat, ks_pval = stats.kstest(phi.flatten(), uniform_cdf.cdf)

    # 3. 平均方向（矢量平均）
    mean_bx = np.mean(Bx)
    mean_by = np.mean(By)
    mean_phi = np.arctan2(mean_by, mean_bx)
    mean_B = np.sqrt(mean_bx**2 + mean_by**2)

    # 4. 剪切角分布
    shear_map = compute_shear_angle(Bx, By)
    shear_mean = np.mean(shear_map)
    shear_std = np.std(shear_map)
    shear_high_fraction = np.sum(shear_map > 60) / shear_map.size * 100  # 高剪切占比

    # 5. 磁能密度分布
    energy = B_total**2  # B^2 ∝ 能量
    energy_total = np.sum(energy)

    # 输出
    print("=" * 60)
    print("矢量磁场方向分析（U(1) 方向对称）")
    print("=" * 60)
    print(f"网格尺寸: {Bx.shape[1]} x {Bx.shape[0]} 像素")
    print(f"方位角 bins: {nbins} ({360/nbins:.1f} deg/bin)")
    print("")
    print("--- 方向统计 ---")
    print(f"平均方向 (矢量平均): {np.degrees(mean_phi):.1f} deg")
    print(f"平均磁场强度: {mean_B:.1f} G")
    print(f"方位角均匀性 KS 检验: stat={ks_stat:.4f}, p={ks_pval:.4f}")
    if ks_pval > 0.05:
        print("  -> 方向分布无明显偏离均匀（p > 0.05）")
    else:
        print("  -> 方向分布存在显著结构（p < 0.05）")
    print("")
    print("--- 剪切分析 ---")
    print(f"平均剪切角: {shear_mean:.1f} deg")
    print(f"剪切角标准差: {shear_std:.1f} deg")
    print(f"高剪切区域 (>60 deg): {shear_high_fraction:.1f}%")
    print("")
    print("--- 能量 ---")
    print(f"总磁能密度: {energy_total:.3e} G^2")
    print("=" * 60)

    results = {
        'phi': phi,
        'B_total': B_total,
        'hist': hist,
        'bin_centers': bin_centers,
        'mean_phi': mean_phi,
        'mean_B': mean_B,
        'ks_stat': ks_stat,
        'ks_pval': ks_pval,
        'shear_map': shear_map,
        'shear_mean': shear_mean,
        'shear_std': shear_std,
        'shear_high_fraction': shear_high_fraction,
        'energy_total': energy_total,
    }

    return results


def save_simulated_data(data_file, Bx, By, seed=42):
    """保存模拟数据到 CSV
    
    Parameters:
    -----------
    data_file : str
        输出文件路径
    Bx, By : np.ndarray
        磁场分量
    seed : int
        随机种子
    """
    ny, nx = Bx.shape
    with open(data_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['x', 'y', 'Bx', 'By', 'B_total', 'phi_deg'])
        for i in range(ny):
            for j in range(nx):
                phi_deg = np.degrees(np.arctan2(By[i, j], Bx[i, j]))
                B_total = np.sqrt(Bx[i, j]**2 + By[i, j]**2)
                writer.writerow([j, i, f"{Bx[i,j]:.2f}", f"{By[i,j]:.2f}",
                                 f"{B_total:.2f}", f"{phi_deg:.1f}"])


def analyze_magnetic_field_from_file(data_file):
    """从 CSV 文件读取并分析磁场数据
    
    Parameters:
    -----------
    data_file : str
        CSV 文件路径
    
    Returns:
    --------
    results : dict
        分析结果
    """
    Bx_list = []
    By_list = []

    with open(data_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            Bx_list.append(float(row['Bx']))
            By_list.append(float(row['By']))

    # 假设是方形网格
    n = int(np.sqrt(len(Bx_list)))
    Bx = np.array(Bx_list).reshape(n, n)
    By = np.array(By_list).reshape(n, n)

    return analyze_magnetic_field(Bx, By)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='矢量磁场方向分析（U(1) 方向对称）')
    parser.add_argument('--data', type=str, default=None, help='数据文件路径（留空则生成模拟数据）')
    parser.add_argument('--nx', type=int, default=64, help='x 网格尺寸')
    parser.add_argument('--ny', type=int, default=64, help='y 网格尺寸')
    parser.add_argument('--seed', type=int, default=42, help='随机种子')
    parser.add_argument('--save', type=str, default=None, help='保存模拟数据到 CSV')
    args = parser.parse_args()

    if args.data:
        analyze_magnetic_field_from_file(args.data)
    else:
        Bx, By, phi = generate_magnetic_field_data(args.nx, args.ny, args.seed)
        if args.save:
            save_simulated_data(args.save, Bx, By, args.seed)
            print(f"[OK] 数据已保存到: {args.save}")
        analyze_magnetic_field(Bx, By)
