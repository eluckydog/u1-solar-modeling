#!/usr/bin/env python3
"""
cme_model.py — 日冕物质抛射传播与到达预测 (v2.0)
=================================================

实时数据 + DBM 解析 + 历史验证

数据源:
  - DONKI 实时 API (NASA CCMC): 最新 CME 事件
  - 本地缓存的 NOAA SWPC 报警
  - 本地历史 CME Bundle (已验证事件)

用法:
  python cme_model.py              → 实时预测最近 CME
  python cme_model.py --offline    → 用本地缓存数据
  python cme_model.py --v0 1900    → 手动指定初速
  python cme_model.py --verify     → 历史事件验证
"""
import numpy as np
import urllib.request, json
from datetime import datetime, timezone, timedelta
import os

__version__ = "2.0.0"

AU_KM = 1.496e8
DONKI_URL = 'https://kauai.ccmc.gsfc.nasa.gov/DONKI/WS/get/CME'
NOAA_ALERTS_URL = 'https://services.swpc.noaa.gov/products/alerts.json'
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'real')


# ============================================================
# CME 传播物理
# ============================================================

class DragBasedModel:
    """DBM 传播模型 (Vrsnak 2013) + 经验校正 (Gopalswamy 2001)"""

    def __init__(self, v0, vsw=400, gamma=0.5e-7, halo=True):
        self.v0 = max(v0, vsw + 1)  # 至少比背景风快
        self.vsw = vsw
        self.gamma = gamma
        self.halo = halo
        self.dv = self.v0 - self.vsw

    @property
    def tau_hours(self):
        if self.dv <= 0:
            return np.inf
        return 2 / (self.gamma * self.dv) / 3600

    def R(self, T):
        """R(T) = Vsw*T + dv*tau*ln(1+T/tau)"""
        t = self.tau_hours
        if np.isinf(t):
            return self.vsw * T * 3600
        vk = self.vsw * 3600
        dk = self.dv * 3600
        return vk * T + dk * t * np.log(1 + T / t)

    def arrival_time(self):
        target = 0.98 * AU_KM
        lo, hi = 1.0, 500.0
        for _ in range(60):
            m = (lo + hi) / 2
            lo, hi = (m, hi) if self.R(m) < target else (lo, m)
        return (lo + hi) / 2

    def arrival_time_corrected(self):
        t = self.arrival_time()
        f = np.clip(0.85 - 0.12 * np.log10(max(self.v0, 300)), 0.4, 0.95)
        return t * f

    def arrival_velocity(self, corrected=True):
        t_h = self.arrival_time_corrected() if corrected else self.arrival_time()
        t = self.tau_hours
        if np.isinf(t):
            return self.vsw
        return self.vsw + self.dv / (1 + t_h / t)

    def geomagnetic_potential(self):
        score = 0
        if self.v0 > 2000: score += 4
        elif self.v0 > 1000: score += 3
        elif self.v0 > 500: score += 1
        if self.halo: score += 3
        va = self.arrival_velocity()
        if va > 800: score += 2
        elif va > 500: score += 1
        return min(score, 10)

    def flare_class(self):
        return 'X' if self.v0 > 1500 else 'M' if self.v0 > 800 else 'C'

    def report(self, prefix=""):
        t_raw = self.arrival_time()
        t = self.arrival_time_corrected()
        v = self.arrival_velocity()
        g = self.geomagnetic_potential()
        eta = datetime.now(timezone.utc) + timedelta(hours=t)
        desc = ['G0','G0','G1','G1','G2','G2','G3','G3','G4','G4','G5'][g]
        return f"{prefix}V0={self.v0:.0f} tau={self.tau_hours:.1f}h " \
               f"T={t_raw:.0f}→{t:.0f}h (~{eta.strftime('%m-%d %H:%M')}) " \
               f"v_arr={v:.0f}km/s 潜力={g}/10({desc}) 耀斑~{self.flare_class()}"


# ============================================================
# 数据获取
# ============================================================

def fetch_donki_cmes(days_back=7):
    """从 DONKI 获取最近 CME 事件"""
    start = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime('%Y-%m-%d')
    end = (datetime.now(timezone.utc) + timedelta(days=1)).strftime('%Y-%m-%d')
    url = f'{DONKI_URL}?startDate={start}&endDate={end}'
    req = urllib.request.Request(url, headers={'User-Agent': 'cme-model/2.0'})
    data = json.loads(urllib.request.urlopen(req, timeout=20).read())
    return data


def fetch_noaa_alerts():
    """获取 NOAA SWPC 最新告警"""
    url = NOAA_ALERTS_URL
    req = urllib.request.Request(url, headers={'User-Agent': 'cme-model/2.0'})
    data = json.loads(urllib.request.urlopen(req, timeout=15).read())
    return data


