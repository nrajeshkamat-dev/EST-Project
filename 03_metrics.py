"""Step 3: rate of change, climate lags (RQ1) and no-analogue communities (RQ2).

  python 03_metrics.py [--binned binned.csv] [--tag base]
"""
import argparse, itertools, json
import numpy as np
import pandas as pd
from scipy import stats
import config as C
from lib import COLS, hellinger, scd_matrix, ensure_dirs


def rate_of_change(b, clim_reg):
    rows = []
    for sid, s in b.groupby("site_id"):
        s = s.sort_values("bin_age", ascending=False)          # oldest -> youngest
        X, ages = s[COLS].values, s.bin_age.values
        for i in range(1, len(s)):
            dt = ages[i - 1] - ages[i]
            if dt == C.BIN_WIDTH:                                # adjacent bins only
                rows.append(dict(site_id=sid, bin_age=(ages[i] + ages[i - 1]) / 2,
                                 hellinger=hellinger(X[i - 1], X[i]),
                                 rate_per_century=hellinger(X[i - 1], X[i]) / dt * 100))
    r = pd.DataFrame(rows)
    c = clim_reg.sort_values("bin_age", ascending=False).reset_index(drop=True)
    c["bin_mid"] = (c.bin_age + c.bin_age.shift(-1)) / 2
    # rows run oldest -> youngest, so shift(-1) is the next (younger) bin: positive = warming
    c["climate_rate_c_per_century"] = (c.temp_c.shift(-1) - c.temp_c) / C.BIN_WIDTH * 100
    c = c.dropna(subset=["bin_mid"])
    return r, c[["bin_mid", "climate_rate_c_per_century"]].rename(columns={"bin_mid": "bin_age"})


def best_lag(veg, temp):
    """veg, temp in chronological order. Return (lag_bins, r): vegetation[t] vs temp[t-k]."""
    best = (None, 0.0)
    for k in range(0, C.MAX_LAG_BINS + 1):
        v, t = (veg[k:], temp[: len(temp) - k]) if k else (veg, temp)
        if len(v) < C.MIN_BINS_LAG - C.MAX_LAG_BINS or np.std(v) == 0 or np.std(t) == 0:
            continue
        r = np.corrcoef(v, t)[0, 1]
        if abs(r) > abs(best[1]):
            best = (k, r)
    return best


def lags(b, clim_sites):
    rows = []
    cs = clim_sites.set_index(["site_id", "bin_age"]).temp_c
    for sid, s in b.groupby("site_id"):
        s = s.sort_values("bin_age", ascending=False)
        t = np.array([cs.get((sid, a), np.nan) for a in s.bin_age])
        good = ~np.isnan(t)
        s, t = s[good], t[good]
        if len(s) < C.MIN_BINS_LAG:
            continue
        for g in C.GENERA:
            v = s[g].values
            if v.mean() < C.MIN_MEAN_PROP:
                continue
            k, r = best_lag(v, t)
            if k is not None:
                rows.append(dict(site_id=sid, genus=g, lag_bins=k, lag_years=k * C.BIN_WIDTH, r=r, n_bins=len(s)))
    return pd.DataFrame(rows)


def lag_summary(L, n_boot=2000, seed=0):
    rng = np.random.default_rng(seed)
    out = []
    for g, d in L.groupby("genus"):
        x = d.lag_years.values
        if len(x) < 5:
            continue
        boots = [np.median(rng.choice(x, len(x))) for _ in range(n_boot)]
        out.append(dict(genus=g, n_sites=len(x), median_lag_yr=np.median(x),
                        ci_low=np.percentile(boots, 2.5), ci_high=np.percentile(boots, 97.5)))
    S = pd.DataFrame(out).sort_values("median_lag_yr")
    groups = [d.lag_years.values for _, d in L.groupby("genus") if len(d) >= 5]
    tests = {}
    if len(groups) > 1:
        H, p = stats.kruskal(*groups)
        tests["kruskal_H"], tests["kruskal_p"] = float(H), float(p)
        gl = [g for g, d in L.groupby("genus") if len(d) >= 5]
        pairs = list(itertools.combinations(range(len(gl)), 2))
        pw = []
        for i, j in pairs:
            u, p = stats.mannwhitneyu(groups[i], groups[j])
            pw.append(dict(a=gl[i], b=gl[j], p_raw=p, p_bonf=min(1, p * len(pairs))))
        tests["pairwise"] = pw
    return S, tests


