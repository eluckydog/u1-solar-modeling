#!/usr/bin/env python3
"""
NOAA 数据管道 v2 — 正确解析格式
"""
import os, json, sys
import urllib.request
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        '..', '..', 'data', 'real')
os.makedirs(DATA_DIR, exist_ok=True)

NOAA_URLS = {
    'flares': 'https://services.swpc.noaa.gov/json/goes/primary/xray-flares-latest.json',
    'xrs': 'https://services.swpc.noaa.gov/json/goes/primary/xrays-1-day.json',
    'wind': 'https://services.swpc.noaa.gov/products/solar-wind/plasma-7-day.json',
    'mag': 'https://services.swpc.noaa.gov/products/solar-wind/mag-7-day.json',
}

def fetch(url, timeout=15):
    for _ in range(2):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = r.read()
            return json.loads(d) if len(d) > 10 else None
        except:
            continue
    return None

def flare_class(flux):
    if flux is None or flux <= 0:
        return 'N/A'
    if flux >= 1e-4: return f'X{flux/1e-4:.2f}'
    if flux >= 1e-5: return f'M{flux/1e-5:.2f}'
    if flux >= 1e-6: return f'C{flux/1e-6:.2f}'
    if flux >= 1e-7: return f'B{flux/1e-7:.2f}'
    return f'A{flux/1e-8:.2f}'

def run():
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    print("="*60)
    print("NOAA 空间天气实时监测")
    print(f"  更新: {ts}")
    print("="*60)

    raw = fetch_all()
    if not any(raw.values()):
        print("\n  [X] 所有数据源不可达 (网络问题)")
        return

    # === 耀斑 ===
    flares = raw.get('flares', [])
    print(f"\n[历] 最新耀斑 (30天):")
    if flares:
        for f in flares[:5]:
            c = f.get('max_class', 'N/A')
            print(f"     {c:6s} @ {f.get('max_time','')[:19]}  GOES-{f.get('satellite','?')}")
    else:
        print("     无数据")

    # === XRS 通量 ===
    xrs = raw.get('xrs', [])
    xrs_long = [x for x in xrs if x.get('energy','') == '0.1-0.8nm']
    
    print(f"\n[X] XRS 通量 (1-8A):")
    if xrs_long:
        last = xrs_long[-1]
        flux = last.get('flux', 0)
        print(f"     当前: {flux:.2e} W/m2 = {flare_class(flux)}")
        print(f"     @ {last.get('time_tag','')[:19]}")
        
        # 找峰值
        peaks = []
        for i in range(1, len(xrs_long)-1):
            f0 = xrs_long[i].get('flux', 0)
            fp = xrs_long[i-1].get('flux', 0)
            fn = xrs_long[i+1].get('flux', 0)
            if f0 > fp and f0 > fn and f0 > 1e-7:
                peaks.append({'time': xrs_long[i]['time_tag'], 'flux': f0,
                              'class': flare_class(f0)})
        
        top = max(peaks, key=lambda p: p['flux']) if peaks else None
        if top:
            print(f"     24h 最高: {top['class']} @ {top['time'][:19]}")
        print(f"     峰值数 (B+): {len(peaks)}")
    else:
        print("     无数据")

    # === 太阳风 ===
    wind = raw.get('wind', [])
    print(f"\n[W] 太阳风:")
    if wind and len(wind) > 1:
        # 跳过表头行
        if isinstance(wind[0], list) and wind[0][0] == 'time_tag':
            wind = wind[1:]
        if wind:
            last_w = wind[-1]
            speed = float(last_w[2]) if len(last_w) > 2 else 0
            dens = float(last_w[1]) if len(last_w) > 1 else 0
            print(f"     速度: {speed:.0f} km/s")
            print(f"     密度: {dens:.1f} /cc")
            
            alerts = []
            if speed > 600:
                alerts.append(f"太阳风高速: {speed:.0f} km/s")
            if dens > 20:
                alerts.append(f"太阳风高密: {dens:.1f} /cc")
            if alerts:
                print(f"\n[!] 警报: {'; '.join(alerts)}")
    else:
        print("     无数据")

    print("\n" + "="*60)
    print("[OK] 数据管道运行成功")
    print("="*60)

def fetch_all():
    return {name: fetch(url) for name, url in NOAA_URLS.items()}

if __name__ == '__main__':
    run()
