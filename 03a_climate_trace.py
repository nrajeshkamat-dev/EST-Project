"""Step 3a: extract TraCE-21ka temperature at each site and for the region.

Download TREFHT decadal-average NetCDF files from NCAR GDEX dataset d651050
(DOI 10.5065/CXB5-TV56, https://gdex.ucar.edu/datasets/d651050/) into data/raw/trace/.
Outputs: climate_sites.csv (site_id, bin_age, temp_c), climate_regional.csv, gradient.json

CHECK THE TIME AXIS: the script prints how it interpreted `time`. If wrong, pass --time-mode.
"""
import argparse, glob, json
import numpy as np
import pandas as pd
import xarray as xr
import config as C
from lib import ensure_dirs, site_bins


def to_age_bp(t, mode):
    t = np.asarray(t, float)
    if mode == "auto":
        if np.abs(t).max() < 30:
            mode = "ka_neg" if t.min() < 0 else "ka_pos"
        else:
            mode = "yr_neg" if t.min() < 0 else "yr_pos"
    print(f"time axis interpreted as: {mode}  (raw range {t.min():.2f} to {t.max():.2f})")
    return {"ka_neg": -t * 1000, "ka_pos": t * 1000, "yr_neg": -t, "yr_pos": t}[mode]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--time-mode", default="auto", choices=["auto", "ka_neg", "ka_pos", "yr_neg", "yr_pos"])
    a = ap.parse_args()
    ensure_dirs()
    files = sorted(glob.glob(str(C.RAW / "trace" / "*.nc")))
    if not files:
        raise SystemExit("No NetCDF files in data/raw/trace/. See the docstring for the download link.")
    ds = xr.open_mfdataset(files, decode_times=False, combine="nested", concat_dim="time")
    ds = ds.sortby("time")
    T = ds[C.TRACE_VAR]
    if "lev" in T.dims:
        T = T.isel(lev=-1)
    T = T.load()
    if float(T.mean()) > 200:
        T = T - 273.15
    age = to_age_bp(ds["time"].values, a.time_mode)
    T = T.assign_coords(age_bp=("time", age))
    lon = ((T["lon"] + 180) % 360) - 180
    T = T.assign_coords(lon=lon).sortby("lon")
    T = T.where((T.age_bp >= C.AGE_MIN - 100) & (T.age_bp <= C.AGE_MAX + 100), drop=True)

    edges = np.arange(C.AGE_MIN, C.AGE_MAX + 1, C.BIN_WIDTH)
    centres = site_bins()
    idx = np.digitize(T.age_bp.values, edges) - 1
    ok = (idx >= 0) & (idx < len(centres))
    binned = np.full((len(centres),) + T.shape[1:], np.nan)
    arr = T.values
    for k in range(len(centres)):
        sel = idx == k
        if sel.any():
            binned[k] = arr[sel].mean(axis=0)
    B = xr.DataArray(binned, dims=("bin", "lat", "lon"),
                     coords={"bin": centres, "lat": T.lat.values, "lon": T.lon.values})

    sites = pd.read_csv(C.PROC / "sites.csv")
    rows = []
    for _, s in sites.iterrows():
        ts = B.sel(lat=s.lat, lon=s.lon, method="nearest").values
        rows += [dict(site_id=s.site_id, bin_age=c, temp_c=v) for c, v in zip(centres, ts)]
    pd.DataFrame(rows).to_csv(C.PROC / "climate_sites.csv", index=False)

    box = B.sel(lat=slice(C.BBOX[1], C.BBOX[3]), lon=slice(C.BBOX[0], C.BBOX[2]))
    reg = box.mean(dim=("lat", "lon"))
    pd.DataFrame({"bin_age": centres, "temp_c": reg.values}).to_csv(C.PROC / "climate_regional.csv", index=False)

    recent = box.isel(bin=slice(0, 2)).mean(dim=("bin", "lon"))      # most recent ~1000 yr
    slope_per_deg = np.polyfit(recent.lat.values, recent.values, 1)[0]   # deg C per deg latitude
    json.dump({"deg_c_per_km": float(slope_per_deg / 111.2)}, open(C.PROC / "gradient.json", "w"))
    print(f"wrote climate files. N-S gradient: {slope_per_deg:.3f} C per degree latitude")