def no_analogue(b, modern):
    M = modern[COLS].values
    nn = scd_matrix(M, M)
    np.fill_diagonal(nn, np.inf)
    thr = np.percentile(nn.min(axis=1), C.NOANALOG_PERCENTILE)
    F = b[COLS].values
    d = scd_matrix(F, M).min(axis=1)
    out = b[["site_id", "bin_age"]].copy()
    out["scd_to_modern"], out["no_analogue"] = d, d > thr
    return out, float(thr)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--binned", default="binned.csv")
    ap.add_argument("--tag", default="base")
    a = ap.parse_args()
    ensure_dirs()
    b = pd.read_csv(C.PROC / a.binned)
    creg = pd.read_csv(C.PROC / "climate_regional.csv")
    csite = pd.read_csv(C.PROC / "climate_sites.csv")
    modern = pd.read_csv(C.PROC / "modern.csv")

    roc, crate = rate_of_change(b, creg)
    roc.to_csv(C.OUT / f"rate_of_change_{a.tag}.csv", index=False)
    crate.to_csv(C.OUT / f"climate_rate_{a.tag}.csv", index=False)

    L = lags(b, csite)
    L.to_csv(C.OUT / f"lags_{a.tag}.csv", index=False)
    S, tests = lag_summary(L)
    S.to_csv(C.OUT / f"lag_summary_{a.tag}.csv", index=False)
    print(S.to_string(index=False))

    na, thr = no_analogue(b, modern)
    na.to_csv(C.OUT / f"no_analogue_{a.tag}.csv", index=False)
    frac = na.groupby("bin_age").no_analogue.mean().rename("frac_no_analogue").reset_index()
    vr = roc.groupby("bin_age").rate_per_century.median().rename("median_veg_rate").reset_index()
    # Climate and vegetation rates belong to the interval BETWEEN two bins (labelled by its midpoint);
    # no-analogue fractions belong to bins. Give each interval the mean of its two bracketing bins.
    fr = frac.set_index("bin_age").frac_no_analogue
    m = crate.copy()
    m["frac_no_analogue"] = [np.nanmean([fr.get(x - C.BIN_WIDTH / 2, np.nan), fr.get(x + C.BIN_WIDTH / 2, np.nan)])
                             for x in m.bin_age]
    m = m.dropna(subset=["frac_no_analogue"]).merge(vr, on="bin_age", how="left")
    m["abs_climate_rate"] = m.climate_rate_c_per_century.abs()
    rho1, p1 = stats.spearmanr(m.frac_no_analogue, m.abs_climate_rate, nan_policy="omit")
    mm = m.dropna(subset=["median_veg_rate"])
    rho2, p2 = stats.spearmanr(mm.frac_no_analogue, mm.median_veg_rate)
    tests.update(dict(no_analogue_threshold_scd=thr,
                      spearman_noanalogue_vs_abs_climate_rate=[float(rho1), float(p1)],
                      spearman_noanalogue_vs_veg_rate=[float(rho2), float(p2)],
                      n_sites=int(b.site_id.nunique()), n_time_bins=int(len(m)),
                      note="p-values ignore temporal autocorrelation; treat as indicative"))
    json.dump(tests, open(C.OUT / f"tests_{a.tag}.json", "w"), indent=2)
    m.to_csv(C.OUT / f"noanalogue_vs_climate_{a.tag}.csv", index=False)
    print(json.dumps({k: v for k, v in tests.items() if k != "pairwise"}, indent=2))
