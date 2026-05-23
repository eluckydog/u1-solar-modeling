# 专业红队安全审计报告

**项目**: U(1) Solar Modeling  
**标准**: T2 | **日期**: 2026-05-23  
**审计范围**: 11 模块（5 应用 + 3 预测 + 2 空间天气 + 1 验证）

---

## 1. 分层安全审查

### 基础设施层（文件系统访问）

| 检查项 | 状态 | 详情 |
|--------|------|------|
| 数据管道路径注入 | ✅ 低风险 | `save_snapshot()` / `load_snapshot()` 的 `filename` 仅由内部硬编码调用，无外部输入注入路径。但函数本身**无路径验证**，若未来重构为接受用户输入则成为漏洞。 |
| FITS 读取格式验证 | ⚠️ 中风险 | `_read_sharp_cea()` 检查 `NAXIS == 2`，但**不验证数据尺寸合理性**。一个构造的 FITS 文件若设 `NAXIS1=100000, NAXIS2=100000`，将尝试分配 80GB（float64），导致 OOM。`assert` 用于 shape 一致性检查（`assert bp.shape == bt.shape == ...`），但 `assert` 在 `python -O` 模式下被禁用。 |
| 模拟数据误踩 | ⚠️ 低风险 | `test_flare_idx.py` 中随机场产生的 Flare_Idx 值与真实 HMI 数据在同一量级。`demo_all.py` 同时调用模拟生成和真实 FITS 路径，若生产流程混淆两类输出可能导致误导性结果。 |
| 硬编码用户路径 | ⚠️ 低风险 | `flare_idx.py` `__main__` 块硬编码 `d = r'C:\Users\13918\.qclaw\...'`，在公开演示时泄露完整用户目录结构。 |

### 应用层（代码执行）

| 检查项 | 状态 | 详情 |
|--------|------|------|
| exec/eval 使用 | ✅ 无风险 | 全代码库未发现 `exec()` 或 `eval()` 调用。 |
| 外部命令执行 | ✅ 无风险 | 未使用 `subprocess`、`os.system`、`os.popen` 等。 |
| CLI 参数验证 | ⚠️ 中风险 | |
| | | `cme_model.py --v0`: `float(sys.argv[idx+1])` — 无范围检查。`v0=1e7` → tau=0.0005h → 1AU 穿越仅需 24 分钟，物理上荒谬但无警告。 |
| | | `dst_model.py`: `int(sys.argv[1])` — 无范围/类型校验。 |
| assert 用于运行时校验 | ⚠️ 中风险 | `U1SolarModel._validate()` 用 `assert self.KAPPA > 0`；`load_sharp_vector()` 用 `assert` 检查 shape 一致性。`python -O` 模式下静默跳过。 |

### 内容层（数据流）

| 检查项 | 状态 | 详情 |
|--------|------|------|
| JSON 解析（DONKI） | ✅ 低风险 | `analyze_donki_cmes()` 广泛使用 `.get()` 安全访问。C层速度字段 `None` 时 `continue` 跳过。 |
| JSON 解析（NOAA） | ⚠️ 中风险 | `dst_model.py` 假设 `fetch_json()` 返回的是 list（`plasma_raw[0]`），若 API 返回意外格式则 IndexError。`plasma_raw` 为空 list 同样 crash。**无行级 try/except**，一条坏数据拖垮整个解析。 |
| CSV 解析（NOAA） | ⚠️ 中风险 | `noaa_pipeline.py` 中 `parse_solar_wind()` 访问 `raw[-1]` 前未确认 `raw` 非空。`parse_xrs_flux()` 的 `for row in raw` 中 `try/except` 跳过坏行 ✅。 |
| NaN/None 防御 | ⚠️ 不一致 | |
| | | `dst_model.py`: ✅ 极好 — 逐字段检查 `None`、`''`、`'NaN'`。 |
| | | `flare_idx.py`: ✅ 好 — `np.isnan()` 过滤。 |
| | | `u1_solar_model.py`: ❌ 无 — `phase(float('nan'))` 返回 nan，静默传播到 `flare_rate()` 和 `predict_next_peak()`。 |

### 行为层（用户交互）

