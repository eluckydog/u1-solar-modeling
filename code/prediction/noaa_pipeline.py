#!/usr/bin/env python3
"""
NOAA 数据集成管道：实时耀斑监测 + U(1) 预测  [已弃用]

⚠️ 本文件已弃用，请使用 noaa_pipeline_v2.py 替代。
   v2 修复了 JSON 解析格式兼容性，接口更稳定。

数据源：
  - NOAA SWPC JSON (最新30天耀斑、XRS通量、太阳风)
  - 本地 SDO/HMI 磁图（如有）

功能：
  1. 实时耀斑态势（latest flare, XRS flux, solar wind）
  2. 耀斑峰值识别（从1min通量数据自找）
  3. 太阳风预警（速度/密度异常）
  4. 综合态势摘要
"""

import warnings
warnings.warn(
    "noaa_pipeline.py (v1) is deprecated, use noaa_pipeline_v2.py instead",
    DeprecationWarning, stacklevel=2
)

import os, json, csv, sys
import urllib.request
from datetime import datetime, timedelta, timezone

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        '..', '..', 'data', 'real')
os.makedirs(DATA_DIR, exist_ok=True)

# NOAA SWPC JSON endpoints
NOAA_URLS = {
    'latest_flares': 'https://services.swpc.noaa.gov/json/goes/primary/xray-flares-latest.json',
    'xrs_flux': 'https://services.swpc.noaa.gov/json/goes/primary/xrays-1-day.json',
    'solar_wind': 'https://services.swpc.noaa.gov/products/solar-wind/plasma-7-day.json',
    'mag': 'https://services.swpc.noaa.gov/products/solar-wind/mag-7-day.json',
}


def fetch_json(url, timeout=15):
    """Fetch JSON from URL with retry"""
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
            if len(data) < 10:
                return None
            return json.loads(data)
        except Exception as e:
            if attempt == 0:
                continue
            return None
    return None


def flare_class(flux):
    """通量 → 耀斑分级"""
    if flux is None or flux <= 0:
        return 'N/A'
    if flux >= 1e-4:
        return f'X{flux/1e-4:.2f}'
    elif flux >= 1e-5:
        return f'M{flux/1e-5:.2f}'
    elif flux >= 1e-6:
        return f'C{flux/1e-6:.2f}'
    elif flux >= 1e-7:
        return f'B{flux/1e-7:.2f}'
    else:
        return f'A{flux/1e-8:.2f}'


def flare_class_num(cls_str):
    """分级字符串 → 数字（用于比较）"""
    prefix = cls_str[0] if cls_str and len(cls_str) > 0 else 'A'
    try:
        num = float(cls_str[1:])
    except:
        num = 0
    return {'X': 4, 'M': 3, 'C': 2, 'B': 1, 'A': 0}.get(prefix, 0), num


def parse_latest_flares(raw):
    """解析最新耀斑列表"""
    if not raw:
        return []
    flares = []
    for item in raw:
        flares.append({
            'time': item.get('time_tag', ''),
            'satellite': item.get('satellite', ''),
            'max_class': item.get('max_class', ''),
            'max_time': item.get('max_time', ''),
            'begin_time': item.get('begin_time', ''),
            'end_time': item.get('end_time', ''),
            'current_class': item.get('current_class', ''),
        })
    return flares


def parse_xrs_flux(raw):
    """解析 XRS 通量时间序列 → 提取耀斑峰值"""
    if not raw:
        return [], []
    # 格式: [[time_tag, channel, flux], ...]
    # channel: 'xrsa' (0.5-4A), 'xrsb' (1-8A)
    points_xrsa = []
    points_xrsb = []
    
    for row in raw:
        try:
            t = row[0]
            ch = row[1]
            f = float(row[2])
            if ch == 'xrsa' or ch == 0:
                points_xrsa.append((t, f))
            elif ch == 'xrsb' or ch == 1:
                points_xrsb.append((t, f))
        except:
            continue
    
    # 从 XRSB (1-8A) 找峰值
    peaks = []
    pts = points_xrsb if points_xrsb else points_xrsa
    for i in range(1, len(pts)-1):
        try:
            t, f = pts[i]
            _, fp = pts[i-1]
            _, fn = pts[i+1]
            if f > fp and f > fn and f > 1e-7:  # > A1.0
                peaks.append({
                    'time': t,
                    'flux_wm2': f,
                    'class': flare_class(f),
                })
        except:
            continue
    
    return pts, peaks


