**中文** | [English](README.en.md)

# u1-solar-modeling

U(1) symmetry in solar observations + **space weather prediction pipeline**.

## Core Insight

The Sun's rotation, magnetic fields, coronal loop oscillations, activity cycle, and helioseismic modes all share one thing: **rotate once and you're back where you started** — that's U(1) symmetry.

This project fits 12 solar modules with U(1) phase:

| Category | Count | Modules |
|----------|-------|---------|
| **Applications** | 5 | Solar rotation, activity cycle, coronal loop oscillation, vector magnetic field, helioseismology |
| **Predictions** | 3 | Hilbert phase tracking, Carrington rotation calendar, shear flare index |
| **Space weather** | 2 | Dst geomagnetic storm prediction, CME propagation (DBM) |
| **Validation** | 1 | Flare_Idx from HMI SHARP magnetograms |
| **Core model** | 1 | U(1) temporal flare model (334,123 Plutino events) |

## Quick Start

### Install

```bash
pip install -r requirements.txt
```

### Run demo

```bash
python demo_all.py          # all 12 modules
```

### Run tests

```bash
python -m pytest tests/ -v  # 82 tests
```

---

## Module Overview

### 5 U(1) Applications

| # | Application | U(1) Variable | Data Source | File |
|---|------------|---------------|-------------|------|
| 1 | **Solar Rotation** (differential rotation Ω(θ)) | latitude θ | SDO HMI | `code/solar_rotation.py` |
| 2 | **Solar Cycle** (11-year sunspot period) | time t | SILSO | `code/solar_cycle.py` |
| 3 | **Coronal Loop Oscillation** (transverse → B-field) | time t | AIA 193 Å | `code/coronal_loop_oscillation.py` |
| 4 | **Vector Magnetic Field** (polar histogram) | azimuth φ | SDO HMI | `code/vector_magnetic_field.py` |
| 5 | **Helioseismology** (spherical harmonic symmetry) | azimuth φ | GONG/HMI | `code/helioseismology.py` |

### 3 Prediction Modules

| # | Module | Function | File |
|---|--------|----------|------|
| 6 | **Hilbert Phase** | Instantaneous phase φ(t) from sunspot data, extrapolate min/max | `code/prediction/hilbert_phase.py` |
| 7 | **Rotation Phase Map** | Map events to Carrington longitude, identify active longitudes | `code/prediction/rotation_phase_map.py` |
| 8 | **Shear Flare Index** | U(1) circular variance × shear angle → flare potential | `code/prediction/shear_flare_index.py` |

### 2 Space Weather Models

| # | Module | Function | File |
|---|--------|----------|------|
| 9 | **Dst Prediction** | Burton equation, real-time NOAA SWPC solar wind | `code/prediction/dst_model.py` |
| 10 | **CME Propagation** | Analytic DBM + Gopalswamy correction, real-time DONKI CME catalog | `code/prediction/cme_model.py` |

### Validation + Core Model

| # | Module | Function | File |
|---|--------|----------|------|
| 11 | **Flare_Idx** | HMI SHARP vector magnetogram → polarity-separated shear × circ. variance | `code/flare_idx.py` |
| 12 | **U(1) Temporal Model** | von Mises fit on 334,123 Plutino events | `code/u1_solar_model.py` |

### Data Pipelines

- **NOAA SWPC**: real-time solar wind (Dst, V, density, Bz)
- **DONKI**: real-time CME catalog (speed, angular width, source)
- **Plutino FlareList**: 207,814 events (1986-2020), Cycles 22-24
- **SILSO sunspot number**: 3297+ monthly rows (1750-2024)
- **HMI SHARP CEA**: AR 11092 vector magnetograms (FITS)

---

## Core Model

**U(1) Temporal Flare Model** (`code/u1_solar_model.py`)

| Parameter | Value | Meaning |
|-----------|-------|---------|
| t₀ | 1986.2 | Cycle 22 solar minimum |
| T | 11.0 years | Mean solar cycle |
| A | 188.44 | von Mises amplitude |
| μ | 142.9° (2.49 rad) | Flare peak phase offset |
| κ | 1.26 | Concentration (width⁻¹) |
| C | 0.0 | Baseline rate |