| 检查项 | 状态 | 详情 |
|--------|------|------|
| 错误信息暴露内部结构 | ✅ 低风险 | `print_report()` 系列不暴露路径。异常被截断到 60-80 字符。 |
| demo_all.py 异常吞噬 | ⚠️ 中风险 | `code/demo_all.py` 模块 10 (`dst_model:`) 使用 `except: pass`（裸 except + 完全沉默）。错误信息完全丢失，无法诊断 NOAA 离线等问题。其他模块的 `except Exception as e: outcome.append(...)` 较好但也不完善。 |
| 实时预测回退机制 | ✅ 好 | `forecast_live()` 在 DONKI/NOAA 失败时自动回退到本地缓存，捕获异常并打印截断信息。 |

---

## 2. 对抗性触发测试

以下输入可导致模型行为异常或崩溃：

1. **`U1SolarModel.phase(float('nan'))`** → nan 静默传播。`flare_rate()` 返回 `nan`，`predict_next_peak()` 返回 `nan`。代码全程不检测 NaN 输入。

2. **`DragBasedModel(v0=-5000)`** → `max()` 钳位到 401，不报错。用户以为输入了某值但模型用了完全不同值。反向同理：`v0=500000` → tau→0 → 到达时间 0.4h → 物理荒谬。

3. **NOAA API 返回格式变更的 JSON** → 假设 `dst_model.py` 中 `fetch_json(NOAA_PLASMA_URL)` 返回的是预期的二维数组格式。若 NOAA 新增列或重组输出，索引 `row[2]` 等将 IndexError。**无格式版本校验**。

4. **恶意大尺寸 FITS** → `_read_sharp_cea()` 中 `fits.open(path)` 后无尺寸检查直接 `h.data.astype(np.float64)`。一个 10000×10000 的 FITS 即为 800MB+（float64），可导致内存耗尽。

5. **CSV 文件含非数字数据** → `hilbert_phase.py` 中 `float(row['year'])` 遇到 `"N/A"` 字符串直接 ValueError，无 fallback。

6. **`predict_dst()` 中超大太阳风参数** → `v=99999, bz=-99999` → 耦合项 `v*bs` ≈ 1e10 → `burton_step` 产生 Dst = -500,000+ nT → 分级输出 `G5 (极强)` 但实际是运算溢出导致的虚假警报。

---

## 3. 攻击链 Trace

**假设**: 攻击者能够拦截或篡改 NOAA/DONKI API 响应（DNS 投毒/中间人/CDN 失陷）。

### Step 1: 数据注入
攻击者修改 `bz_gsm` 字段为持续 -5000nT 的虚假数据，太阳风速度注入为 20000 km/s，DONKI CME 注入 `speed: 50000`。

### Step 2: 传播与放大
- **Dst 模型**: `predict_dst()` 中的耦合项 `v_avg * bs_avg` 增大 1000×，`burton_step` 积分 6 小时后 Dst 低至 -500,000 nT。
- **CME 模型**: `DragBasedModel(v0=50000)` → tau ≈ 1e-5h → 到达时间 < 1 小时，地磁潜力 = 10/10(G5)。
- **缓存持久化**: `save_snapshot(donki, 'donki_cmes_snapshot.json')` 将虚假数据写入本地。重启使用 `--offline` 或网络恢复失败后缓存回退时，虚假数据被视为真实。

### Step 3: 影响
- **虚假警报**: 输出声称即将发生 G5 级超级风暴，造成不必要的资源调度 / 公众恐慌。
- **NOAA 态势面板误报**: `noaa_pipeline.py` 报告 M+ 耀斑和太阳风高速警报。
- **缓存毒化**: 恶意 JSON 持久驻留，即使网络恢复正常后，离线模式仍继续输出虚假预测。
- **限制**: 攻击者无法执行任意代码或读取文件（无 RCE 向量）。攻击范围限于**虚假科学输出**和**拒绝服务**。

---

## 4. 总体风险评估

```
    整体风险: 低-中
    高严重性: 0  中严重性: 5  低严重性: 3  无风险: 4
```

**积极方面**:
- 代码**未使用** `exec/eval/subprocess` — 无 RCE 向量
- NOAA/DONKI 数据获取有基本的异常捕获和回退机制
- `analyze_donki_cmes()` 安全使用 `.get()` 访问嵌套 JSON
- `dst_model.py` 对 None/NaN/''/'NaN' 字符串做了多层防御 — 本代码库中防御最好的模块
- HMI FITS 读取有基本的格式检查（NAXIS==2）