def save_snapshot(data, filename):
    """保存数据快照到本地"""
    path = os.path.join(DATA_DIR, filename)
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    size = os.path.getsize(path) / 1024
    return path, f"{size:.0f} KB"


def load_snapshot(filename):
    """从本地快照加载"""
    path = os.path.join(DATA_DIR, filename)
    with open(path, encoding='utf-8') as f:
        return json.load(f)


# ============================================================
# CME 分析器
# ============================================================

def analyze_donki_cmes(donki_data):
    """解析 DONKI CME 列表, 返回可预测的 CME"""
    results = []
    for cme in donki_data:
        cme_id = cme.get('activityID', '?')
        start_str = cme.get('startTime', '?')
        source = cme.get('sourceLocation', '?')
        ar_num = cme.get('activeRegionNum', '?')

        for analysis in cme.get('cmeAnalyses', []):
            speed = analysis.get('speed')
            if speed is None:
                continue
            half_angle = analysis.get('halfAngle') or 45
            earth_dir = analysis.get('isEarthDirected', False)
            lat = analysis.get('latitude')
            lon = analysis.get('longitude')

            halo = half_angle >= 45 if half_angle else True
            v0 = float(speed)

            model = DragBasedModel(v0, halo=halo)
            t = model.arrival_time_corrected()
            va = model.arrival_velocity()
            gp = model.geomagnetic_potential()
            eta = datetime.now(timezone.utc) + timedelta(hours=t)

            results.append({
                'cme_id': cme_id,
                'start': start_str,
                'v0': v0,
                'half_angle': half_angle,
                'halo': halo,
                'source': source,
                'ar_num': ar_num,
                'lat': lat,
                'lon': lon,
                'eta_hours': round(t, 1),
                'eta_utc': eta.strftime('%Y-%m-%d %H:%M'),
                'v_arrival': round(va),
                'potential': gp,
                'model': model,
            })
    return results


# ============================================================
# NOAA 告警 → CME 解析
# ============================================================

ALERT_PATTERNS = [
    ('WATA', 'Watch', None, 500),
    ('WGT', 'Warning', None, 800),
    ('EF3A', 'Electron Flux Alert', 300, None),
    ('AKL', 'A-K Index Alert', None, None),
    ('CME', 'CME Arrival', None, None),
]


def parse_cme_alerts(alerts):
    """从 NOAA 告警提取 CME 相关信息"""
    cme_alerts = []
    for a in alerts:
        msg = a.get('message', '')
        pid = a.get('product_id', '')
        # 找 CME 到达/CME 关键词
        for kw, label, v0_min, v0_max in ALERT_PATTERNS:
            if kw in pid:
                cme_alerts.append({'product_id': pid, 'message': msg[:200],
                                   'label': label, 'time': a.get('issue_datetime', '')})
    return cme_alerts


# ============================================================
# 历史验证 Bundle (内置, 避免依赖网络)
# ============================================================

HISTORICAL_CMES = [
    {'name': 'Carrington 1859', 'v0': 2500, 'known_hours': 17.5, 'known_g': 'G5',
     'note': 'Carrington Event, 极光到赤道'},
    {'name': 'Halloween 2003',  'v0': 1900, 'known_hours': 19,   'known_g': 'G5',
     'note': '瑞典电网故障'},
    {'name': 'Bastille 2000',   'v0': 1800, 'known_hours': 26,   'known_g': 'G4-G5',
     'note': 'SOHO 异常'},
    {'name': 'St. Patrick 2015', 'v0': 700,  'known_hours': 38,   'known_g': 'G3-G4',
     'note': '强烈极光'},
]


def verify_historical():
    """内建历史验证, 无需网络"""
    print(f"\n{'='*55}")
    print(f"  历史 CME 验证 (DBM + 经验校正)")
    print(f"{'='*55}")
    max_err = 0
    for h in HISTORICAL_CMES:
        model = DragBasedModel(h['v0'])
        t = model.arrival_time_corrected()
        err = abs(t - h['known_hours']) / h['known_hours'] * 100
        max_err = max(max_err, err)
        ok = '✓' if err < 20 else '≈'
        print(f"  {h['name']:20s} V0={h['v0']:<4d} "
              f"T={t:.0f}h  err={err:.0f}% {ok}  "
              f"Known: {h['known_hours']:.0f}h, {h['known_g']}")
    print(f"  最大误差: {max_err:.0f}%")
    return max_err


# ============================================================
# 主入口
# ============================================================

