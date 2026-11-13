"""Step 3a: extract annual TraCE-21ka temperature (°C) and precipitation (mm/day).

Reads annual decadal-average NetCDF-3 files via scipy.io.netcdf_file (with xarray fallback),
explicitly filtering annual files (*decavg_400BCE.nc) to avoid mixing seasonal DJF/JJA/MAM/SON files.
"""
import argparse
import glob
import json
from pathlib import Path
import numpy as np
import pandas as pd
import requests
from scipy.io import netcdf_file
import config as C
from lib import ensure_dirs, latlon_to_xy_km, site_bins


def to_age_bp(t, mode="auto"):
    t = np.asarray(t, float)
    if mode == "auto":
        if np.abs(t).max() < 30:
            mode = "ka_neg" if t.min() < 0 else "ka_pos"
        else:
            mode = "yr_neg" if t.min() < 0 else "yr_pos"
    print(f"time axis interpreted as: {mode} (raw range {t.min():.2f} to {t.max():.2f})")
    return {"ka_neg": -t * 1000.0, "ka_pos": t * 1000.0, "yr_neg": -t, "yr_pos": t}[mode]


def download_prect(dest_dir: Path):
    dest = dest_dir / "trace.01-36.22000BP.cam2.PRECT.22000BP_decavg_400BCE.nc"
    if dest.exists() and dest.stat().st_size > 10_000_000:
        return dest, None
    dest_dir.mkdir(parents=True, exist_ok=True)
    last_err = None
    for url in C.TRACE_PRECT_URLS:
        try:
            print(f"downloading PRECT from {url} ...")
            with requests.get(url, stream=True, timeout=180) as r:
                r.raise_for_status()
                tmp = dest.with_suffix(".nc.part")
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
                tmp.replace(dest)
            print(f"downloaded {dest.name} ({dest.stat().st_size / 1e6:.1f} MB)")
            return dest, None
        except Exception as e:
            last_err = str(e)
    return None, f"PRECT download unavailable ({last_err}); continuing with TREFHT only."


def load_trace_var(pattern, varname, time_mode="auto"):
    files = sorted(glob.glob(str(C.RAW / "trace" / pattern)))
    if not files:
        return None
    times, arrs, lat, lon, units = [], [], None, None, ""
    for f in files:
        with netcdf_file(f, "r", mmap=False) as nc:
            v = nc.variables[varname]
            data = np.array(v.data, dtype=float)
            if data.ndim == 4:
                data = data[:, -1, :, :]
            u = v._attributes.get("units", b"")
            units = u.decode("utf-8", "ignore") if isinstance(u, bytes) else str(u)
            t = np.array(nc.variables["time"].data, dtype=float)
            lat = np.array(nc.variables["lat"].data, dtype=float)
            lon = np.array(nc.variables["lon"].data, dtype=float)
            arrs.append(data)
            times.append(t)
    arr = np.concatenate(arrs, axis=0)
    age = to_age_bp(np.concatenate(times), time_mode)
    ord_t = np.argsort(age)
    age, arr = age[ord_t], arr[ord_t]
    lon = ((lon + 180.0) % 360.0) - 180.0
    ord_lon = np.argsort(lon)
    lon, arr = lon[ord_lon], arr[:, :, ord_lon]
    sel = (age >= C.AGE_MIN - 100) & (age <= C.AGE_MAX + 100)
    return arr[sel], age[sel], lat, lon, units


def bin_field(arr, age, bin_width):
    edges = np.arange(C.AGE_MIN, C.AGE_MAX + 1, bin_width)
    centres = site_bins(bin_width)
    idx = np.digitize(age, edges) - 1
    out = np.full((len(centres),) + arr.shape[1:], np.nan, dtype=float)
    for k in range(len(centres)):
        sel = idx == k
        if sel.any():
            out[k] = arr[sel].mean(axis=0)
    return centres, out


def spatial_gradients(field_2d, lat, lon, bbox):
    w, s, e, n = bbox
    lm = (lat >= s) & (lat <= n)
    lnm = (lon >= w) & (lon <= e)
    sub_lat, sub_lon = lat[lm], lon[lnm]
    sub = field_2d[np.ix_(lm, lnm)]
    slope_lat = float(np.polyfit(sub_lat, sub.mean(axis=1), 1)[0])
    # 2D planar OLS over equal-area km coordinates
    LON, LAT = np.meshgrid(sub_lon, sub_lat)
    xk, yk, _, _ = latlon_to_xy_km(LAT.ravel(), LON.ravel())
    A = np.column_stack([np.ones_like(xk), xk, yk])
    coef, *_ = np.linalg.lstsq(A, sub.ravel(), rcond=None)
    gx, gy = float(coef[1]), float(coef[2])
    return {
        "ns_per_deg": slope_lat,
        "ns_per_km": slope_lat / 111.32,
        "grad_x_per_km": gx,
        "grad_y_per_km": gy,
        "grad_mag_per_km": float(np.hypot(gx, gy)),
    }


