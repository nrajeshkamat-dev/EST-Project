"""Step 4: 1D northward & 2D equal-area spatial migration rates (RQ3) vs climate velocity.

Supports:
  --bin-width N         override bin width for metadata/climate velocity note
  --climate-rate FILE   override climate_rate CSV path (relative to data/outputs)
  --mode2d              compute 2D thin-plate spline arrival isochrones & azimuths (auto-enabled when lon present)
"""
import argparse, json
import numpy as np
import pandas as pd
from scipy import stats
from scipy.interpolate import RBFInterpolator
from scipy.spatial import Delaunay
import config as C
from lib import ensure_dirs, latlon_to_xy_km


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


def fit_migration_1d(d, lat0, rng):
    d = d.copy()
    d["dist_km"] = (d.lat - lat0) * 111.2
    fit = stats.linregress(d.dist_km, d.arrival_age)
    if fit.slope >= 0 or fit.pvalue > 0.05:
        return dict(rate_m_per_yr=np.nan, ci_low=np.nan, ci_high=np.nan, p=float(fit.pvalue))
    boots = []
    for _ in range(1000):
        idx = rng.integers(0, len(d), len(d))
        f = stats.linregress(d.dist_km.values[idx], d.arrival_age.values[idx])
        if f.slope < 0:
            boots.append(1000.0 / abs(f.slope))
    return dict(
        rate_m_per_yr=float(1000.0 / abs(fit.slope)),
        ci_low=float(np.percentile(boots, 2.5)) if boots else np.nan,
        ci_high=float(np.percentile(boots, 97.5)) if boots else np.nan,
        p=float(fit.pvalue),
    )


