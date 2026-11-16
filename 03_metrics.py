"""Step 3: rate of change, climate lags (RQ1) and no-analogue communities (RQ2).

Supports Phase 1 modes:
  --lag-mode {raw,diff}  level correlations vs first-differenced stationary series
  --ebisuzaki-n N        FFT phase-randomized surrogates for autocorrelation-valid p-values
  --bin-width N          bin width in years (default config.BIN_WIDTH)
"""
import argparse, itertools, json
import numpy as np
import pandas as pd
from scipy import stats
import config as C
from lib import COLS, hellinger, scd_matrix, ensure_dirs, ebisuzaki_p


def rate_of_change(b, clim_reg, bw=C.BIN_WIDTH):
    rows = []
    for sid, s in b.groupby("site_id"):
        s = s.sort_values("bin_age", ascending=False)          # oldest -> youngest
        X, ages = s[COLS].values, s.bin_age.values
        for i in range(1, len(s)):
            dt = ages[i - 1] - ages[i]
            if dt == bw:                                       # adjacent bins only
                h = hellinger(X[i - 1], X[i])
                rows.append(dict(site_id=sid, bin_age=(ages[i] + ages[i - 1]) / 2,
                                 hellinger=h, rate_per_century=h / dt * 100))
    r = pd.DataFrame(rows)
    c = clim_reg.sort_values("bin_age", ascending=False).reset_index(drop=True)
    c["bin_mid"] = (c.bin_age + c.bin_age.shift(-1)) / 2
    # oldest -> youngest: shift(-1) is younger bin, so positive = warming / wetting
    c["climate_rate_c_per_century"] = (c.temp_c.shift(-1) - c.temp_c) / bw * 100
    cols_out = ["bin_mid", "climate_rate_c_per_century"]
    if "precip_mm_day" in c.columns:
        c["precip_rate_mm_day_per_century"] = (c.precip_mm_day.shift(-1) - c.precip_mm_day) / bw * 100
        cols_out.append("precip_rate_mm_day_per_century")
    c = c.dropna(subset=["bin_mid"])
    return r, c[cols_out].rename(columns={"bin_mid": "bin_age"})


def _best_lag_pair(veg, clim, lag_mode, min_bins_lag, max_lag_bins, ebisuzaki_n, rng):
    """veg, clim are evenly spaced on regular bw grid in chronological order (oldest -> youngest)."""
    v_s, c_s = (np.diff(veg), np.diff(clim)) if lag_mode == "diff" else (veg, clim)
    min_pairs = max(6, min_bins_lag - max_lag_bins)
    best = (None, 0.0, None, None, 0)
    for k in range(0, max_lag_bins + 1):
        vp, cp = (v_s[k:], c_s[: len(c_s) - k]) if k else (v_s, c_s)
        valid = (~np.isnan(vp)) & (~np.isnan(cp))
        n_ok = int(valid.sum())
        if n_ok < min_pairs:
            continue
        vv, cv = vp[valid], cp[valid]
        if np.std(vv) == 0 or np.std(cv) == 0:
            continue
        r = float(np.corrcoef(vv, cv)[0, 1])
        if abs(r) > abs(best[1]):
            best = (k, r, vv, cv, n_ok)
    k, r, vv, cv, n_ok = best
    if k is None:
        return None
    p_eb = ebisuzaki_p(cv, vv, r_obs=r, n_sim=ebisuzaki_n, method="pearson", rng=rng) if ebisuzaki_n > 0 else np.nan
    return k, r, n_ok, p_eb


def compute_lags(b, clim_sites, bw=C.BIN_WIDTH, lag_mode="raw", clim_col="temp_c",
                 ebisuzaki_n=C.EBISUZAKI_N, seed=0):
    if clim_col not in clim_sites.columns:
        return pd.DataFrame()
    rng = np.random.default_rng(seed)
    scale = 500.0 / bw
    min_bins_lag = max(C.MIN_BINS_LAG, int(round(C.MIN_BINS_LAG * scale)))
    max_lag_bins = max(1, int(round(C.MAX_LAG_BINS * scale)))

    cs = clim_sites.set_index(["site_id", "bin_age"])[clim_col]
    rows = []
    for sid, s in b.groupby("site_id"):
        s = s.sort_values("bin_age", ascending=False)
        t_vals = np.array([cs.get((sid, a), np.nan) for a in s.bin_age], dtype=float)
        good = ~np.isnan(t_vals)
        s = s[good]
        if len(s) < min_bins_lag:
            continue
        # Reindex onto regular descending bin grid so interior gaps stay NaN for first-differencing
        grid_ages = np.arange(float(s.bin_age.max()), float(s.bin_age.min()) - 0.5 * bw, -bw)
        clim_map = dict(zip(s.bin_age.values, t_vals[good]))
        clim_grid = np.array([clim_map.get(a, np.nan) for a in grid_ages], dtype=float)
        for g in C.GENERA:
            v_obs = s[g].values
            if v_obs.mean() < C.MIN_MEAN_PROP:
                continue
            veg_map = dict(zip(s.bin_age.values, v_obs))
            veg_grid = np.array([veg_map.get(a, np.nan) for a in grid_ages], dtype=float)
            res = _best_lag_pair(veg_grid, clim_grid, lag_mode, min_bins_lag, max_lag_bins, ebisuzaki_n, rng)
            if res is not None:
                k, r, n_pairs, p_eb = res
                rows.append(dict(
                    site_id=sid, genus=g, lag_bins=k, lag_years=k * bw, r=r,
                    n_bins=len(s), n_pairs=n_pairs, p_ebisuzaki=p_eb,
                    sig_05=bool(not np.isnan(p_eb) and p_eb < 0.05),
                ))
    return pd.DataFrame(rows)


