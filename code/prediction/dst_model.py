#!/usr/bin/env python3
"""
dst_model.py — Burton 方程 Dst 预测模型
========================================
dDst/dt = a * V * Bs - b - Dst / tau

其中 Bs = max(-Bz_GSM, 0) 即南向 IMF 分量

物理:
  太阳风携带南向磁场 -> 磁重联 -> 环电流增强 -> Dst 下降
  V*Bs 是磁层-太阳风耦合的关键输入, 称为"驱动函数"

参数 (Burton et al. 1975, O'Brien & McPherron 2000):
  a  = -3.3e-5 nT/(km/s * nT * s)  (耦合效率)
  b  = -0.5 nT/s                    (常数损耗)
  tau = 4.0 h                       (环电流衰减时间常数)

输入: NOAA SWPC 实时数据 (太阳风等离子体 + IMF + 当前 Dst)
输出: Dst 预测 ±6h
"""
import numpy as np
import urllib.request, json
from datetime import datetime, timedelta, timezone
import os

__version__ = "1.0.0"

# 标准 Burton 参数 (O'Brien & McPherron 2000)
# dDst/dt = -a*(V/1000)*Bs - Dst/tau
# 其中 a=4.4 nT/hr, Bs=max(-Bz_GSM,0), tau=4-8hr
DEFAULT_A = 4.4        # nT/hr (耦合系数, 无量纲化后)
DEFAULT_TAU = 4.0      # 小时 (环电流衰减时间常数)

NOAA_PLASMA_URL = 'https://services.swpc.noaa.gov/products/solar-wind/plasma-1-day.json'
NOAA_MAG_URL    = 'https://services.swpc.noaa.gov/products/solar-wind/mag-1-day.json'
NOAA_DST_URL    = 'https://services.swpc.noaa.gov/products/kyoto-dst.json'


def fetch_json(url, timeout=15):
    """通用 NOAA API JSON 获取"""
    req = urllib.request.Request(url, headers={'User-Agent': 'DstModel/1.0'})
    r = urllib.request.urlopen(req, timeout=timeout)
    return json.loads(r.read())


def fetch_noaa_data():
    """
    获取 NOAA 实时太阳风 + IMF + Dst 数据。
    
    返回:
        plasma: list of dicts [{time_tag, density, speed, temperature}, ...]
        imf:    list of dicts [{time_tag, bx_gsm, by_gsm, bz_gsm, bt}, ...]
        dst:    dict {time_tag (str), dst (float)} 最新一条
    """
    # 等离子体
    plasma_raw = fetch_json(NOAA_PLASMA_URL)
    plasma_header = plasma_raw[0]
    plasma = []
    for row in plasma_raw[1:]:
        plasma.append({
            'time_tag': row[0],
            'density': float(row[1]) if row[1] is not None and row[1] not in ('', 'NaN') else np.nan,
            'speed': float(row[2]) if row[2] is not None and row[2] not in ('', 'NaN') else np.nan,
            'temperature': float(row[3]) if row[3] is not None and row[3] not in ('', 'NaN') else np.nan,
        })
    
    # IMF
    imf_raw = fetch_json(NOAA_MAG_URL)
    imf_header = imf_raw[0]
    imf = []
    for row in imf_raw[1:]:
        imf.append({
            'time_tag': row[0],
            'bx_gsm': float(row[1]) if row[1] is not None and row[1] not in ('', 'NaN') else np.nan,
            'by_gsm': float(row[2]) if row[2] is not None and row[2] not in ('', 'NaN') else np.nan,
            'bz_gsm': float(row[3]) if row[3] is not None and row[3] not in ('', 'NaN') else np.nan,
            'bt': float(row[6]) if len(row) > 6 and row[6] is not None and row[6] not in ('', 'NaN') else np.nan,
        })
    
    # Dst (Kyoto)
    dst_raw = fetch_json(NOAA_DST_URL)
    # 取最近一条
    latest_dst = dst_raw[-1] if dst_raw else {'time_tag': None, 'dst': 0}
    
    return plasma, imf, latest_dst


def bz_south(bz_gsm):
    """南向 IMF 分量: Bs = -Bz 当 Bz < 0, 否则 0"""
    return max(-bz_gsm, 0.0)


def burton_step(dt_hours, v, bs, dst, a=DEFAULT_A, tau=DEFAULT_TAU):
    """
    单步 Euler 积分 (O'Brien & McPherron 2000):
      dDst/dt = -a * (V/1000) * Bs - Dst/tau
    
    其中 V/1000 将 km/s 转换为 1000 km/s 单位,
    a=4.4 nT/hr, Bs = max(-Bz_GSM, 0) (南向分量)
    
    参数:
        dt_hours: 时间步长 (小时)
        v:        太阳风速 (km/s)
        bs:       南向 IMF 分量 (nT)
        dst:      当前 Dst (nT)
        a:        耦合系数 (nT/hr)
        tau:      衰减时间常数 (小时)
    
    返回: 下个时刻的 Dst (nT)
    """
    d_dst = -a * (v / 1000) * bs - dst / tau
    return dst + d_dst * dt_hours


