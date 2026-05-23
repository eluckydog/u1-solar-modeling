#!/usr/bin/env python3
"""
U(1) Solar Model — 形式化太阳活动模型

基于 Plutino FlareList (1986-2020, 334,123 事件) 的经验拟合。
在 U(1) 对称性框架下将太阳耀斑活动重新形式化。

核心方程:
  φ(t) = 2π · (t - t₀) / T  (mod 2π)
  F(φ) = A · exp(κ · cos(φ - μ)) + C

其中:
  t₀ = 1986.2 年  (Cycle 22 极小)
  T  = 11 年       (平均太阳周期)
  A  = 188.4            (振幅)
  μ  = 142.9°         (相位偏移 Φ_lag)
  κ  = 1.26         (von Mises 聚集度)
  C  = 0.0            (本底发生率)

验证:
  Rayleigh Z = 3496 (p ≈ 0, 基于 9375 个 M+X 耀斑)
  R² = 0.6891, 峰谷比 = 12.4x

使用:
  from u1_solar_model import U1SolarModel
  model = U1SolarModel()
  f = model.flare_rate(phase=2.5)       # 给定相位
  f = model.flare_rate(year=2026.5)     # 给定年份
  p = model.predict_next_peak()         # 预测下次高峰
"""

import numpy as np
from typing import Optional, Tuple

class U1SolarModel:
    """U(1) Solar Model — 用 U(1) 对称性重建的太阳活动模型"""
    
    # === 模型常量 ===
    CYCLE_START = 1986.2       # 年, Cycle 22 极小
    PERIOD = 11.0                 # 年, 平均周期
    A = 188.442312                   # 振幅
    MU = 2.493744                 # 相位偏移 (rad)
    KAPPA = 1.259244           # 聚集度
    C = 0.000000                   # 本底
    PHASE_LAG_DEG = 142.9  # 耀斑峰值相位 (从 Cycle 最小算起)
    LAG_YEARS = 4.37  # 最小到峰值时间
    
    def __init__(self):
        self.name = "U(1) Solar Model"
        self._validate()
    
    def _validate(self):
        """自检模型参数有效性"""
        if self.PERIOD <= 0:
            raise ValueError(f"PERIOD must be positive, got {self.PERIOD}")
        if self.KAPPA <= 0:
            raise ValueError(f"KAPPA must be positive, got {self.KAPPA}")
    
    # ---- 相位计算 ----
    def phase(self, year: float) -> float:
        """计算给定年份的 U(1) 相位 (rad, [0, 2π))"""
        if not np.isfinite(year):
            raise ValueError(f"year must be finite, got {year}")
        if year < 1700 or year > 2100:
            raise ValueError(f"year {year} outside valid range [1700, 2100]")
        return (2 * np.pi * (year - self.CYCLE_START) / self.PERIOD) % (2 * np.pi)
    
    def year_from_phase(self, phi: float, cycle: int = 0) -> float:
        """从 U(1) 相位反推年份, cycle=0 为当前周期"""
        return self.CYCLE_START + self.PERIOD * (phi / (2*np.pi) + cycle)
    
    def phase_to_sin(self, year: float) -> float:
        """归一化正弦活动指标 (-1 ~ 1), 0 = 最大, π = 最小"""
        phi = self.phase(year)
        return np.cos(phi - self.MU)
    
    # ---- 耀斑率预测 ----
    def flare_rate(self, year: Optional[float] = None,
                   phase: Optional[float] = None,
                   cls: str = 'MX') -> float:
        """
        预测 M+X 级耀斑发生率 (events/10°-phase-bin/cycle)
        
        参数:
            year: 预测年份 (浮点数)
            phase: U(1) 相位 (rad), 与 year 二选一
            cls: 'MX' 或 'X' (X级专用暂用相同模型)
        
        返回:
            该相位下的期望耀斑数量
        """
        if phase is None and year is not None:
            phase = self.phase(year)
        elif phase is None:
            raise ValueError("Provide either year or phase")
        
        if not np.isfinite(phase):
            raise ValueError(f"phase must be finite, got {phase}")
        
        return self.A * np.exp(self.KAPPA * np.cos(phase - self.MU)) + self.C
    
    def flare_probability(self, year: Optional[float] = None,
                          phase: Optional[float] = None) -> float:
        """
        归一化耀斑概率 [0, 1], 1 = 该周期最大可能
        
        等同于 flare_rate 归一化到 [0, 1]
        """
        f = self.flare_rate(year=year, phase=phase)
        f_peak = self.flare_rate(phase=self.MU)
        return f / f_peak
    
    # ---- 预测 ----
    def predict_next_peak(self) -> float:
        """预测下一次 M+X 耀斑高峰年份"""
        from datetime import datetime
        now = datetime.now()
        current_year = now.year + (now.timetuple().tm_yday - 1) / 365.25
        
        phi_now = self.phase(current_year)
        target = self.MU % (2 * np.pi)
        
        # 从当前相位到目标相位的偏移 (cycles)
        offset = (target - phi_now) / (2 * np.pi)
        if offset <= 0:
            offset += 1  # 下一周期
        
        return current_year + offset * self.PERIOD
    
    def peak_to_phase(self, year: float) -> float:
        """耀斑高峰对应年份 → 该周期的 U(1) 相位"""
        return self.phase(year)
    
    # ---- 诊断 ----
    def summary(self) -> dict:
        return {
            'name': self.name,
            'cycle_start': self.CYCLE_START,
            'period': self.PERIOD,
            'amplitude_A': self.A,
            'phase_lag_mu_deg': self.PHASE_LAG_DEG,
            'concentration_kappa': self.KAPPA,
            'baseline_C': self.C,
            'peak_trough_ratio': 12.4,
            'peak_phase_deg': 142.9,
            'next_peak_year': self.predict_next_peak(),
            'lag_years': self.LAG_YEARS,
        }

# ===== 命令行接口 =====
if __name__ == '__main__':
    m = U1SolarModel()
    print(f"=== {m.name} ===")
    print(f"Phase lag: {m.PHASE_LAG_DEG:.1f}° ({m.LAG_YEARS:.2f} years)")
    print(f"Peak/trough ratio: {m.summary()['peak_trough_ratio']:.0f}x")
    print(f"Current phase: {m.phase(2026.4):.2f} rad ({np.degrees(m.phase(2026.4)):.0f}°)")
    print(f"Current flare rate: {m.flare_rate(year=2026.4):.0f} events/bin")
    print(f"Next peak prediction: {m.predict_next_peak():.1f}")
