"""SYNTHETIC test suite with KNOWN ground truth to verify Phase 1 pipeline logic.

Usage:
  python synthetic_demo.py           # writes synthetic processed files under DATA_DIR=data_demo
  python synthetic_demo.py --verify  # runs automated PASS/FAIL assertions on lags, Ebisuzaki, 2D migration, PRECT & UPHE
"""
import argparse
import importlib
import json
import os
os.environ.setdefault("DATA_DIR", "data_demo")

import numpy as np
import pandas as pd
from scipy.special import expit
import config as C
from lib import ensure_dirs, site_bins, ebisuzaki_p, COLS

OPT = dict(Picea=-1, Abies=2, Larix=0, Betula=3, Pinus=5, Tsuga=6, Alnus=4, Populus=4,
           Acer=7, Quercus=8, Fagus=8, Fraxinus=8, Ulmus=8, Carya=9)
LAG = dict(Picea=500, Abies=500, Larix=0, Betula=500, Pinus=500, Tsuga=1500, Alnus=0, Populus=0,
           Acer=1000, Quercus=1000, Fagus=2500, Fraxinus=1000, Ulmus=1000, Carya=1500)
MIG_M_PER_YR = 200.0


def regional_T(a):
    return (
        8
        - 10 * expit((a - 11500) / 900)
        - 2.2 * np.exp(-((a - 12000) / 400) ** 2)
        - 1.6 * np.exp(-((a - 8200) / 350) ** 2)
        + 1.4 * np.exp(-((a - 5200) / 450) ** 2)
    )


def regional_P(a):
    return 2.5 + 0.6 * (1 - expit((a - 11500) / 1000)) - 0.35 * np.exp(-((a - 12000) / 450) ** 2)


def generate_synthetic(seed=42):
    rng = np.random.default_rng(seed)
    ensure_dirs()
    centres = site_bins()
    ns = 60
    lats = rng.uniform(34, 50, ns)
    lons = rng.uniform(-95, -65, ns)

    def props(lat, lon, a):
        t_site = lambda age: regional_T(age) - 0.5 * (lat - 40)
        w = {g: np.exp(-((t_site(a + LAG[g]) - OPT[g]) / 4.0) ** 2) + 0.01 for g in C.GENERA}
        # Plant northward wave for Quercus (200 m/yr) and NW (315 deg) wave for Fagus (200 m/yr)
        arr_q = 13000 - (lat - 34) * 111.2 / (MIG_M_PER_YR / 1000.0)
        w["Quercus"] *= expit((arr_q - a) / 150.0)
        d_nw_km = ((lat - 34) * 111.32 - (lon + 65) * 111.32 * np.cos(np.radians(42.0))) / np.sqrt(2.0)
        arr_f = 13500 - d_nw_km / (MIG_M_PER_YR / 1000.0)
        w["Fagus"] *= expit((arr_f - a) / 150.0)
        w["Other"] = 0.1
        v = np.array([w[c] for c in COLS])
        return v / v.sum()

    rows = []
    for i in range(ns):
        for a in centres:
            if rng.random() < 0.05:
                continue
            cnt = rng.multinomial(400, props(lats[i], lons[i], a))
            rows.append([i, lats[i], lons[i], a] + list(cnt / cnt.sum()) + [400])
    b = pd.DataFrame(rows, columns=["site_id", "lat", "lon", "bin_age"] + COLS + ["n_grains"])
    b.to_csv(C.PROC / "binned.csv", index=False)
    b.groupby("site_id")[["lat", "lon"]].first().reset_index().to_csv(C.PROC / "sites.csv", index=False)

    mod = []
    for j in range(150):
        i = rng.integers(ns)
        cnt = rng.multinomial(400, props(lats[i], lons[i], 250))
        mod.append([1000 + j, lats[i], lons[i]] + list(cnt / cnt.sum()))
    pd.DataFrame(mod, columns=["site_id", "lat", "lon"] + COLS).to_csv(C.PROC / "modern.csv", index=False)

    pd.DataFrame({"bin_age": centres, "temp_c": regional_T(centres), "precip_mm_day": regional_P(centres)}).to_csv(C.PROC / "climate_regional.csv", index=False)
    cs = [
        dict(site_id=i, bin_age=a, temp_c=regional_T(a) - 0.5 * (lats[i] - 40), precip_mm_day=regional_P(a) + 0.02 * (lons[i] + 80))
        for i in range(ns) for a in centres
    ]
    pd.DataFrame(cs).to_csv(C.PROC / "climate_sites.csv", index=False)
    (C.PROC / "gradient.json").write_text(json.dumps({
        "deg_c_per_km": -0.5 / 111.2,
        "deg_c_per_km_2d_mag": 0.5 / 111.2,
        "precip_mm_day_per_km_2d_mag": 0.00024,
    }, indent=2), encoding="utf-8")
    print(f"[synthetic] data written to {C.DATA}")