def forecast_live():
    """实时预测: DONKI CME + NOAA 告警"""
    print(f"  [CME Model v{__version__}] 实时模式")
    print(f"  时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC")

    # 1. DONKI CME
    print(f"\n{'='*55}")
    print(f"  DONKI 实时 CME (最近 7 天)")
    print(f"{'='*55}")
    try:
        donki = fetch_donki_cmes(7)
        print(f"  获取 {len(donki)} 个事件")
        # 保存快照
        sp, sz = save_snapshot(donki, 'donki_cmes_snapshot.json')
        print(f"  快照: {sp} ({sz})")

        results = analyze_donki_cmes(donki)
        results.sort(key=lambda r: -(r['potential']))

        if results:
            # 最高潜力事件
            best = results[0]
            m = best['model']
            print(f"\n  最高潜力 CME: {best['cme_id']}")
            print(f"  开始: {best['start']}  V0={best['v0']:.0f} km/s")
            print(f"  半角: {best['half_angle']}° 源区: {best['source']}")
            print(f"  预测: T={best['eta_hours']}h ({best['eta_utc']} UTC)")
            print(f"  潜力: {best['potential']}/10  到达速度: {best['v_arrival']} km/s")

            # 全部列表
            print(f"\n  全部 CME 事件:")
            for r in results:
                m = r['model']
                src = r['source'] if r['source'] != '?' else f"AR{r['ar_num']}"
                print(f"    {r['start']} V0={r['v0']:.0f} T={r['eta_hours']:.0f}h "
                      f"v_arr={r['v_arrival']} P={r['potential']}/10 src={src}")
        else:
            print("  没有可预测的 CME (速度信息不足)")

    except Exception as e:
        print(f"  [X] DONKI 获取失败: {str(e)[:80]}")
        print(f"  回退到本地缓存...")
        try:
            donki = load_snapshot('donki_cmes_snapshot.json')
            print(f"  从快照加载 {len(donki)} 个事件")
        except:
            donki = []

    # 2. NOAA 告警
    print(f"\n{'='*55}")
    print(f"  NOAA SWPC 告警 (最新)")
    print(f"{'='*55}")
    try:
        alerts = fetch_noaa_alerts()
        sp, sz = save_snapshot(alerts, 'noaa_alerts_snapshot.json')
        print(f"  获取 {len(alerts)} 条 ({sz})")
        cme_info = parse_cme_alerts(alerts)
        for ci in cme_info[:5]:
            print(f"    {ci['product_id']:8s} {ci['label']}")
    except Exception as e:
        print(f"  [X] NOAA 告警失败: {str(e)[:60]}")
        try:
            alerts = load_snapshot('noaa_alerts_snapshot.json')
            print(f"  从快照加载 {len(alerts)} 条")
        except:
            pass

    # 3. 历史验证
    verify_historical()

    return results


def forecast_offline():
    """离线模式: 只用本地数据"""
    print(f"  [CME Model v{__version__}] 离线模式")

    # 加载 DONKI 快照
    try:
        donki = load_snapshot('donki_cmes_snapshot.json')
        print(f"  DONKI 缓存: {len(donki)} 个事件")
        results = analyze_donki_cmes(donki)
        print(f"  可预测: {len(results)} 个")
        for r in results[:5]:
            m = r['model']
            print(f"    {r['start']} V0={r['v0']:.0f} T={r['eta_hours']:.0f}h P={r['potential']}/10")
    except:
        print("  无 DONKI 缓存, 使用历史示例")
        print("  python cme_model.py --v0 1900 手动运行")

    verify_historical()


def demo_cme(v0):
    """给定 V0 做单次预测"""
    print(f"  [CME Model v{__version__}] 单次预测: V0={v0} km/s")
    model = DragBasedModel(v0)
    print(f"\n{'='*55}")
    print(f"  CME 传播预测")
    print(f"{'='*55}")
    print(f"  V0: {v0:.0f} km/s  Vsw: {model.vsw:.0f}  dv: {model.dv:.0f}")
    print(f"  Tau: {model.tau_hours:.1f}h  Halo: {'Yes' if model.halo else 'No'}")
    print(f"  耀斑: ~{model.flare_class()}级")
    print(f"  ─────────────────────────────────────")
    t_raw = model.arrival_time()
    t = model.arrival_time_corrected()
    v = model.arrival_velocity()
    g = model.geomagnetic_potential()
    eta = datetime.now(timezone.utc) + timedelta(hours=t)
    desc = ['G0','G0','G1','G1','G2','G2','G3','G3','G4','G4','G5'][g]
    print(f"  DBM 原始: {t_raw:.0f}h → 校正: {t:.0f}h")
    print(f"  到达时间: {eta.strftime('%m-%d %H:%M')} UTC")
    print(f"  到达速度: {v:.0f} km/s")
    print(f"  地磁潜力: {g}/10 → {desc}")
    print(f"{'='*55}\n")


if __name__ == '__main__':
    import sys
    args = [a.lower() for a in sys.argv[1:]]

    if '--verify' in args:
        verify_historical()
    elif '--offline' in args:
        forecast_offline()
    elif '--v0' in args:
        idx = args.index('--v0') + 1
        v0 = float(sys.argv[idx + 1]) if len(sys.argv) > idx + 1 else 1000
        demo_cme(v0)
    else:
        forecast_live()
