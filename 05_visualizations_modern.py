"""Modern publication-grade 300-dpi visualisations (Okabe-Ito, Natural Earth GeoJSON).

Modes:
  --mode mid_project -> reads data/outputs/mid_project/*, writes data/outputs/mid_project/figures_modern/
  --mode final       -> reads final_2d & stage outputs, writes data/outputs/figures_final/
  --mode standalone  -> reads final_2d outputs only (no baseline comparison), writes data/outputs/figures_standalone/
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import config as C

# Okabe-Ito colorblind-safe palette
OI = {
    "blue": "#0072B2",
    "vermilion": "#D55E00",
    "orange": "#E69F00",
    "green": "#009E73",
    "sky": "#56B4E9",
    "purple": "#CC79A7",
    "ink": "#111827",
    "slate": "#4B5565",
    "muted": "#6B7280",
    "grid": "#E5E7EB",
}

EVENTS = [
    ("Bølling–Allerød", 14.7, 12.9, "#FEF3C7"),
    ("Younger Dryas", 12.9, 11.7, "#DBEAFE"),
    ("8.2 ka", 8.4, 8.0, "#E0E7FF"),
]


def setup_style():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
        "font.size": 9.5,
        "axes.titlesize": 11,
        "axes.titleweight": "semibold",
        "axes.labelsize": 9.5,
        "axes.edgecolor": "#CBD5E1",
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": OI["grid"],
        "grid.linewidth": 0.6,
        "grid.alpha": 0.7,
        "xtick.color": OI["slate"],
        "ytick.color": OI["slate"],
        "text.color": OI["ink"],
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
    })


def _extract_segments(gj):
    segs = []
    for feat in gj.get("features", []):
        geom = feat.get("geometry") or {}
        gtype = geom.get("type")
        coords = geom.get("coordinates") or []
        if gtype == "LineString":
            segs.append(np.asarray(coords, float)[:, :2])
        elif gtype == "MultiLineString":
            for line in coords:
                segs.append(np.asarray(line, float)[:, :2])
        elif gtype == "Polygon":
            for ring in coords:
                segs.append(np.asarray(ring, float)[:, :2])
        elif gtype == "MultiPolygon":
            for poly in coords:
                for ring in poly:
                    segs.append(np.asarray(ring, float)[:, :2])
    return segs


def draw_ena_basemap(ax, bbox=C.BBOX):
    w, s, e, n = bbox
    ax.set_facecolor("#F1F5F9")
    for fname, color, lw, alpha, zorder in [
        ("ne_50m_admin_1_states_provinces_lines.geojson", "#CBD5E1", 0.5, 0.9, 1),
        ("ne_50m_lakes.geojson", "#38BDF8", 0.7, 0.65, 2),
        ("ne_50m_coastline.geojson", "#475569", 0.85, 0.95, 3),
    ]:
        p = C.GEO / fname
        if p.exists():
            segs = _extract_segments(json.loads(p.read_text(encoding="utf-8")))
            # Filter segments that overlap expanded bbox for speed
            keep = [sg for sg in segs if len(sg) >= 2 and np.any((sg[:, 0] >= w - 5) & (sg[:, 0] <= e + 5) & (sg[:, 1] >= s - 5) & (sg[:, 1] <= n + 5))]
            if keep:
                ax.add_collection(LineCollection(keep, colors=color, linewidths=lw, alpha=alpha, zorder=zorder))
    ax.set_xlim(w, e)
    ax.set_ylim(s, n)
    ax.set_aspect(1.0 / np.cos(np.radians(0.5 * (s + n))))
    ax.grid(True, linestyle=":", alpha=0.5)


def shade_events(ax, label_top=True):
    ymax = ax.get_ylim()[1]
    for name, a1, a0, col in EVENTS:
        ax.axvspan(a1, a0, color=col, alpha=0.55, zorder=0)
        if label_top:
            ax.text(0.5 * (a1 + a0), ymax, f" {name}", fontsize=7.5, color=OI["slate"],
                    ha="center", va="top", rotation=0)


# ---------------- MID-PROJECT BASELINE FIGURES ---------------- #
def render_mid_project():
    mid = C.OUT / "mid_project"
    fig_dir = mid / "figures_modern"
    fig_dir.mkdir(parents=True, exist_ok=True)
    sites = pd.read_csv(C.PROC / "sites.csv")
    binned = pd.read_csv(C.PROC / "binned.csv")
    creg = pd.read_csv(C.PROC / "climate_regional.csv").sort_values("bin_age")
    # Convert Kelvin in-memory solely for legible Mid-Project display
    temp_disp = creg.temp_c - 273.15 if creg.temp_c.mean() > 150 else creg.temp_c
    roc = pd.read_csv(mid / "rate_of_change_base.csv")
    crate = pd.read_csv(mid / "climate_rate_base.csv").sort_values("bin_age")
    lags = pd.read_csv(mid / "lag_summary_base.csv").sort_values("median_lag_yr", ascending=False)
    na = pd.read_csv(mid / "noanalogue_vs_climate_base.csv").sort_values("bin_age")
    mig = pd.read_csv(mid / "migration_base.csv").dropna(subset=["rate_m_per_yr"]).sort_values("rate_m_per_yr")
    vel = json.loads((mid / "velocity_comparison_base.json").read_text())

    # Fig 1: Site map + coverage
    counts = binned.groupby("site_id").bin_age.nunique().reindex(sites.site_id).fillna(0)
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    draw_ena_basemap(ax)
    sc = ax.scatter(sites.lon, sites.lat, c=counts, cmap="viridis", s=38, edgecolors="white", lw=0.6, zorder=5)
    cb = fig.colorbar(sc, ax=ax, shrink=0.82, pad=0.02)
    cb.set_label("Occupied 500-yr bins (of 30)")
    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")
    ax.set_title(f"Mid-Project Baseline: {len(sites)} Fossil Pollen Sites (TRSH+UPHE)")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig1_sites.png", dpi=300)
    plt.close(fig)

    # Fig 2: Climate temp (display °C), climate rate, turnover
    v = roc.groupby("bin_age").rate_per_century.agg(["median", lambda x: x.quantile(0.25), lambda x: x.quantile(0.75)])
    v.columns = ["med", "q1", "q3"]
    fig, axes = plt.subplots(3, 1, figsize=(8.2, 6.4), sharex=True)
    axes[0].plot(creg.bin_age / 1000, temp_disp, color=OI["vermilion"], lw=2.0)
    axes[0].set_ylabel("TraCE Temp (°C)\n[disp. K-273.15]")
    axes[1].plot(crate.bin_age / 1000, crate.climate_rate_c_per_century, color=OI["orange"], lw=1.8)
    axes[1].axhline(0, color=OI["muted"], lw=0.7)
    axes[1].set_ylabel("Climate Rate\n(°C / century)")
    axes[2].plot(v.index / 1000, v.med, color=OI["blue"], lw=2.0)
    axes[2].fill_between(v.index / 1000, v.q1, v.q3, color=OI["blue"], alpha=0.2)
    axes[2].set_ylabel("Turnover\n(Hellinger / c.)")
    axes[2].set_xlabel("Age (ka BP)")
    axes[2].set_xlim(15.0, 0.0)
    for idx_ax, ax in enumerate(axes):
        shade_events(ax, label_top=(idx_ax == 0))
    axes[0].set_title("Mid-Project Baseline: Deglacial Temperature, Rate & Vegetation Turnover")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig2_rates.png", dpi=300)
    plt.close(fig)

    # Fig 3: Genus lags
    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    y = np.arange(len(lags))
    ax.hlines(y, lags.ci_low, lags.ci_high, color=OI["sky"], lw=3.0)
    ax.scatter(lags.median_lag_yr, y, color=OI["blue"], s=55, zorder=4)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{r.genus} (n={int(r.n_sites)})" for _, r in lags.iterrows()])
    ax.set_xlabel("Median lag behind raw temperature (years, 95% bootstrap CI)")
    ax.set_title("Mid-Project Baseline: Genus-Level Raw Cross-Correlation Lags")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig3_lags.png", dpi=300)
    plt.close(fig)

    # Fig 4: No-analogue (showing 33.1% 500 BP weed floor)
    fig, ax = plt.subplots(figsize=(8.0, 4.2))
    ax2 = ax.twinx()
    ax2.spines["top"].set_visible(False)
    ax.bar(na.bin_age / 1000, na.frac_no_analogue * 100, width=0.38, color=OI["sky"], alpha=0.85, label="No-analogue (%)")
    ax2.plot(na.bin_age / 1000, na.abs_climate_rate, color=OI["vermilion"], lw=2.0, label="|Climate rate|")
    ax.annotate("500 BP weed floor: 33.1%\n(UPHE bias)", xy=(0.5, 33.1), xytext=(2.8, 52),
                arrowprops=dict(arrowstyle="->", color=OI["vermilion"]), fontsize=8.5, color=OI["vermilion"], fontweight="semibold")
    ax.set_xlim(15.0, 0.0)
    ax.set_ylim(0, 95)
    ax.set_xlabel("Age (ka BP)")
    ax.set_ylabel("No-analogue fossil samples (%)")
    ax2.set_ylabel("|Climate rate| (°C / century)", color=OI["vermilion"])
    ax.set_title("Mid-Project Baseline: No-Analogue Communities (TRSH+UPHE, SCD threshold=0.066)")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig4_noanalogue.png", dpi=300)
    plt.close(fig)

    # Fig 5: Migration vs velocity (log scale)
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    y = np.arange(len(mig))
    ax.hlines(y, mig.ci_low.clip(lower=10), mig.ci_high.clip(lower=10), color="#A7F3D0", lw=3.2)
    ax.scatter(mig.rate_m_per_yr, y, color=OI["green"], s=60, zorder=4, label="1D migration (m/yr)")
    ax.axvline(vel["past_p95_climate_velocity_m_per_yr"], color=OI["blue"], ls="--", lw=1.6,
               label=f"Past p95 velocity ({vel['past_p95_climate_velocity_m_per_yr']:.0f} m/yr)")
    ax.axvline(vel["modern_climate_velocity_m_per_yr"], color=OI["vermilion"], ls="-.", lw=1.8,
               label=f"Modern velocity ({vel['modern_climate_velocity_m_per_yr']:.0f} m/yr)")
    ax.set_xscale("log")
    ax.set_yticks(y)
    ax.set_yticklabels([f"{r.genus} (n={int(r.n_sites)})" for _, r in mig.iterrows()])
    ax.set_xlabel("Speed (m / yr, log scale)")
    ax.set_title("Mid-Project Baseline: 1D Northward Migration vs Climate Velocity")
    ax.legend(frameon=False, loc="lower right", fontsize=8.5)
    fig.tight_layout()
    fig.savefig(fig_dir / "fig5_migration.png", dpi=300)
    plt.close(fig)
    print(f"[viz] mid_project modern PNGs written to {fig_dir}")


# ---------------- FINAL PUBLICATION FIGURES ---------------- #
def render_final(standalone: bool = False):
    fig_dir = C.OUT / ("figures_standalone" if standalone else "figures_final")
    fig_dir.mkdir(parents=True, exist_ok=True)
    mid = C.OUT / "mid_project"

    sites_base = pd.read_csv(C.PROC / "sites.csv")
    sites_fin = pd.read_csv(C.PROC / "sites_final_2d.csv")
    binned_fin = pd.read_csv(C.PROC / "binned_final_2d.csv")
    creg = pd.read_csv(C.PROC / "climate_regional.csv").sort_values("bin_age")

    # LegacyAge audit if present
    la_audit_p = C.STAGE_LOGS / "legacyage_match_audit.csv"
    la_matched = set()
    if la_audit_p.exists():
        la = pd.read_csv(la_audit_p)
        la_matched = set(la.loc[la.matched == True, "dataset_id"].astype(int))

    # Fig 1: Single-panel spatial network overview across Eastern North America
    fig, ax_map = plt.subplots(figsize=(8.4, 5.0))
    draw_ena_basemap(ax_map)
    dropped_sites = sites_base[~sites_base.site_id.isin(sites_fin.site_id)]
    if la_matched:
        m_mask = sites_fin.site_id.isin(la_matched)
        ax_map.scatter(sites_fin.loc[m_mask, "lon"], sites_fin.loc[m_mask, "lat"],
                       c=OI["blue"], s=44, edgecolors="white", lw=0.65, zorder=5,
                       label=f"Retained, LegacyAge 1.0 (n={int(m_mask.sum())})")
        ax_map.scatter(sites_fin.loc[~m_mask, "lon"], sites_fin.loc[~m_mask, "lat"],
                       c=OI["orange"], s=44, edgecolors="white", lw=0.65, zorder=5,
                       label=f"Retained, Neotoma fallback (n={int((~m_mask).sum())})")
    else:
        ax_map.scatter(sites_fin.lon, sites_fin.lat, c=OI["blue"], s=44, edgecolors="white", lw=0.65, zorder=5,
                       label=f"Retained TRSH-only (n={len(sites_fin)})")
    if len(dropped_sites):
        drop_lbl = f"Excluded (<100 woody grains, n={len(dropped_sites)})" if standalone else f"Dropped (<100 TRSH grains, n={len(dropped_sites)})"
        ax_map.scatter(dropped_sites.lon, dropped_sites.lat, marker="x", c=OI["vermilion"], s=60, lw=1.7, zorder=6,
                       label=drop_lbl)
    ax_map.set_xlabel("Longitude (°E)")
    ax_map.set_ylabel("Latitude (°N)")
    ax_map.set_title(f"Study Sites Across Eastern North America ({len(sites_fin)} retained, {len(binned_fin):,} bins)")
    ax_map.legend(frameon=True, facecolor="white", framealpha=0.94, fontsize=8.5, loc="lower right")
    fig.tight_layout()
    fig.savefig(fig_dir / ("fig1_study_sites.png" if standalone else "fig1_spatial_overview.png"), dpi=300)
    plt.close(fig)

    # Fig 2: Climate + precip + turnover annotated events
    roc_fin = pd.read_csv(C.OUT / "rate_of_change_final_2d.csv")
    cr_fin = pd.read_csv(C.OUT / "climate_rate_final_2d.csv").sort_values("bin_age")
    vf = roc_fin.groupby("bin_age").rate_per_century.agg(["median", lambda x: x.quantile(0.25), lambda x: x.quantile(0.75)])
    vf.columns = ["med", "q1", "q3"]

    fig, axes = plt.subplots(3, 1, figsize=(9.4, 6.8), sharex=True)
    axes[0].plot(creg.bin_age / 1000, creg.temp_c, color=OI["vermilion"], lw=2.0, label="Temperature (°C)")
    axes[0].set_ylabel("TraCE Temp (°C)", color=OI["vermilion"])
    if "precip_mm_day" in creg.columns:
        ax0r = axes[0].twinx()
        ax0r.spines["top"].set_visible(False)
        ax0r.plot(creg.bin_age / 1000, creg.precip_mm_day, color=OI["sky"], lw=1.8, ls="--", label="Precip (mm/day)")
        ax0r.set_ylabel("Precip (mm/day)", color=OI["blue"])
    axes[1].plot(cr_fin.bin_age / 1000, cr_fin.climate_rate_c_per_century, color=OI["orange"], lw=1.9)
    axes[1].axhline(0, color=OI["muted"], lw=0.7)
    axes[1].set_ylabel("Temp Rate\n(°C / century)")
    if not standalone:
        vm = pd.read_csv(mid / "rate_of_change_base.csv").groupby("bin_age").rate_per_century.median()
        axes[2].plot(vm.index / 1000, vm.values, color=OI["muted"], lw=1.2, ls=":", label="Mid-Project median")
    axes[2].plot(vf.index / 1000, vf.med, color=OI["blue"], lw=2.0, label="Median turnover (IQR)" if standalone else "Final median (IQR)")
    axes[2].fill_between(vf.index / 1000, vf.q1, vf.q3, color=OI["blue"], alpha=0.22)
    axes[2].set_ylabel("Veg. Turnover\n(Hellinger / c.)")
    axes[2].set_xlabel("Age (ka BP)")
    axes[2].set_xlim(15.0, 0.0)
    axes[2].legend(frameon=False, fontsize=8.2, loc="upper right")
    for idx_ax, ax in enumerate(axes):
        shade_events(ax, label_top=(idx_ax == 0))
    axes[0].set_title("Late-Quaternary Climate Dynamics & Community Turnover (TraCE-21ka + Neotoma)")
    fig.tight_layout()
    fig.savefig(fig_dir / ("fig2_climate_and_turnover.png" if standalone else "fig2_climate_turnover_events.png"), dpi=300)
    plt.close(fig)

    # Fig 3a / Fig 3: Option A Two-Panel Timeline Lollipop + 100% Stacked Polarity Bar
    lags_site = pd.read_csv(C.OUT / "lags_final_2d.csv")
    ls_fin = pd.read_csv(C.OUT / "lag_summary_final_2d.csv")

    breakdowns = []
    for _, r in ls_fin.iterrows():
        g = r["genus"]
        sub = lags_site[lags_site["genus"] == g]
        n_tot = len(sub)
        n_pos_sig = len(sub[(sub["r"] >= 0) & (sub["p_ebisuzaki"] < 0.05)])
        n_pos_nonsig = len(sub[(sub["r"] >= 0) & (sub["p_ebisuzaki"] >= 0.05)])
        n_neg_sig = len(sub[(sub["r"] < 0) & (sub["p_ebisuzaki"] < 0.05)])
        n_neg_nonsig = len(sub[(sub["r"] < 0) & (sub["p_ebisuzaki"] >= 0.05)])
        breakdowns.append({
            "genus": g,
            "pct_pos_sig": n_pos_sig / n_tot * 100,
            "pct_pos_nonsig": n_pos_nonsig / n_tot * 100,
            "pct_neg_sig": n_neg_sig / n_tot * 100,
            "pct_neg_nonsig": n_neg_nonsig / n_tot * 100,
            "pct_pos_tot": (n_pos_sig + n_pos_nonsig) / n_tot * 100,
            "pct_neg_tot": (n_neg_sig + n_neg_nonsig) / n_tot * 100,
        })
    df_merged = pd.merge(ls_fin, pd.DataFrame(breakdowns), on="genus")
    df_sorted = df_merged.sort_values(by=["median_lag_yr", "mean_r"], ascending=[False, True]).reset_index(drop=True)

    fig, (ax_left, ax_right) = plt.subplots(
        1, 2, figsize=(12.2, 6.4), sharey=True, gridspec_kw={"width_ratios": [1.1, 1.25]}
    )
    y = np.arange(len(df_sorted))

    # Left Panel: Timeline Lollipop
    ax_left.axvspan(-100, 1000, color="#FEF3C7", alpha=0.35, zorder=0)
    ax_left.axvspan(1000, 2000, color="#F1F5F9", alpha=0.5, zorder=0)
    ax_left.axvspan(2000, 3100, color="#E0E7FF", alpha=0.35, zorder=0)

    ax_left.text(450, len(y) - 0.25, "Fast Pioneers\n(<1,000 yr)", ha="center", va="bottom", fontsize=7.6, color="#92400E", fontweight="bold")
    ax_left.text(1500, len(y) - 0.25, "Canopy Reorganization\n(1,000–2,000 yr)", ha="center", va="bottom", fontsize=7.6, color="#475569", fontweight="bold")
    ax_left.text(2550, len(y) - 0.25, "Late Climax\n(>2,000 yr)", ha="center", va="bottom", fontsize=7.6, color="#3730A3", fontweight="bold")

    for i, r in df_sorted.iterrows():
        ax_left.hlines(i, r.ci_low, r.ci_high, color="#94A3B8", lw=2.4, zorder=2)
        pt_color = OI["vermilion"] if r.frac_pos_r >= 0.5 else OI["blue"]
        ax_left.scatter(r.median_lag_yr, i, color=pt_color, s=80, edgecolors="white", lw=1.3, zorder=4)
        txt = f"{r.median_lag_yr:.0f} yr"
        if r.ci_high > r.ci_low:
            txt += f" [{r.ci_low:.0f}–{r.ci_high:.0f}]"
        if r.genus == "Larix":
            ax_left.text(r.median_lag_yr + 85, i, txt, va="center", ha="left", fontsize=7.6, color="#0F172A", fontweight="semibold",
                         bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="#CBD5E1", lw=0.5, alpha=0.9))
        else:
            ax_left.text(max(r.ci_high, r.median_lag_yr) + 50, i, txt, va="center", ha="left", fontsize=7.6, color="#0F172A", fontweight="medium")

    ax_left.set_yticks(y)
    ax_left.set_yticklabels([f"{r.genus} (n={r.n_sites})" for _, r in df_sorted.iterrows()], fontsize=9.5, fontweight="semibold")
    ax_left.set_xlim(-100, 3500)
    ax_left.set_ylim(-0.6, len(y) + 0.6)
    ax_left.set_xlabel("Median Response Lag Behind Climate (years ± 95% CI)", fontsize=9.2)
    ax_left.set_title("A. Response Delay (How Long Did Trees Take?)", fontsize=10.5, fontweight="bold", pad=8)

    # Right Panel: 100% Stacked Polarity Bar
    for i, r in df_sorted.iterrows():
        left = 0
        ax_right.barh(i, r.pct_neg_sig, left=left, color=OI["blue"], height=0.62, edgecolor="white", lw=0.6, zorder=3)
        left += r.pct_neg_sig
        ax_right.barh(i, r.pct_neg_nonsig, left=left, color=OI["sky"], height=0.62, edgecolor="white", lw=0.6, zorder=3)
        left += r.pct_neg_nonsig
        ax_right.barh(i, r.pct_pos_nonsig, left=left, color=OI["orange"], height=0.62, edgecolor="white", lw=0.6, zorder=3)
        left += r.pct_pos_nonsig
        ax_right.barh(i, r.pct_pos_sig, left=left, color=OI["vermilion"], height=0.62, edgecolor="white", lw=0.6, zorder=3)

        dom_txt = f"{r.pct_pos_tot:.0f}% Warm" if r.pct_pos_tot >= 50 else f"{r.pct_neg_tot:.0f}% Cold"
        sig_txt = f"({r.pct_sig_05*100:.0f}% sig)"
        badge_bg = "#FFEDD5" if r.pct_pos_tot >= 50 else "#DBEAFE"
        badge_fg = "#9A3412" if r.pct_pos_tot >= 50 else "#1E40AF"
        ax_right.text(102, i, f"{dom_txt} {sig_txt}", va="center", ha="left", fontsize=7.8,
                      fontweight="semibold", color=badge_fg,
                      bbox=dict(boxstyle="round,pad=0.18", facecolor=badge_bg, edgecolor="none"))

    ax_right.axvline(50, color=OI["slate"], ls="--", lw=1.0, zorder=2)
    ax_right.set_xlim(0, 142)
    ax_right.set_xticks([0, 25, 50, 75, 100])
    ax_right.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax_right.set_xlabel("Fossil Sites Breakdown (% Sites Cold- vs. Warm-Tracking)", fontsize=9.2)
    ax_right.set_title("B. Reaction to Warming (Did Trees Expand or Retreat?)", fontsize=10.5, fontweight="bold", pad=8)

    legend_handles = [
        Line2D([0], [0], marker="o", color="white", markerfacecolor=OI["blue"], markersize=8, label="Cold-Tracking Net Dominant"),
        Line2D([0], [0], marker="o", color="white", markerfacecolor=OI["vermilion"], markersize=8, label="Warm-Tracking Net Dominant"),
        Patch(facecolor=OI["blue"], edgecolor="none", label="−r Cold-Retreat (p < 0.05)"),
        Patch(facecolor=OI["sky"], edgecolor="none", label="−r Cold-Retreat (p ≥ 0.05)"),
        Patch(facecolor=OI["orange"], edgecolor="none", label="+r Warm-Expand (p ≥ 0.05)"),
        Patch(facecolor=OI["vermilion"], edgecolor="none", label="+r Warm-Expand (p < 0.05)"),
    ]
    fig.legend(handles=legend_handles, loc="lower center", bbox_to_anchor=(0.5, -0.04),
               ncol=6, frameon=True, facecolor="white", edgecolor="#CBD5E1", fontsize=8.0)

    fig.suptitle("Forest Lag Timeline & Warming Response Polarity (Neotoma + TraCE-21ka)",
                 fontsize=12, fontweight="bold", y=0.98)
    fig.tight_layout(rect=[0, 0.06, 1, 0.95])
    fig.savefig(fig_dir / ("fig3_genus_lags_raincloud.png" if standalone else "fig3a_lags_raincloud.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)

    # Fig 3b: Mid vs Final Dumbbell Comparison (comparison mode only)
    if not standalone:
        ls_mid = pd.read_csv(mid / "lag_summary_base.csv").set_index("genus")
        ls_f = ls_fin.set_index("genus")
        both = sorted(set(ls_mid.index) | set(ls_f.index), key=lambda g: ls_f.loc[g, "median_lag_yr"] if g in ls_f.index else 9999)
        fig, ax = plt.subplots(figsize=(8.6, 5.2))
        for i, g in enumerate(both):
            m_val = ls_mid.loc[g, "median_lag_yr"] if g in ls_mid.index else np.nan
            f_val = ls_f.loc[g, "median_lag_yr"] if g in ls_f.index else np.nan
            if not np.isnan(m_val) and not np.isnan(f_val):
                ax.plot([m_val, f_val], [i, i], color="#94A3B8", lw=2.0, zorder=1)
            if not np.isnan(m_val):
                ax.scatter(m_val, i, color=OI["muted"], s=65, zorder=3)
            else:
                # Missing in Mid-Project
                ax.text(f_val - 70, i, "Mid: <5 sites", color=OI["muted"], fontsize=7.8, style="italic", ha="right", va="center")
            if not np.isnan(f_val):
                ax.scatter(f_val, i, color=OI["blue"], s=75, zorder=4)
            else:
                # Missing in Final
                ax.text(m_val + 70, i, "Final: <5 sites (TRSH-only)", color=OI["vermilion"], fontsize=7.8, style="italic", ha="left", va="center")
        ax.set_yticks(range(len(both)))
        ax.set_yticklabels([
            f"{g} ({100*ls_f.loc[g,'pct_sig_05']:.0f}% sig)" if g in ls_f.index and "pct_sig_05" in ls_f.columns else g
            for g in both
        ])
        ax.set_xlabel("Median lag (years)")
        ax.set_title("Mid-Project Raw Lags vs. Final Detrended / RPP / LegacyAge Lags")
        handles = [
            plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=OI["blue"], markersize=8, label="Final (diff + RPP + LegacyAge)"),
            plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=OI["muted"], markersize=7, label="Mid-Project (raw, TRSH+UPHE)"),
        ]
        ax.legend(handles=handles, frameon=True, facecolor="white", framealpha=0.92, edgecolor="#CBD5E1", loc="lower right", fontsize=8.5)
        fig.tight_layout()
        fig.savefig(fig_dir / "fig3b_mid_vs_final_lags.png", dpi=300)
        plt.close(fig)

    # Fig 4: No-analogue trajectory + SCD taxonomic driver heatmap
    na_fin = pd.read_csv(C.OUT / "noanalogue_vs_climate_final_2d.csv").sort_values("bin_age")
    drv = pd.read_csv(C.OUT / ("no_analogue_drivers_final_2d.csv" if standalone else "no_analogue_drivers_trsh_only.csv"))
    fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(9.4, 6.4), sharex=True, gridspec_kw={"height_ratios": [1.0, 1.15]})
    if standalone:
        l1 = ax_top.plot(na_fin.bin_age / 1000, na_fin.frac_no_analogue * 100, color=OI["blue"], lw=2.2,
                         label="No-analogue samples (%)")
        ax_top.fill_between(na_fin.bin_age / 1000, 0, na_fin.frac_no_analogue * 100, color=OI["sky"], alpha=0.16)
        ax_r = ax_top.twinx()
        ax_r.spines["top"].set_visible(False)
        l2 = ax_r.plot(na_fin.bin_age / 1000, na_fin.abs_climate_rate, color=OI["vermilion"], lw=1.8, ls="--",
                       label="|Climate rate| (°C/century)")
        ax_r.set_ylabel("|Climate rate| (°C / c.)", color=OI["vermilion"])
        ax_top.set_ylabel("No-analogue samples (%)", color=OI["blue"])
        ax_top.set_ylim(0, 95)
        pk_row = na_fin.loc[na_fin.frac_no_analogue.idxmax()]
        ax_top.annotate(f"Peak: {pk_row.frac_no_analogue*100:.1f}% ({pk_row.bin_age/1000:.1f} ka)",
                        xy=(pk_row.bin_age / 1000, pk_row.frac_no_analogue * 100),
                        xytext=(10.3, 82), fontsize=8.0, fontweight="semibold", color="#0F172A",
                        bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="#CBD5E1", lw=0.5),
                        arrowprops=dict(arrowstyle="->", color="#475569", lw=0.9))
        row_500 = na_fin.loc[na_fin.bin_age == 500].iloc[0]
        ax_top.annotate(f"500 BP: {row_500.frac_no_analogue*100:.1f}%",
                        xy=(0.5, row_500.frac_no_analogue * 100), xytext=(2.6, 22),
                        fontsize=8.0, fontweight="semibold", color="#0F172A",
                        arrowprops=dict(arrowstyle="->", color="#475569", lw=0.9))
        lines = l1 + l2
        ax_top.legend(lines, [l.get_label() for l in lines], frameon=False, fontsize=8.2, loc="upper right")
        ax_top.set_title("No-Analogue Forests Track Rapid Climate Change & Specific Co-Occurring Taxa")
    else:
        na_raw = pd.read_csv(C.OUT / "noanalogue_vs_climate_raw_celsius.csv").sort_values("bin_age")
        na_tr = pd.read_csv(C.OUT / "noanalogue_vs_climate_trsh_only.csv").sort_values("bin_age")
        ax_top.plot(na_raw.bin_age / 1000, na_raw.frac_no_analogue * 100, color=OI["vermilion"], lw=1.8, ls="--",
                    label="Mid-Project / Raw Celsius (TRSH+UPHE, 500 BP = 33.1%)")
        ax_top.plot(na_tr.bin_age / 1000, na_tr.frac_no_analogue * 100, color=OI["blue"], lw=2.2,
                    label="TRSH-only (weeds removed, 500 BP = 15.6%)")
        ax_top.plot(na_fin.bin_age / 1000, na_fin.frac_no_analogue * 100, color=OI["green"], lw=1.9,
                    label="Final (TRSH + RPP + LegacyAge)")
        ax_top.set_ylabel("No-analogue samples (%)")
        ax_top.set_ylim(0, 95)
        ax_top.legend(frameon=False, fontsize=8.2, loc="upper right")
        ax_top.set_title("No-Analogue Reduction After Removing UPHE Weed Bias & SCD Driver Attribution")

    tax_cols = [c for c in C.GENERA + ["Other"] if c in drv.columns]
    # Show top 8 contributors by mean SCD
    drv_bins = drv.sort_values("bin_age", ascending=False)
    top8 = drv_bins[tax_cols].mean().sort_values(ascending=False).head(8).index.tolist()
    mat = drv_bins[top8].values.T
    im = ax_bot.imshow(mat, aspect="auto", cmap="YlOrRd", extent=[15.0, 0.0, len(top8) - 0.5, -0.5])
    ax_bot.set_yticks(range(len(top8)))
    ax_bot.set_yticklabels(top8)
    ax_bot.set_xlabel("Age (ka BP)")
    ax_bot.set_ylabel("Top SCD Contributors")
    ax_bot.set_xlim(15.0, 0.0)
    ax_bot.grid(False)
    cb = fig.colorbar(im, ax=ax_bot, orientation="horizontal", fraction=0.06, pad=0.22)
    cb.set_label("Mean Squared Chord Distance (SCD) Contribution to Nearest Modern Analogue")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig4_noanalogue_drivers.png", dpi=300)
    plt.close(fig)

    # Fig 5a: 2D migration isochrones + azimuth arrows
    grid_p = C.OUT / "migration_2d_grid_final_2d.csv"
    arr_p = C.OUT / "arrivals_final_2d.csv"
    mig_fin = pd.read_csv(C.OUT / "migration_final_2d.csv")
    if grid_p.exists() and arr_p.exists():
        grid_df = pd.read_csv(grid_p)
        arr_df = pd.read_csv(arr_p)
        g_list = mig_fin.dropna(subset=["rate_2d_median_m_per_yr"]).sort_values("n_sites", ascending=False).head(6).genus.tolist()
        ncols = 3
        nrows = max(1, int(np.ceil(len(g_list) / ncols)))
        fig, axes = plt.subplots(nrows, ncols, figsize=(11.5, 4.0 * nrows), sharex=True, sharey=True)
        axes = np.atleast_1d(axes).ravel()
        for idx_g, g in enumerate(g_list):
            ax = axes[idx_g]
            draw_ena_basemap(ax)
            sub_g = grid_df[grid_df.genus == g]
            sub_a = arr_df[arr_df.genus == g]
            if len(sub_g):
                pv = sub_g.pivot(index="lat", columns="lon", values="pred_age_ka")
                X, Y = np.meshgrid(pv.columns.values, pv.index.values)
                cf = ax.contourf(X, Y, pv.values, levels=np.linspace(2, 14, 7), cmap="viridis_r", alpha=0.55, extend="both", zorder=2)
                ax.contour(X, Y, pv.values, levels=np.linspace(2, 14, 7), colors=OI["ink"], linewidths=0.5, alpha=0.6, zorder=3)
                # Downsample quiver arrows
                qsub = sub_g.dropna(subset=["u_dir", "v_dir"]).iloc[::4]
                if len(qsub):
                    ax.quiver(qsub.lon, qsub.lat, qsub.u_dir, qsub.v_dir, color=OI["ink"], scale=18, width=0.005, alpha=0.8, zorder=4)
            ax.scatter(sub_a.lon, sub_a.lat, c=sub_a.arrival_age / 1000, cmap="viridis_r", vmin=2, vmax=14,
                       s=24, edgecolors="white", lw=0.5, zorder=5)
            row = mig_fin[mig_fin.genus == g].iloc[0]
            ax.set_title(f"{g}: {row.rate_2d_median_m_per_yr:.0f} m/yr (az {row.mean_azimuth_deg:.0f}°)", fontsize=9.8)
        for j in range(len(g_list), len(axes)):
            axes[j].axis("off")
        sm = plt.cm.ScalarMappable(cmap="viridis_r", norm=matplotlib.colors.Normalize(vmin=2, vmax=14))
        sm.set_array([])
        cax = fig.add_axes([0.32, 0.035, 0.36, 0.018])
        cbar = fig.colorbar(sm, cax=cax, orientation="horizontal")
        cbar.set_label("Arrival Age Isochrone (ka BP)")
        fig.suptitle("2D Postglacial Arrival Isochrones (ka BP) & Migration Vectors Around Appalachians / Great Lakes", fontsize=11.5, fontweight="semibold")
        fig.tight_layout(rect=[0, 0.07, 1, 0.96])
        fig.savefig(fig_dir / ("fig5_migration_isochrones.png" if standalone else "fig5a_migration_isochrones.png"), dpi=300)
        plt.close(fig)

    # Fig 5b / Fig 6: Velocity Deficit Log-Lollipop with Full Ranges
    mig_f2 = mig_fin.dropna(subset=["rate_2d_median_m_per_yr"]).set_index("genus")
    vel_fin = json.loads((C.OUT / "velocity_comparison_final_2d.json").read_text())
    mig_mid = None if standalone else pd.read_csv(mid / "migration_base.csv").dropna(subset=["rate_m_per_yr"]).set_index("genus")
    grid_df = pd.read_csv(C.OUT / "migration_2d_grid_final_2d.csv") if (C.OUT / "migration_2d_grid_final_2d.csv").exists() else None

    # Compute full spatial surface ranges for 2D migrants
    grid_ranges = {}
    if grid_df is not None:
        for g in mig_f2.index:
            sub = grid_df[grid_df.genus == g]["speed_m_per_yr"].dropna()
            if len(sub):
                grid_ranges[g] = {
                    "min": float(sub.min()),
                    "q25": float(sub.quantile(0.25)),
                    "med": float(sub.median()),
                    "q75": float(sub.quantile(0.75)),
                    "max": float(sub.max()),
                }

    genera_v = sorted(
        set(mig_f2.index) if standalone else (set(mig_mid.index) | set(mig_f2.index)),
        key=lambda g: mig_f2.loc[g, "rate_2d_median_m_per_yr"] if g in mig_f2.index else mig_mid.loc[g, "rate_m_per_yr"],
    )
    fig, ax = plt.subplots(figsize=(9.8, 4.8 if standalone else 5.2))
    ax.set_facecolor("white")

    # Past deglacial climate velocity band (median to max, with p95 line)
    past_med = vel_fin["past_median_climate_velocity_m_per_yr"]
    past_p95 = vel_fin["past_p95_climate_velocity_m_per_yr"]
    past_max = vel_fin.get("past_max_climate_velocity_m_per_yr", 343.2)
    ax.axvspan(past_med, past_max, color="#E0F2FE", alpha=0.55, zorder=0)
    ax.axvline(past_p95, color=OI["blue"], ls="--", lw=1.8, zorder=1)

    # Modern climate velocity band (1.5 to 2.5 °C/century, central 1.9 °C/century)
    grad = vel_fin["spatial_gradient_c_per_km"]
    mod_low = 1.5 / grad * 10.0
    mod_cen = vel_fin["modern_climate_velocity_m_per_yr"]
    mod_hi = 2.5 / grad * 10.0
    ax.axvspan(mod_low, mod_hi, color="#FFEDD5", alpha=0.65, zorder=0)
    ax.axvline(mod_cen, color=OI["vermilion"], ls="-.", lw=2.0, zorder=1)

    for i, g in enumerate(genera_v):
        if not standalone:
            y_m = i - 0.16
            if g in mig_mid.index:
                r1 = mig_mid.loc[g]
                if pd.notna(r1.get("ci_low")) and pd.notna(r1.get("ci_high")):
                    ax.hlines(y_m, max(10, r1.ci_low), min(3500, r1.ci_high), color="#CBD5E1", lw=2.0, zorder=2)
                ax.scatter(r1.rate_m_per_yr, y_m, color=OI["muted"], s=58, zorder=3)
            else:
                # Genera significant in Final 2D but non-significant or missing in Mid 1D
                if g == "Alnus":
                    ax.text(24, y_m, "Mid 1D: p=0.119 (non-sig)", color=OI["slate"], fontsize=7.4, style="italic", va="center")
                else:
                    ax.text(24, y_m, "Mid 1D: <5 sites", color=OI["slate"], fontsize=7.4, style="italic", va="center")

        y_pos = i if standalone else i + 0.16
        if g in mig_f2.index:
            r2 = mig_f2.loc[g]
            st = grid_ranges.get(g, {
                "min": float(r2.rate_2d_iqr_low),
                "q25": float(r2.rate_2d_iqr_low),
                "med": float(r2.rate_2d_median_m_per_yr),
                "q75": float(r2.rate_2d_iqr_high),
                "max": float(r2.rate_2d_iqr_high),
            })
            # Full spatial range bar with end-cap whiskers
            ax.hlines(y_pos, st["min"], st["max"], color="#047857", lw=1.6, zorder=2)
            ax.vlines([st["min"], st["max"]], y_pos - 0.14, y_pos + 0.14, color="#047857", lw=1.6, zorder=2)
            # Median marker
            ax.scatter(st["med"], y_pos, color=OI["green"], s=85 if standalone else 70, edgecolors="white", lw=1.4, zorder=4)
            if standalone:
                txt = f"{st['med']:.0f} m/yr (range {st['min']:.0f}–{st['max']:.0f})"
                ax.text(st["min"] * 0.93, y_pos, txt, ha="right", va="center", fontsize=7.8, fontweight="medium", color="#0F172A",
                        bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="#E2E8F0", lw=0.6, alpha=0.92))
            else:
                txt = f"{st['med']:.0f} m/yr ({st['min']:.0f}–{st['max']:.0f})"
                ax.text(st["max"] * 1.07, y_pos, txt, ha="left", va="center", fontsize=7.4, fontweight="medium", color="#065F46",
                        bbox=dict(boxstyle="round,pad=0.14", facecolor="#F0FDF4", edgecolor="#86EFAC", lw=0.5, alpha=0.92))
        else:
            # Genera significant in Mid 1D but non-significant or dropped in Final 2D
            if g == "Quercus":
                ax.text(285 * 1.08, y_pos, "Final 2D: p=0.095 (non-sig)", color="#047857", fontsize=7.5, style="italic", va="center",
                        bbox=dict(boxstyle="round,pad=0.16", facecolor="#F0FDF4", edgecolor="#86EFAC", lw=0.6))
            elif g == "Abies":
                ax.text(59.4 * 1.12, y_pos, "Final: <5 sites (TRSH-only)", color=OI["vermilion"], fontsize=7.5, style="italic", va="center",
                        bbox=dict(boxstyle="round,pad=0.16", facecolor="#FEF2F2", edgecolor="#FECACA", lw=0.6))

    if standalone:
        ax.text(23, 4.35, "Non-significant 2D surfaces (p > 0.05):\nPinus, Quercus, Betula, Ulmus,\nFraxinus, Populus, Acer",
                fontsize=7.2, color=OI["slate"], style="italic", va="top",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="#F8FAFC", edgecolor="#CBD5E1", lw=0.6, alpha=0.9))

    if standalone:
        custom_handles = [
            Line2D([0], [0], marker="o", color="white", markerfacecolor=OI["green"], markeredgecolor="white", markersize=8, lw=0, label="2D spatial speed (median)"),
            Line2D([0], [0], color="#047857", lw=1.5, marker="|", markersize=7, label="2D spatial surface range (min–max)"),
            Patch(facecolor="#E0F2FE", edgecolor="none", alpha=0.6, label=f"Past deglacial velocity range: {past_med:.0f}–{past_max:.0f} m/yr (median to max)"),
            Line2D([0], [0], color=OI["blue"], ls="--", lw=1.6, label=f"Past p95 thermal velocity: {past_p95:.0f} m/yr"),
            Patch(facecolor="#FFEDD5", edgecolor="none", alpha=0.7, label=f"Modern velocity range: {mod_low:.0f}–{mod_hi:.0f} m/yr (1.5–2.5 °C/c.)"),
            Line2D([0], [0], color=OI["vermilion"], ls="-.", lw=1.8, label=f"Modern velocity: {mod_cen:.0f} m/yr (1.9 °C/c.)"),
        ]
    else:
        custom_handles = [
            Line2D([0], [0], marker="o", color="white", markerfacecolor=OI["green"], markeredgecolor="white", markersize=8, lw=0, label="Final 2D spatial speed (median)"),
            Line2D([0], [0], color="#047857", lw=1.5, marker="|", markersize=7, label="Final 2D spatial range (min–max)"),
            Line2D([0], [0], marker="o", color="white", markerfacecolor=OI["muted"], markeredgecolor="white", markersize=7, lw=0, label="Mid-Project 1D OLS (± 95% CI)"),
            Patch(facecolor="#E0F2FE", edgecolor="none", alpha=0.6, label=f"Past deglacial velocity range: {past_med:.0f}–{past_max:.0f} m/yr (median to max)"),
            Line2D([0], [0], color=OI["blue"], ls="--", lw=1.6, label=f"Past p95 thermal velocity: {past_p95:.0f} m/yr"),
            Patch(facecolor="#FFEDD5", edgecolor="none", alpha=0.7, label=f"Modern velocity range: {mod_low:.0f}–{mod_hi:.0f} m/yr (1.5–2.5 °C/c.)"),
            Line2D([0], [0], color=OI["vermilion"], ls="-.", lw=1.8, label=f"Modern velocity: {mod_cen:.0f} m/yr (1.9 °C/c.)"),
        ]

    ax.legend(handles=custom_handles, loc="lower right", frameon=True, facecolor="white", framealpha=0.95, edgecolor="#CBD5E1", fontsize=7.4)
    ax.set_xscale("log")
    ax.set_xlim(18 if standalone else 16, 2700)
    ax.set_ylim(-0.6, len(genera_v) - 0.3)
    ax.set_yticks(range(len(genera_v)))
    ax.set_yticklabels(genera_v, fontsize=10, fontweight="semibold")
    ax.set_xlabel("Speed (m / year, log scale)", fontsize=9.5)
    ax.set_title("Postglacial 2D Tree Migration Speeds & Spatial Ranges vs. Climate Velocity" if standalone
                 else "Migration Velocity Deficit: Mid-Project 1D & Final 2D vs. Required Climate Tracking Speed",
                 fontsize=11, fontweight="semibold", pad=10)
    ax.grid(True, which="both", linestyle=":", color=OI["grid"], alpha=0.7)
    fig.tight_layout()
    fig.savefig(fig_dir / ("fig6_velocity_deficit.png" if standalone else "fig5b_velocity_deficit.png"), dpi=300)
    plt.close(fig)
    print(f"[viz] {'standalone 6' if standalone else 'final 7'} PNGs written to {fig_dir}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["mid_project", "final", "standalone"], required=True)
    a = ap.parse_args()
    setup_style()
    if a.mode == "mid_project":
        render_mid_project()
    elif a.mode == "standalone":
        render_final(standalone=True)
    else:
        render_final(standalone=False)
