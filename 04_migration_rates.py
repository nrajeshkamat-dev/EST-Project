"""Step 4: northward migration rates per genus (RQ3) and comparison with climate velocity.

Arrival = first time (going forward) proportion >= ARRIVAL_THRESHOLD for 2 consecutive bins.
Sites where the genus is already present in their oldest bin are excluded (arrival not observed).
Rate = 1 / |slope| of arrival age against northward distance.
Climate velocity (km/yr) = climate rate (C/yr) / spatial gradient (C/km): how fast a site's climate
moves across the landscape, i.e. the speed a tree would need to keep up.
"""
import argparse, json
import numpy as np
import pandas as pd
from scipy import stats
import config as C
from lib import ensure_dirs


def arrival_age(s, g):
    s = s.sort_values("bin_age", ascending=False)
    v, a = s[g].values, s.bin_age.values
    hit = v >= C.ARRIVAL_THRESHOLD
    if hit[0]:
        return np.nan                                  # already present at start: censored
    for i in range(len(v) - 1):
        if hit[i] and hit[i + 1]:
            return a[i]
    return np.nan


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--binned", default="binned.csv")
    ap.add_argument("--tag", default="base")
    a = ap.parse_args()
    ensure_dirs()
    b = pd.read_csv(C.PROC / a.binned)
    lat0 = b.lat.min()
    rng = np.random.default_rng(0)
    rows, arr_rows = [], []
    for g in C.GENERA:
        recs = [(sid, s.lat.iloc[0], arrival_age(s, g)) for sid, s in b.groupby("site_id")]
        d = pd.DataFrame(recs, columns=["site_id", "lat", "arrival_age"]).dropna()
        d["dist_km"] = (d.lat - lat0) * 111.2
        d["genus"] = g
        arr_rows.append(d)
        if len(d) < C.MIN_SITES_MIGRATION:
            continue
        fit = stats.linregress(d.dist_km, d.arrival_age)
        if fit.slope >= 0 or fit.pvalue > 0.05:
            rows.append(dict(genus=g, n_sites=len(d), rate_m_per_yr=np.nan, ci_low=np.nan, ci_high=np.nan, p=fit.pvalue))
            continue
        boots = []
        for _ in range(1000):
            i = rng.integers(0, len(d), len(d))
            f = stats.linregress(d.dist_km.values[i], d.arrival_age.values[i])
            if f.slope < 0:
                boots.append(1000 / abs(f.slope))
        rows.append(dict(genus=g, n_sites=len(d), rate_m_per_yr=1000 / abs(fit.slope),
                         ci_low=np.percentile(boots, 2.5) if boots else np.nan,
                         ci_high=np.percentile(boots, 97.5) if boots else np.nan, p=fit.pvalue))
    R = pd.DataFrame(rows)
    R.to_csv(C.OUT / f"migration_{a.tag}.csv", index=False)
    pd.concat(arr_rows).to_csv(C.OUT / f"arrivals_{a.tag}.csv", index=False)
    print(R.to_string(index=False))

    grad = abs(json.load(open(C.PROC / "gradient.json"))["deg_c_per_km"])
    cr = pd.read_csv(C.OUT / f"climate_rate_{a.tag}.csv").climate_rate_c_per_century.abs()
    vel = lambda rate_c_per_century: rate_c_per_century / 100 / grad * 1000      # m/yr
    comp = dict(spatial_gradient_c_per_km=grad,
                past_median_climate_velocity_m_per_yr=float(vel(cr.median())),
                past_p95_climate_velocity_m_per_yr=float(vel(np.percentile(cr.dropna(), 95))),
                past_max_climate_velocity_m_per_yr=float(vel(cr.max())),
                modern_warming_c_per_century=C.MODERN_WARMING_C_PER_CENTURY,
                modern_climate_velocity_m_per_yr=float(vel(C.MODERN_WARMING_C_PER_CENTURY)),
                median_genus_migration_m_per_yr=float(R.rate_m_per_yr.median()) if R.rate_m_per_yr.notna().any() else None,
                note="Modern rate uses the value in config.py; cite the stated source. Past rates are averaged over %d-yr bins and so UNDERSTATE faster, shorter-lived change; the comparison with modern warming is therefore conservative." % C.BIN_WIDTH)
    json.dump(comp, open(C.OUT / f"velocity_comparison_{a.tag}.json", "w"), indent=2)
    print(json.dumps(comp, indent=2))