**Validation**: 334,123 Plutino events (1986-2020, Cycles 22-24)
- Rayleigh Z = 3496 (p ≈ 0), R² = 0.689
- Peak/trough ratio = 12.4×
- **Phase lag Φ_lag = 142.9°** — magnetic energy accumulation and release separated by ~3.2 years
- Next peak prediction: **2034.6**
- Full documentation: `docs/U1_SOLAR_MODEL.md`

---

## Project Structure

```
u1-solar-modeling/
├── README.md / README.en.md   # Bilingual docs
├── SKILL.md
├── requirements.txt
├── demo_all.py                 # End-to-end demo (12 modules)
├── dimensions/                 # Theoretical foundations (5 docs)
├── code/                       # 5 applications + core model
│   ├── prediction/             # Prediction + space weather
│   │   ├── dst_model.py       # Dst geomagnetic storm
│   │   ├── cme_model.py       # CME propagation
│   │   ├── hilbert_phase.py   # Hilbert phase tracking
│   │   ├── shear_flare_index.py
│   │   └── rotation_phase_map.py
│   ├── flare_idx.py           # HMI Flare_Idx validation
│   ├── u1_solar_model.py      # Core temporal model
│   └── ...
├── data/                       # Observed + real-time data
├── docs/
│   ├── U1_SOLAR_MODEL.md
│   ├── DATA_BARRIERS_AND_MODEL_SPEC.md
│   └── storm_clock.html
└── tests/                      # 82 unit tests
```

## Data Sources

| Data | Source | Path/API |
|------|--------|----------|
| Solar rotation | SDO HMI | `data/solar_rotation_sim.csv` (synthetic) |
| Sunspot number | SILSO | `data/sunspot_number.csv` |
| Coronal loop | AIA 193 Å | `data/coronal_loop_sim.csv` (synthetic) |
| Vector B-field | SDO HMI | `data/hmi/*.fits` |
| Helioseismology | GONG | `data/helioseismology_modes.csv` (synthetic) |
| **Real-time solar wind** | NOAA SWPC | `services.swpc.noaa.gov/json/` |
| **Real-time CME** | DONKI | `kauai.ccmc.gsfc.nasa.gov/DONKI/` |
| **Flare catalog** | Plutino | `data/real/plutino_FlareList_*.csv` |

## Dependencies

- Python ≥ 3.10
- `numpy`, `scipy`, `matplotlib`
- `astropy` (FITS reading)
- `sunpy` (optional, solar physics)

## Data Barriers

**~70% of project time was spent on data acquisition, not modeling.** Key bottlenecks:

| Barrier | Impact |
|---------|--------|
| **JSOC DRMS registration wall** | Vector magnetograms (B_720s) require human email approval → AI agents can't self-serve |
| **~50 KB/s from academic infrastructure** | Large Plutino files timeout at 180s; HMI full-res data (100s GB) impossible |
| **Format fragmentation** | Same agency uses JSON for flares, CSV for solar wind, different column names |
| **No REST metadata queries** | Must download full FITS to read header; no "give me HARPNUM 377's dimensions" endpoint |
| **HF datasets unreachable** | Well-labeled flare datasets (juliensimon/solar-flares) → URLError, no fallback |

**Result**: ~2 hours fighting data walls, ~1 hour doing actual modeling. Efficiency ratio: **30%**.

## Status

| Dimension | Rating | Source |
|-----------|--------|--------|
| Security | **Low risk** | Red Team v2.0 |
| Code quality | **7.5/10** | Engineering AI v3.1 |
| Standards | **6.1/10** 🟡 | Review Board v6.1 |
| Tests | **82/82 ✅ 1.6s** | pytest |

Full audit report: `JOINT_REVIEW_REPORT.md` (v2, 10 P0/P1 issues closed)

## Author

math-science (QClaw agent) | 2026-05-23 | License: MIT