def extract_climate(bin_width=None, time_mode="auto", do_download_prect=False, suffix=""):
    ensure_dirs()
    bw = int(bin_width or C.BIN_WIDTH)
    warn = None
    if do_download_prect:
        _, warn = download_prect(C.RAW / "trace")

    res_t = load_trace_var(C.TRACE_TREFHT_GLOB, C.TRACE_VAR, time_mode)
    if res_t is None:
        raise SystemExit(f"No {C.TRACE_TREFHT_GLOB} NetCDF files in {C.RAW / 'trace'}.")
    T, age_t, lat, lon, t_units = res_t
    if t_units.strip().upper().startswith("K") or float(np.nanmean(T)) > 150.0:
        T = T - 273.15
    assert -40.0 < float(np.nanmean(T)) < 40.0, f"TREFHT mean out of Celsius bounds: {np.nanmean(T)}"

    centres, B_T = bin_field(T, age_t, bw)
    lm = (lat >= C.BBOX[1]) & (lat <= C.BBOX[3])
    lnm = (lon >= C.BBOX[0]) & (lon <= C.BBOX[2])
    reg_t = B_T[:, lm, :][:, :, lnm].mean(axis=(1, 2))
    assert -40.0 < float(np.nanmean(reg_t)) < 40.0, f"Regional temp_c invalid: {reg_t}"

    # Precipitation (optional if missing)
    res_p = load_trace_var(C.TRACE_PRECT_GLOB, C.TRACE_PRECT_VAR, time_mode)
    B_P, reg_p = None, None
    if res_p is not None:
        P, age_p, p_lat, p_lon, p_units = res_p
        if "m/s" in p_units.lower() or float(np.nanmean(P)) < 1e-3:
            P = P * 86400.0 * 1000.0
        assert 0.0 < float(np.nanmean(P)) < 30.0, f"PRECT mean out of mm/day bounds: {np.nanmean(P)}"
        _, B_P = bin_field(P, age_p, bw)
        plm = (p_lat >= C.BBOX[1]) & (p_lat <= C.BBOX[3])
        plnm = (p_lon >= C.BBOX[0]) & (p_lon <= C.BBOX[2])
        reg_p = B_P[:, plm, :][:, :, plnm].mean(axis=(1, 2))

    site_files = sorted(C.PROC.glob("sites*.csv")) or [C.PROC / "sites.csv"]
    sites = pd.concat([pd.read_csv(sf)[["site_id", "lat", "lon"]] for sf in site_files], ignore_index=True).drop_duplicates("site_id")
    rows = []
    for _, s in sites.iterrows():
        li = int(np.argmin(np.abs(lat - s.lat)))
        lj = int(np.argmin(np.abs(lon - s.lon)))
        ts = B_T[:, li, lj]
        ps = B_P[:, li, lj] if B_P is not None else [np.nan] * len(centres)
        for c, tv, pv in zip(centres, ts, ps):
            rec = {"site_id": s.site_id, "bin_age": c, "temp_c": float(tv)}
            if B_P is not None:
                rec["precip_mm_day"] = float(pv)
            rows.append(rec)
    cs_df = pd.DataFrame(rows)
    assert -40.0 < float(cs_df.temp_c.mean()) < 40.0, "Site temp_c out of Celsius range"
    cs_df.to_csv(C.PROC / f"climate_sites{suffix}.csv", index=False)

    creg = {"bin_age": centres, "temp_c": reg_t}
    if reg_p is not None:
        creg["precip_mm_day"] = reg_p
    pd.DataFrame(creg).to_csv(C.PROC / f"climate_regional{suffix}.csv", index=False)

    # Spatial gradients over most recent ~1000 yr
    n_rec = max(1, int(round(1000.0 / bw)))
    t_recent = np.nanmean(B_T[:n_rec], axis=0)
    tg = spatial_gradients(t_recent, lat, lon, C.BBOX)
    grad_payload = {
        "deg_c_per_km": tg["ns_per_km"],
        "deg_c_per_km_2d_mag": tg["grad_mag_per_km"],
        "temp_grad_2d": tg,
        "has_precip": B_P is not None,
    }
    if B_P is not None:
        p_recent = np.nanmean(B_P[:n_rec], axis=0)
        pg = spatial_gradients(p_recent, p_lat, p_lon, C.BBOX)
        grad_payload["precip_mm_day_per_km_ns"] = pg["ns_per_km"]
        grad_payload["precip_mm_day_per_km_2d_mag"] = pg["grad_mag_per_km"]
        grad_payload["precip_grad_2d"] = pg

    if not suffix:
        (C.PROC / "gradient.json").write_text(json.dumps(grad_payload, indent=2), encoding="utf-8")
    print(f"wrote climate_regional{suffix}.csv ({reg_t.min():.2f}..{reg_t.max():.2f} C), "
          f"N-S grad={tg['ns_per_deg']:.3f} C/deg, has_precip={B_P is not None}")
    return grad_payload, warn


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--time-mode", default="auto", choices=["auto", "ka_neg", "ka_pos", "yr_neg", "yr_pos"])
    ap.add_argument("--bin-width", type=int, default=C.BIN_WIDTH)
    ap.add_argument("--download-prect", action="store_true")
    ap.add_argument("--suffix", default="")
    a = ap.parse_args()
    extract_climate(a.bin_width, a.time_mode, a.download_prect, a.suffix)
