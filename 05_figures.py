"""Step 5: figures for the report and slides (PNG, 200 dpi) in data/outputs/figures."""
import argparse, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import config as C

ap = argparse.ArgumentParser(); ap.add_argument("--tag", default="base"); a = ap.parse_args()
F = C.OUT / "figures"; F.mkdir(parents=True, exist_ok=True)
O = lambda n: C.OUT / f"{n}_{a.tag}"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

# Fig 1: site map
s = pd.read_csv(C.PROC / "sites.csv")
fig, ax = plt.subplots(figsize=(6, 4))
ax.scatter(s.lon, s.lat, s=14, color="#2F5496"); ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
ax.set_title(f"Fossil pollen sites used (n = {len(s)})"); fig.tight_layout(); fig.savefig(F / "fig1_sites.png", dpi=200); plt.close()

# Fig 2: climate rate vs vegetation rate of change
roc = pd.read_csv(f"{O('rate_of_change')}.csv"); cr = pd.read_csv(f"{O('climate_rate')}.csv")
v = roc.groupby("bin_age").rate_per_century.agg(["median", lambda x: x.quantile(.25), lambda x: x.quantile(.75)])
v.columns = ["med", "q1", "q3"]
fig, ax = plt.subplots(2, 1, figsize=(7, 5), sharex=True)
ax[0].plot(cr.bin_age / 1000, cr.climate_rate_c_per_century, color="#C00000"); ax[0].axhline(0, color="grey", lw=.5)
ax[0].set_ylabel("Climate rate\n(°C / century)")
ax[1].plot(v.index / 1000, v.med, color="#2F5496"); ax[1].fill_between(v.index / 1000, v.q1, v.q3, alpha=.25, color="#2F5496")
ax[1].set_ylabel("Vegetation turnover\n(Hellinger / century)"); ax[1].set_xlabel("Age (ka BP)"); ax[1].invert_xaxis()
fig.tight_layout(); fig.savefig(F / "fig2_rates.png", dpi=200); plt.close()

# Fig 3: lag by genus
S = pd.read_csv(f"{O('lag_summary')}.csv")
fig, ax = plt.subplots(figsize=(6.5, 4))
ax.barh(S.genus, S.median_lag_yr, xerr=[S.median_lag_yr - S.ci_low, S.ci_high - S.median_lag_yr], color="#8FAADC", ecolor="#1F3864")
ax.set_xlabel("Median lag behind temperature (years, 95% bootstrap CI)"); ax.set_title("Genus-level lag (RQ1)")
fig.tight_layout(); fig.savefig(F / "fig3_lags.png", dpi=200); plt.close()

# Fig 4: no-analogue vs climate rate
m = pd.read_csv(f"{O('noanalogue_vs_climate')}.csv").sort_values("bin_age")
fig, ax = plt.subplots(figsize=(7, 3.6)); ax2 = ax.twinx()
ax.bar(m.bin_age / 1000, m.frac_no_analogue, width=.4, color="#A9A9A9"); ax.set_ylabel("Fraction no-analogue samples")
ax2.plot(m.bin_age / 1000, m.abs_climate_rate, color="#C00000"); ax2.set_ylabel("|Climate rate| (°C / century)", color="#C00000")
ax.set_xlabel("Age (ka BP)"); ax.invert_xaxis(); ax.set_title("No-analogue communities and climate rate (RQ2)")
fig.tight_layout(); fig.savefig(F / "fig4_noanalogue.png", dpi=200); plt.close()

# Fig 5: migration vs climate velocity
R = pd.read_csv(f"{O('migration')}.csv").dropna(subset=["rate_m_per_yr"]); V = json.load(open(f"{O('velocity_comparison')}.json"))
fig, ax = plt.subplots(figsize=(6.5, 4))
if len(R):
    ax.barh(R.genus, R.rate_m_per_yr, xerr=[(R.rate_m_per_yr - R.ci_low).clip(lower=0), (R.ci_high - R.rate_m_per_yr).clip(lower=0)], color="#A9D18E")
for k, c, l in [("past_p95_climate_velocity_m_per_yr", "#2F5496", "Past climate velocity (95th pct)"),
                ("modern_climate_velocity_m_per_yr", "#C00000", "Velocity at modern warming rate")]:
    ax.axvline(V[k], color=c, ls="--", label=l)
ax.set_xlabel("Migration rate (m / year)"); ax.legend(frameon=False, fontsize=8); ax.set_title("Migration vs required speed (RQ3)")
fig.tight_layout(); fig.savefig(F / "fig5_migration.png", dpi=200); plt.close()
print("figures written to", F)