def verify_synthetic():
    generate_synthetic(seed=42)
    met = importlib.import_module("03_metrics")
    mig = importlib.import_module("04_migration_rates")
    pp = importlib.import_module("02_preprocess")

    b = pd.read_csv(C.PROC / "binned.csv")
    cs = pd.read_csv(C.PROC / "climate_sites.csv")
    mod = pd.read_csv(C.PROC / "modern.csv")

    # 1. Stationary lag recovery (+-500 yr) & PRECT lag non-empty check
    L = met.compute_lags(b, cs, bw=C.BIN_WIDTH, lag_mode="diff", clim_col="temp_c", ebisuzaki_n=200, seed=0)
    S, _ = met.lag_summary(L, n_boot=200)
    s_map = S.set_index("genus").median_lag_yr.to_dict()
    for g in ("Picea", "Pinus", "Acer", "Tsuga", "Carya", "Fagus"):
        err = abs(s_map[g] - LAG[g])
        assert err <= 500.0, f"Lag recovery mismatch for {g}: got {s_map[g]}, truth {LAG[g]}"
    Lp = met.compute_lags(b, cs, bw=C.BIN_WIDTH, lag_mode="diff", clim_col="precip_mm_day", ebisuzaki_n=100, seed=1)
    assert len(Lp) > 50, f"PRECT synthetic lag pairs too small: {len(Lp)}"

    # 2. Ebisuzaki null calibration on 40 independent AR(1) random-walk pairs (<=15% false positives at p<0.05)
    rng_rw = np.random.default_rng(123)
    fp = 0
    n_trials = 40
    for _ in range(n_trials):
        x, y = np.zeros(30), np.zeros(30)
        ex, ey = rng_rw.normal(size=30), rng_rw.normal(size=30)
        for t in range(1, 30):
            x[t] = 0.85 * x[t - 1] + ex[t]
            y[t] = 0.85 * y[t - 1] + ey[t]
        if ebisuzaki_p(np.diff(x), np.diff(y), n_sim=300, rng=rng_rw) < 0.05:
            fp += 1
    fpr = fp / n_trials
    assert fpr <= 0.125, f"Ebisuzaki AR(1) false positive rate too high: {fpr:.3f} ({fp}/{n_trials})"

    # 3. 2D arrival speed recovery (+-15% of 200 m/yr) for N (Quercus) & NW (Fagus)
    for g, exp_az_lo, exp_az_hi in [("Quercus", 340, 20), ("Fagus", 295, 335)]:
        recs = [(sid, s.lat.iloc[0], s.lon.iloc[0], mig.arrival_age(s, g)) for sid, s in b.groupby("site_id")]
        d = pd.DataFrame(recs, columns=["site_id", "lat", "lon", "arrival_age"]).dropna()
        m2, _ = mig.fit_migration_2d(d, g)
        sp = m2["rate_2d_median_m_per_yr"]
        az = m2["mean_azimuth_deg"]
        assert m2["p_2d"] < 0.01 and abs(sp - MIG_M_PER_YR) / MIG_M_PER_YR <= 0.15, f"2D speed fail {g}: {sp:.1f}"
        az_ok = (az >= exp_az_lo or az <= exp_az_hi) if exp_az_lo > exp_az_hi else (exp_az_lo <= az <= exp_az_hi)
        assert az_ok, f"2D azimuth fail {g}: {az:.1f}"

    # 4. UPHE weed contamination test: modern UPHE inflates no-analogue vs TRSH-only
    b_uphe = b.copy()
    m_uphe = mod.copy()
    b_uphe[COLS] = b_uphe[COLS].mul(0.85, axis=0)
    b_uphe["Other"] = b_uphe["Other"] + 0.15
    m_uphe[COLS] = m_uphe[COLS].mul(0.35, axis=0)
    m_uphe["Other"] = m_uphe["Other"] + 0.65
    na_trsh, _ = met.no_analogue(b[b.bin_age == 250], mod)[:2]
    na_weed, _ = met.no_analogue(b_uphe[b_uphe.bin_age == 250], m_uphe)[:2]
    assert na_weed.no_analogue.mean() > na_trsh.no_analogue.mean() + 0.30, "UPHE weed test failed to trigger elevated 250 BP no-analogue"

    # Also verify counts_table(..., trsh_only=True) strips UPHE rows cleanly
    synth_long = pd.DataFrame([
        {"dataset_id": 1, "lat": 42.0, "lon": -80.0, "depth": 10.0, "age_bp": 500.0, "taxon": "Quercus", "group": "TRSH", "count": 120},
        {"dataset_id": 1, "lat": 42.0, "lon": -80.0, "depth": 10.0, "age_bp": 500.0, "taxon": "Ambrosia-type", "group": "UPHE", "count": 200},
    ])
    kept, _ = pp.counts_table(synth_long, trsh_only=True)
    assert float(kept["Other"].iloc[0]) == 0.0 and float(kept["Quercus"].iloc[0]) == 120.0

    print(f"SYNTHETIC_VERIFY_OK: lags={{{', '.join(f'{k}:{s_map[k]:.0f}' for k in ('Picea','Quercus','Fagus','Tsuga'))}}}, rw_fpr={fpr:.3f}, prect_pairs={len(Lp)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    if a.verify:
        verify_synthetic()
    else:
        generate_synthetic()