def predict_dst(plasma, imf, current_dst, hours_ahead=6):
    """
    Burton 方程向前积分预测 Dst。
    
    参数:
        plasma: 太阳风等离子体数据
        imf:    IMF 数据
        current_dst: 当前 Dst (nT)
        hours_ahead: 预测时长 (小时)
    
    返回:
        predictions: [(time_tag, dst_pred), ...]
        current_state: 当前状态 dict
    """
    # 对齐等离子体和 IMF 数据 (按最近时间匹配)
    # 取最近几条的平均作为当前状态
    n_avg = 5
    
    recent_v = []
    recent_bs = []
    
    # 最近 n_avg 条有效数据
    for p, m in zip(plasma[-n_avg:], imf[-n_avg:]):
        v = p['speed']
        bz = m['bz_gsm']
        if not np.isnan(v) and not np.isnan(bz):
            recent_v.append(v)
            recent_bs.append(bz_south(bz))
    
    if not recent_v:
        return [], {'error': 'no valid data'}
    
    v_avg = np.mean(recent_v)
    bs_avg = np.mean(recent_bs)
    
    current = {
        'v': v_avg,
        'v_last': plasma[-1]['speed'],
        'bs': bs_avg,
        'bs_last': bz_south(imf[-1]['bz_gsm']),
        'bz_last': imf[-1]['bz_gsm'],
        'bt_last': imf[-1]['bt'],
        'density': plasma[-1]['density'],
        'dst_current': current_dst,
        'coupling': v_avg * bs_avg,  # 磁层耦合强度
    }
    
    # 向前积分 (1 分钟步长)
    dt_hours = 1.0 / 60.0  # 1 分钟 = 1/60 小时
    n_steps = int(hours_ahead / dt_hours)
    
    dst_pred = current_dst
    predictions = []
    
    # 用当前太阳风状态外推 (因为没有未来数据)
    for i in range(n_steps):
        dst_pred = burton_step(dt_hours, v_avg, bs_avg, dst_pred)
        t = datetime.now(timezone.utc) + timedelta(hours=i * dt_hours)
        predictions.append((t.isoformat(), dst_pred))
    
    return predictions, current


def estimate_recovery_time(dst_min, threshold=-20):
    """
    从 Dst 极小值估算地磁风暴恢复时间。
    使用指数衰减: Dst(t) = Dst_min * exp(-t/tau)
    
    返回: 恢复到 threshold 所需时间 (小时)
    """
    if dst_min >= threshold:
        return 0
    t_hours = -DEFAULT_TAU * np.log(threshold / dst_min) if dst_min < 0 else 0
    return max(0, t_hours)


def classify_storm(dst_min):
    """地磁风暴分级 (基于 NOAA G-scale)"""
    if dst_min >= -30:
        return "G0 (安静)", "green"
    elif dst_min >= -50:
        return "G1 (轻微)", "yellow"
    elif dst_min >= -100:
        return "G2 (中等)", "orange"
    elif dst_min >= -200:
        return "G3 (强)", "red"
    elif dst_min >= -350:
        return "G4 (严重)", "purple"
    else:
        return "G5 (极强)", "darkred"


def print_report(predictions, current, hours_ahead=6):
    """打印 Dst 预测报告"""
    print(f"\n{'='*55}")
    print(f"  Dst 模型 — Burton 方程实时预测")
    print(f"{'='*55}")
    print(f"  当前 Dst          : {current['dst_current']:+.0f} nT")
    print(f"  太阳风速          : {current['v_last']:.0f} km/s ({current['v']:.0f} avg)")
    print(f"  密度              : {current['density']:.2f} /cc")
    print(f"  IMF Bt            : {current['bt_last']:.1f} nT")
    print(f"  IMF Bz            : {current['bz_last']:+.1f} nT (南向 Bs={current['bs_last']:.1f})")
    print(f"  磁层耦合 V*Bs     : {current['coupling']:.0f} km/s*nT")
    print(f"  ─────────────────────────────────────")
    
    if predictions:
        min_dst = min(p[1] for p in predictions)
        grade, _ = classify_storm(min_dst)
        print(f"  {hours_ahead}h 预测:")
        for t, d in predictions[::60][:4]:  # 每 60 分钟挑一个
            print(f"    {t[11:16]}  Dst = {d:+.0f} nT")
        print(f"  {hours_ahead}h 极小值 : {min_dst:+.0f} nT → {grade}")
        
        rec = estimate_recovery_time(min_dst)
        if rec > 0:
            print(f"  恢复时间估计       : {rec:.0f} 小时 (>-20 nT)")
    else:
        print(f"  无法预测 (数据不足)")
    
    print(f"{'='*55}\n")
    return predictions


# ============================================================
# 命令行入口
# ============================================================

def main():
    import sys
    
    hours_ahead = 6
    if len(sys.argv) > 1:
        try:
            hours_ahead = int(sys.argv[1])
        except ValueError:
            pass
    
    print(f"  [Dst Model v{__version__}] 获取 NOAA 实时数据...")
    
    plasma, imf, latest_dst = fetch_noaa_data()
    current_dst = float(latest_dst['dst'])
    
    print(f"  Plasma: {len(plasma)} records, IMF: {len(imf)} records")
    print(f"  当前 Dst: {current_dst:+.0f} nT (at {latest_dst['time_tag']})")
    
    predictions, current = predict_dst(plasma, imf, current_dst, hours_ahead)
    print_report(predictions, current, hours_ahead)
    
    return predictions, current


if __name__ == '__main__':
    main()
