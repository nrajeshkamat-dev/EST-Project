"""SYNTHETIC test data with KNOWN answers, to check that the pipeline works. NOT real results.
Run:  DATA_DIR=data_demo python synthetic_demo.py
Then run steps 03, 03b..05 with the same DATA_DIR. Planted truth is printed at the end.
"""
import os
os.environ.setdefault("DATA_DIR", "data_demo")
import json
import numpy as np
import pandas as pd
from scipy.special import expit
import config as C
from lib import ensure_dirs, site_bins, COLS

rng = np.random.default_rng(42)
ensure_dirs()
centres = site_bins()

def regional_T(a):
    return 8 - 10 * expit((a - 11500) / 900) - 2.0 * np.exp(-((a - 12000) / 400) ** 2)

OPT = dict(Picea=-1, Abies=2, Larix=0, Betula=3, Pinus=5, Tsuga=6, Alnus=4, Populus=4,
           Acer=7, Quercus=8, Fagus=8, Fraxinus=8, Ulmus=8, Carya=9)
LAG = dict(Picea=0, Abies=500, Larix=0, Betula=500, Pinus=500, Tsuga=1500, Alnus=0, Populus=0,
           Acer=1000, Quercus=1000, Fagus=2500, Fraxinus=1000, Ulmus=1000, Carya=1500)
MIG_M_PER_YR = 200.0     # planted for Quercus and Fagus
NS = 60
lats = rng.uniform(34, 50, NS); lons = rng.uniform(-95, -65, NS)

def props(lat, a):
    Tsite = lambda age: regional_T(age) - 0.5 * (lat - 40)
    w = {}
    for g in C.GENERA:
        w[g] = np.exp(-((Tsite(a + LAG[g]) - OPT[g]) / 4.0) ** 2) + 0.01
    for g in ("Quercus", "Fagus"):
        arrival = 13000 - (lat - 34) * 111.2 / (MIG_M_PER_YR / 1000)
        w[g] *= expit((arrival - a) / 150)
    w["Other"] = 0.1
    v = np.array([w[c] for c in COLS]); return v / v.sum()

rows = []
for i in range(NS):
    for a in centres:
        if rng.random() < 0.1: continue
        cnt = rng.multinomial(300, props(lats[i], a))
        rows.append([i, lats[i], lons[i], a] + list(cnt / cnt.sum()) + [300])
b = pd.DataFrame(rows, columns=["site_id", "lat", "lon", "bin_age"] + COLS + ["n_grains"])
b.to_csv(C.PROC / "binned.csv", index=False)
b.groupby("site_id")[["lat", "lon"]].first().reset_index().to_csv(C.PROC / "sites.csv", index=False)

mod = []
for j in range(150):
    i = rng.integers(NS); cnt = rng.multinomial(300, props(lats[i], 250))
    mod.append([1000 + j, lats[i], lons[i]] + list(cnt / cnt.sum()))
pd.DataFrame(mod, columns=["site_id", "lat", "lon"] + COLS).to_csv(C.PROC / "modern.csv", index=False)

pd.DataFrame({"bin_age": centres, "temp_c": regional_T(centres)}).to_csv(C.PROC / "climate_regional.csv", index=False)
cs = [dict(site_id=i, bin_age=a, temp_c=regional_T(a) - 0.5 * (lats[i] - 40)) for i in range(NS) for a in centres]
pd.DataFrame(cs).to_csv(C.PROC / "climate_sites.csv", index=False)
json.dump({"deg_c_per_km": -0.5 / 111.2}, open(C.PROC / "gradient.json", "w"))
print("synthetic data written to", C.DATA)
print("PLANTED lags (yr):", LAG)
print("PLANTED migration for Quercus, Fagus:", MIG_M_PER_YR, "m/yr")