def lag_summary(L, n_boot=2000, seed=0):
    rng = np.random.default_rng(seed)
    out = []
    if len(L) == 0:
        return pd.DataFrame(), {}
    for g, d in L.groupby("genus"):
        x = d.lag_years.values
        if len(x) < 5:
            continue
        boots = [np.median(rng.choice(x, len(x))) for _ in range(n_boot)] if n_boot > 0 else []
        sig = d[d.p_ebisuzaki < 0.05] if "p_ebisuzaki" in d.columns else d.iloc[0:0]
        n_sig = int(len(sig))
        out.append(dict(
            genus=g,
            n_sites=len(x),
            n_sig_05=n_sig,
            pct_sig_05=round(n_sig / len(x), 4),
            median_lag_yr=float(np.median(x)),
            ci_low=float(np.percentile(boots, 2.5)) if boots else np.nan,
            ci_high=float(np.percentile(boots, 97.5)) if boots else np.nan,
            median_lag_sig_yr=float(np.median(sig.lag_years.values)) if n_sig else np.nan,
            frac_pos_r=round(float((d.r >= 0).mean()), 4),
            mean_r=round(float(d.r.mean()), 4),
        ))
    S = pd.DataFrame(out).sort_values("median_lag_yr") if out else pd.DataFrame()
    groups = [d.lag_years.values for _, d in L.groupby("genus") if len(d) >= 5]
    tests = {}
    if len(groups) > 1:
        H, p = stats.kruskal(*groups)
        tests["kruskal_H"], tests["kruskal_p"] = float(H), float(p)
        gl = [g for g, d in L.groupby("genus") if len(d) >= 5]
        pairs = list(itertools.combinations(range(len(gl)), 2))
        pw = []
        for i, j in pairs:
            u, pv = stats.mannwhitneyu(groups[i], groups[j])
            pw.append(dict(a=gl[i], b=gl[j], p_raw=pv, p_bonf=min(1, pv * len(pairs))))
        tests["pairwise"] = pw
    return S, tests