def parse_solar_wind(raw):
    """解析太阳风数据"""
    if not raw:
        return None
    try:
        # 格式: [[time, time_tag, proton_density, bulk_speed, ion_temp], ...]
        latest = raw[-1] if len(raw) > 0 else None
        if latest and len(latest) >= 4:
            return {
                'time': latest[0],
                'density': float(latest[2]) if latest[2] != 'null' else None,
                'speed': float(latest[3]) if latest[3] != 'null' else None,
                'temperature': float(latest[4]) if len(latest) > 4 and latest[4] != 'null' else None,
            }
    except:
        pass
    return None


def check_alert_conditions(sw, flares, xrs_pts):
    """检查预警条件"""
    alerts = []
    
    # 1. 太阳风高速
    if sw and sw.get('speed') and sw['speed'] > 600:
        alerts.append(f"太阳风高速: {sw['speed']:.0f} km/s (>600)")
    
    # 2. 高密度
    if sw and sw.get('density') and sw['density'] > 20:
        alerts.append(f"太阳风高密: {sw['density']:.1f} /cc (>20)")
    
    # 3. M级以上耀斑
    for f in flares:
        lvl, num = flare_class_num(f['max_class'])
        if lvl >= 3:  # M+
            alerts.append(f"M+耀斑: {f['max_class']} @ {f['max_time']}")
    
    # 4. XRS 持续升高
    if xrs_pts and len(xrs_pts) > 10:
        last5 = [f for _, f in xrs_pts[-5:]]
        mean_last = sum(last5)/len(last5)
        prev5 = [f for _, f in xrs_pts[-10:-5]]
        mean_prev = sum(prev5)/len(prev5)
        if mean_last > mean_prev * 3 and mean_last > 1e-6:
            alerts.append(f"XRS 通量快速上升: {mean_last:.2e} -> {flare_class(mean_last)}")
    
    return alerts


def fetch_all():
    """获取所有 NOAA 数据"""
    results = {}
    
    for name, url in NOAA_URLS.items():
        data = fetch_json(url)
        results[name] = data
    
    return results


def run_summary():
    """运行完整态势"""
    print("=" * 65)
    print("NOAA 空间天气实时监测")
    print(f"更新时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 65)
    
    # 获取数据
    raw = fetch_all()
    if not any(raw.values()):
        print("  [X] 数据获取失败（网络不可达）")
        return None
    
    # 解析
    flares = parse_latest_flares(raw.get('latest_flares'))
    xrs_pts, peaks = parse_xrs_flux(raw.get('xrs_flux'))
    sw = parse_solar_wind(raw.get('solar_wind'))
    
    print(f"\n【空间天气】")
    if sw:
        print(f"  太阳风速: {sw['speed']:.0f} km/s" if sw['speed'] else "  N/A")
        print(f"  质子密度: {sw['density']:.1f} /cc" if sw['density'] else "  N/A")
    
    print(f"\n【最新耀斑 (30天)】")
    if flares:
        for f in flares[:5]:
            cls = f['max_class']
            lvl, _ = flare_class_num(cls)
            marker = '[!]' if lvl >= 3 else '  '
            print(f"  {marker} {cls:6s}  @ {f['max_time'][:19]}  (GOES-{f['satellite']})")
        if len(flares) > 5:
            print(f"  ... 共 {len(flares)} 条")
    else:
        print("  无数据")
    
    print(f"\n【XRS 通量 (1-8A, 最新值)】")
    if xrs_pts and len(xrs_pts) > 0:
        _, f = xrs_pts[-1]
        print(f"  当前: {f:.2e} W/m²  =  {flare_class(f)}")
        if peaks:
            top = max(peaks, key=lambda p: p['flux_wm2'])
            print(f"  24h 最高: {top['class']}  @ {top['time'][:19]}")
            print(f"  峰值数 (B+): {len(peaks)}")
    
    print(f"\n【预警】")
    alerts = check_alert_conditions(sw, flares, xrs_pts)
    if alerts:
        for a in alerts:
            print(f"  [!] {a}")
    else:
        print("  无异常")
    
    # 保存
    snapshot = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'latest_class': flares[0]['max_class'] if flares else None,
        'wind_speed': sw['speed'] if sw else None,
        'density': sw['density'] if sw else None,
        'xrs_current': xrs_pts[-1][1] if xrs_pts else None,
        'num_peaks_24h': len(peaks),
        'alerts': alerts,
    }
    with open(os.path.join(DATA_DIR, 'noaa_snapshot.json'), 'w') as f:
        json.dump(snapshot, f, indent=2)
    print(f"\n  快照保存: {os.path.join(DATA_DIR, 'noaa_snapshot.json')}")
    print("=" * 65)
    
    return snapshot


if __name__ == '__main__':
    snap = run_summary()
    if snap:
        print("\n✓ 数据管道运行成功")