def fit_migration_2d(d, genus, grid_n=25):
    """Fit 2D equal-area planar F-test + smooth TPS arrival surface arrival_age(x_km, y_km)."""
    xk, yk, lat0, lon0 = latlon_to_xy_km(d.lat.values, d.lon.values)
    pts_xy = np.column_stack([xk, yk])
    y_age = d.arrival_age.values
    # 2D planar F-test: tests whether any directional spatial migration trend exists
    X_lin = np.column_stack([np.ones(len(d)), xk, yk])
    coef, *_ = np.linalg.lstsq(X_lin, y_age, rcond=None)
    yhat = X_lin @ coef
    ssr = float(np.sum((yhat - y_age.mean()) ** 2))
    sse = float(np.sum((y_age - yhat) ** 2))
    r2_2d = ssr / (ssr + sse) if (ssr + sse) > 0 else 0.0
    p_2d = float(stats.f.sf((ssr / 2.0) / max(sse / max(len(d) - 3, 1), 1e-12), 2, max(len(d) - 3, 1))) if len(d) >= 5 else 1.0

    scale = max(float(np.ptp(xk)), float(np.ptp(yk)), 100.0)
    pts_norm = pts_xy / scale

    lons = np.linspace(float(d.lon.min()), float(d.lon.max()), grid_n)
    lats = np.linspace(float(d.lat.min()), float(d.lat.max()), grid_n)
    LON, LAT = np.meshgrid(lons, lats)
    gx, gy, _, _ = latlon_to_xy_km(LAT.ravel(), LON.ravel(), lat0=lat0, lon0=lon0)
    g_xy = np.column_stack([gx, gy])

    rbf = RBFInterpolator(pts_norm, y_age, kernel="thin_plate_spline", smoothing=0.08 * len(d))
    pred = rbf(g_xy / scale).reshape(grid_n, grid_n)

    try:
        hull = Delaunay(pts_xy)
        inside = (hull.find_simplex(g_xy) >= 0).reshape(grid_n, grid_n)
    except Exception:
        inside = np.ones((grid_n, grid_n), dtype=bool)

    dy_km = float((lats[1] - lats[0]) * 111.32) if grid_n > 1 else 1.0
    dx_km = float((lons[1] - lons[0]) * 111.32 * np.cos(np.radians(lat0))) if grid_n > 1 else 1.0
    d_age_dy, d_age_dx = np.gradient(pred, dy_km, dx_km)
    grad_mag = np.hypot(d_age_dx, d_age_dy)

    with np.errstate(divide="ignore", invalid="ignore"):
        speed = np.where(grad_mag > 0, 1000.0 / grad_mag, np.nan)
        u_dir = np.where(grad_mag > 0, -d_age_dx / grad_mag, np.nan)
        v_dir = np.where(grad_mag > 0, -d_age_dy / grad_mag, np.nan)

    valid = inside & np.isfinite(speed) & (speed >= 5.0) & (speed <= 5000.0)
    grid_df = pd.DataFrame({
        "genus": genus,
        "lat": LAT.ravel(),
        "lon": LON.ravel(),
        "pred_age_ka": np.where(inside, pred / 1000.0, np.nan).ravel(),
        "speed_m_per_yr": np.where(valid, speed, np.nan).ravel(),
        "u_dir": np.where(valid, u_dir, np.nan).ravel(),
        "v_dir": np.where(valid, v_dir, np.nan).ravel(),
    })
    if p_2d > 0.05 or valid.sum() < 5:
        return dict(r2_2d=r2_2d, p_2d=p_2d, rate_2d_median_m_per_yr=np.nan, rate_2d_iqr_low=np.nan,
                    rate_2d_iqr_high=np.nan, mean_azimuth_deg=np.nan, azimuth_conc=np.nan), None

    sp_v = speed[valid]
    mu, mv = float(np.mean(u_dir[valid])), float(np.mean(v_dir[valid]))
    az = float((np.degrees(np.arctan2(mu, mv)) + 360.0) % 360.0)
    return dict(
        r2_2d=r2_2d,
        p_2d=p_2d,
        rate_2d_median_m_per_yr=float(np.median(sp_v)),
        rate_2d_iqr_low=float(np.percentile(sp_v, 25)),
        rate_2d_iqr_high=float(np.percentile(sp_v, 75)),
        mean_azimuth_deg=az,
        azimuth_conc=float(np.hypot(mu, mv)),
    ), grid_df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--binned", default="binned.csv")
    ap.add_argument("--tag", default="base")
    ap.add_argument("--bin-width", type=int, default=C.BIN_WIDTH)
    ap.add_argument("--climate-rate", default=None)
    ap.add_argument("--mode2d", action="store_true")
    a = ap.parse_args()
    ensure_dirs()
    bw = int(a.bin_width)
    b = pd.read_csv(C.PROC / a.binned)
    lat0 = b.lat.min()
    rng = np.random.default_rng(0)
    use_2d = a.mode2d or ("lon" in b.columns)

    rows, arr_rows, grid_rows = [], [], []
    for g in C.GENERA:
        recs = [(sid, s.lat.iloc[0], s.lon.iloc[0] if "lon" in s.columns else np.nan, arrival_age(s, g))
                for sid, s in b.groupby("site_id")]
        d = pd.DataFrame(recs, columns=["site_id", "lat", "lon", "arrival_age"]).dropna(subset=["arrival_age"])
        d["dist_km"] = (d.lat - lat0) * 111.2
        d["genus"] = g
        arr_rows.append(d)
        if len(d) < C.MIN_SITES_MIGRATION:
            continue
        rec = dict(genus=g, n_sites=len(d), **fit_migration_1d(d, lat0, rng))
        if use_2d and d.lon.notna().all():
            m2, gdf = fit_migration_2d(d, g)
            rec.update(m2)
            if gdf is not None:
                grid_rows.append(gdf)
        rows.append(rec)

    R = pd.DataFrame(rows)
    R.to_csv(C.OUT / f"migration_{a.tag}.csv", index=False)
    pd.concat(arr_rows, ignore_index=True).to_csv(C.OUT / f"arrivals_{a.tag}.csv", index=False)
    if grid_rows:
        pd.concat(grid_rows, ignore_index=True).to_csv(C.OUT / f"migration_2d_grid_{a.tag}.csv", index=False)
    print(R.to_string(index=False))

    grad_j = json.loads((C.PROC / "gradient.json").read_text(encoding="utf-8"))
    grad = abs(grad_j["deg_c_per_km"])
    cr_path = C.OUT / (a.climate_rate or f"climate_rate_{a.tag}.csv")
    cr_df = pd.read_csv(cr_path)
    cr = cr_df.climate_rate_c_per_century.abs()
    vel = lambda rate_c_per_century: rate_c_per_century / 100.0 / grad * 1000.0
    comp = dict(
        spatial_gradient_c_per_km=grad,
        spatial_gradient_2d_c_per_km=grad_j.get("deg_c_per_km_2d_mag"),
        past_median_climate_velocity_m_per_yr=float(vel(cr.median())),
        past_p95_climate_velocity_m_per_yr=float(vel(np.percentile(cr.dropna(), 95))),
        past_max_climate_velocity_m_per_yr=float(vel(cr.max())),
        modern_warming_c_per_century=C.MODERN_WARMING_C_PER_CENTURY,
        modern_climate_velocity_m_per_yr=float(vel(C.MODERN_WARMING_C_PER_CENTURY)),
        median_genus_migration_m_per_yr=float(R.rate_m_per_yr.median()) if ("rate_m_per_yr" in R and R.rate_m_per_yr.notna().any()) else None,
        median_genus_migration_2d_m_per_yr=float(R.rate_2d_median_m_per_yr.median()) if ("rate_2d_median_m_per_yr" in R and R.rate_2d_median_m_per_yr.notna().any()) else None,
    )
    if grad_j.get("precip_mm_day_per_km_2d_mag") and "precip_rate_mm_day_per_century" in cr_df.columns:
        pgrad = float(grad_j["precip_mm_day_per_km_2d_mag"])
        p_vel = cr_df.precip_rate_mm_day_per_century.abs().dropna() / 100.0 / max(pgrad, 1e-9) * 1000.0
        comp["spatial_gradient_precip_2d_mm_day_per_km"] = pgrad
        comp["past_p95_precip_velocity_m_per_yr"] = float(np.percentile(p_vel, 95)) if len(p_vel) else None
    comp["note"] = (
        f"Past rates averaged over {bw}-yr bins UNDERSTATE brief abrupt events; comparison with modern "
        f"{C.MODERN_WARMING_C_PER_CENTURY} C/century is conservative. 2D speeds reflect 1/|grad age| across convex hull."
    )
    (C.OUT / f"velocity_comparison_{a.tag}.json").write_text(json.dumps(comp, indent=2), encoding="utf-8")
    print(json.dumps(comp, indent=2))