def no_analogue(b, modern):
    M = modern[COLS].values
    nn = scd_matrix(M, M)
    np.fill_diagonal(nn, np.inf)
    thr = np.percentile(nn.min(axis=1), C.NOANALOG_PERCENTILE)
    F = b[COLS].values
    dmat = scd_matrix(F, M)
    nn_idx = dmat.argmin(axis=1)
    d = dmat[np.arange(len(F)), nn_idx]
    out = b[["site_id", "bin_age"]].copy()
    out["scd_to_modern"], out["no_analogue"] = d, d > thr
    # Per-taxon squared chord distance attribution relative to nearest modern sample
    comp = (np.sqrt(F) - np.sqrt(M[nn_idx])) ** 2
    drv_raw = pd.DataFrame(comp, columns=COLS)
    drv_raw["bin_age"] = b["bin_age"].values
    drv = drv_raw.groupby("bin_age")[COLS].mean().reset_index().sort_values("bin_age", ascending=False)
    return out, float(thr), drv


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--binned", default="binned.csv")
    ap.add_argument("--modern", default="modern.csv")
    ap.add_argument("--climate-regional", default="climate_regional.csv")
    ap.add_argument("--climate-sites", default="climate_sites.csv")
    ap.add_argument("--tag", default="base")
    ap.add_argument("--bin-width", type=int, default=C.BIN_WIDTH)
    ap.add_argument("--lag-mode", choices=["raw", "diff"], default="raw")
    ap.add_argument("--ebisuzaki-n", type=int, default=C.EBISUZAKI_N)
    a = ap.parse_args()
    ensure_dirs()
    bw = int(a.bin_width)
    b = pd.read_csv(C.PROC / a.binned)
    creg = pd.read_csv(C.PROC / a.climate_regional)
    csite = pd.read_csv(C.PROC / a.climate_sites)
    modern = pd.read_csv(C.PROC / a.modern)

    roc, crate = rate_of_change(b, creg, bw=bw)
    roc.to_csv(C.OUT / f"rate_of_change_{a.tag}.csv", index=False)
    crate.to_csv(C.OUT / f"climate_rate_{a.tag}.csv", index=False)

    L = compute_lags(b, csite, bw=bw, lag_mode=a.lag_mode, clim_col="temp_c", ebisuzaki_n=a.ebisuzaki_n, seed=0)
    L.to_csv(C.OUT / f"lags_{a.tag}.csv", index=False)
    S, tests = lag_summary(L)
    S.to_csv(C.OUT / f"lag_summary_{a.tag}.csv", index=False)
    print(S.to_string(index=False))

    if "precip_mm_day" in csite.columns:
        Lp = compute_lags(b, csite, bw=bw, lag_mode=a.lag_mode, clim_col="precip_mm_day", ebisuzaki_n=a.ebisuzaki_n, seed=1)
        Lp.to_csv(C.OUT / f"lags_precip_{a.tag}.csv", index=False)
        Sp, tests_p = lag_summary(Lp)
        Sp.to_csv(C.OUT / f"lag_summary_precip_{a.tag}.csv", index=False)
        tests["precip_kruskal_p"] = tests_p.get("kruskal_p")
        tests["precip_n_pairs"] = int(len(Lp))
        tests["precip_ebisuzaki_pass_rate_p05"] = float((Lp.p_ebisuzaki < 0.05).mean()) if len(Lp) else None

    na, thr, drv = no_analogue(b, modern)
    na.to_csv(C.OUT / f"no_analogue_{a.tag}.csv", index=False)
    drv.to_csv(C.OUT / f"no_analogue_drivers_{a.tag}.csv", index=False)
    frac = na.groupby("bin_age").no_analogue.mean().rename("frac_no_analogue").reset_index()
    vr = roc.groupby("bin_age").rate_per_century.median().rename("median_veg_rate").reset_index()
    fr = frac.set_index("bin_age").frac_no_analogue
    m = crate.copy()
    fna_vals = []
    for x in m.bin_age:
        pair = [fr.get(x - bw / 2, np.nan), fr.get(x + bw / 2, np.nan)]
        valid_p = [v for v in pair if not np.isnan(v)]
        fna_vals.append(float(np.mean(valid_p)) if valid_p else np.nan)
    m["frac_no_analogue"] = fna_vals
    m = m.dropna(subset=["frac_no_analogue"]).merge(vr, on="bin_age", how="left")
    m["abs_climate_rate"] = m.climate_rate_c_per_century.abs()
    rho1, p1 = stats.spearmanr(m.frac_no_analogue, m.abs_climate_rate, nan_policy="omit")
    mm = m.dropna(subset=["median_veg_rate"])
    rho2, p2 = stats.spearmanr(mm.frac_no_analogue, mm.median_veg_rate)

    rng_eb = np.random.default_rng(42)
    n_eb = max(a.ebisuzaki_n, 1000) if a.ebisuzaki_n > 0 else 0
    eb_clim = ebisuzaki_p(m.abs_climate_rate.values, m.frac_no_analogue.values, r_obs=rho1, n_sim=n_eb, method="spearman", rng=rng_eb) if n_eb else np.nan
    eb_veg = ebisuzaki_p(mm.median_veg_rate.values, mm.frac_no_analogue.values, r_obs=rho2, n_sim=n_eb, method="spearman", rng=rng_eb) if n_eb else np.nan

    tests.update(dict(
        lag_mode=a.lag_mode,
        ebisuzaki_n=a.ebisuzaki_n,
        no_analogue_threshold_scd=thr,
        spearman_noanalogue_vs_abs_climate_rate=[float(rho1), float(p1)],
        spearman_noanalogue_vs_veg_rate=[float(rho2), float(p2)],
        ebisuzaki_p_climate=float(eb_clim) if not np.isnan(eb_clim) else None,
        ebisuzaki_p_veg=float(eb_veg) if not np.isnan(eb_veg) else None,
        n_sites=int(b.site_id.nunique()),
        n_time_bins=int(len(m)),
        note=f"lag_mode={a.lag_mode}; Ebisuzaki phase-randomization (N={a.ebisuzaki_n}) accounts for temporal autocorrelation.",
    ))
    json.dump(tests, open(C.OUT / f"tests_{a.tag}.json", "w"), indent=2)
    m.to_csv(C.OUT / f"noanalogue_vs_climate_{a.tag}.csv", index=False)
    print(json.dumps({k: v for k, v in tests.items() if k != "pairwise"}, indent=2))