**关键薄弱点**:
- 输入验证不统一 — `U1SolarModel` 完全无 NaN/Inf 防御
- Python `assert` 用于关键运行时验证
- 裸 `except: pass` 隐藏错误
- 大 FITS 无尺寸检查 → OOM 潜在风险
- 硬编码用户路径泄漏

---

## 5. 改进建议（按优先级）

### P0 — 立即修复

1. **`code/demo_all.py` 模块 10**: 将 `except: pass` 替换为 `except Exception as e: outcome.append(f"dst_model: {e}")`。裸 except 隐藏 NOAA 数据管道故障。

    ```python
    # 当前 (危险):
    except: pass  # 即使 NOAA 不可达也不中断
    
    # 建议:
    except Exception as e:
        outcome.append(f"dst_model: {e}")
    ```

### P1 — 高优先级

2. **`u1_solar_model.py` 输入验证**: 在 `phase()` 和 `flare_rate()` 入口添加 NaN/Inf/负数检查。

    ```python
    def phase(self, year: float) -> float:
        if not np.isfinite(year) or year < 1700 or year > 2100:
            raise ValueError(f"Invalid year: {year}")
        ...
    ```

3. **`flare_idx.py` FITS 尺寸检查**: 在 `_read_sharp_cea()` 中限制最大像素数。

    ```python
    MAX_PIXELS = 100_000_000  # ~800MB for float64
    if h.header['NAXIS1'] * h.header['NAXIS2'] > MAX_PIXELS:
        raise ValueError(f"FITS too large: {h.header['NAXIS1']}x{h.header['NAXIS2']}")
    ```

4. **`dst_model.py` API 响应结构验证**: 在 `fetch_json()` 返回后验证是 list 且非空。

    ```python
    plasma_raw = fetch_json(NOAA_PLASMA_URL)
    if not isinstance(plasma_raw, list) or len(plasma_raw) < 2:
        return [], {}, {'time_tag': None, 'dst': 0}
    ```

### P2 — 中优先级

5. **`cme_model.py` CLI 参数范围检查**: 对 `--v0` 添加物理合理性约束。

    ```python
    v0 = float(sys.argv[idx + 1])
    if not 100 < v0 < 10000:
        print(f"[WARN] V0={v0} 超出物理合理范围 (100-10000 km/s)")
    ```

6. **移除硬编码用户路径**: `flare_idx.py` `__main__` 块中使用 `os.path.expanduser` 或环境变量替代绝对路径。

    ```python
    d = os.environ.get('HMI_DATA_DIR', os.path.join(os.path.dirname(__file__), '..', 'data', 'hmi'))
    ```

7. **替换关键 `assert`**: 在 `load_sharp_vector()` 和 `U1SolarModel._validate()` 中。

    ```python
    # 当前:
    assert self.KAPPA > 0, "KAPPA must be positive"
    # 建议:
    if self.KAPPA <= 0:
        raise ValueError(f"KAPPA must be positive, got {self.KAPPA}")
    ```

### P3 — 低优先级

8. **添加 HTTPS 证书验证**: NOAA/DONKI 当前使用 `urllib.request` 无证书锁定。添加 `context=ssl.create_default_context()`。

9. **`noaa_pipeline.py` 行级防御**: `parse_solar_wind()` 中增加 `raw` 非空检查和 try/except。

10. **统一异常日志**: 整个项目使用一致的日志模式，避免 `print(f"[X] ... ")` 与 `outcome.append()` 混用。

---

## 审计结论

U(1) Solar Modeling 项目作为科学计算框架，**安全性总体可接受**。核心风险集中于：

> **输入验证不一致 + `except: pass` 隐藏故障 + 无尺寸限制的 FITS 读取**

这三个问题在科学计算项目中常见，但修复成本低、收益高。建议优先处理 P0 的 `except: pass` 和 P1 的 NaN 传播，然后逐步覆盖 P2-P3 项。

无 RCE 或数据泄露风险。攻击面主要限于虚假科学输出和拒绝服务，不会导致系统级受损。

---

*红队 v2.0 | T2 标准测试 | 2026-05-23*
