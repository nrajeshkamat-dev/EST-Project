"""Step 6: Self-contained offline HTML reports (Mid-Project & Final) + Final DOCX & PDF reports.

Usage:
  python 06_build_report.py --mode mid_project   -> TBD2_MidProject_Baseline_Report.html
  python 06_build_report.py --mode final         -> TBD2_Final_Report.html + TBD2_Final_Project_Report.docx/.pdf
  python 06_build_report.py --mode standalone    -> TBD2_Project_Report_Standalone.html/.docx/.pdf
  python 06_build_report.py --verify-only        -> verify HTML DOM/Plotly/assets & DOCX/PDF structure
"""
import argparse
import base64
import html
import json
from pathlib import Path
import numpy as np
import pandas as pd
import docx
import pymupdf
import config as C
from report_paper import build_final_report_docx_and_pdf
from report_standalone import build_standalone_report_docx_and_pdf

BASE_CSS = """
:root {
  --bg: #f5f7fa;
  --surface: #ffffff;
  --raised: #eceff4;
  --border: rgba(17, 24, 39, 0.09);
  --ink: #111827;
  --ink-2: #4b5565;
  --ink-muted: #6b7487;
  --accent: #0072b2;
  --ok: #009e73;
  --warn: #d55e00;
  --font: "Segoe UI", system-ui, -apple-system, sans-serif;
  --mono: ui-monospace, "Cascadia Code", Consolas, monospace;
}
* { box-sizing: border-box; }
::selection { background: rgba(0, 114, 178, 0.16); color: var(--ink); }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
body {
  margin: 0; font-family: var(--font); font-size: 15px; line-height: 1.6;
  color: var(--ink); background: var(--bg);
}
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: rgba(17, 24, 39, 0.2); border-radius: 4px; }
.wrap { max-width: 1280px; margin: 0 auto; padding: 24px 28px 64px; }
header.hero {
  background: var(--surface); border: 1px solid var(--border); border-radius: 14px;
  padding: 28px 32px; margin-bottom: 20px;
}
header.hero h1 { margin: 0 0 8px; font-size: 26px; font-weight: 600; letter-spacing: -0.02em; line-height: 1.2; }
.meta-row { display: flex; flex-wrap: wrap; gap: 16px; color: var(--ink-2); font-size: 13px; margin-bottom: 12px; }
.badge {
  display: inline-block; font-family: var(--mono); font-size: 12px; padding: 2px 8px;
  border-radius: 5px; background: var(--raised); color: var(--ink-2); border: 1px solid var(--border);
}
.badge.accent { color: var(--accent); border-color: rgba(0, 114, 178, 0.28); background: rgba(0, 114, 178, 0.06); }
.badge.warn { color: var(--warn); border-color: rgba(213, 94, 0, 0.28); background: rgba(213, 94, 0, 0.06); }
.badge.ok { color: var(--ok); border-color: rgba(0, 158, 115, 0.28); background: rgba(0, 158, 115, 0.06); }
.prose { max-width: 72ch; color: var(--ink-2); margin: 8px 0 0; }
.kpi-strip {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 12px; margin-bottom: 20px;
}
.kpi {
  background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 16px 18px;
}
.kpi .label { font-size: 12.5px; color: var(--ink-muted); margin-bottom: 4px; }
.kpi .val { font-size: 24px; font-weight: 500; font-variant-numeric: tabular-nums; letter-spacing: -0.01em; }
.kpi .sub { font-size: 12.5px; color: var(--ink-2); margin-top: 4px; font-variant-numeric: tabular-nums; }
nav.tabs {
  display: flex; flex-wrap: wrap; gap: 6px; padding: 6px; margin-bottom: 20px;
  background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
}
nav.tabs button[role="tab"] {
  border: 0; background: transparent; color: var(--ink-2); font-family: var(--font);
  font-size: 13.5px; font-weight: 500; padding: 8px 14px; border-radius: 8px; cursor: pointer;
  transition: background-color 140ms cubic-bezier(0.22, 1, 0.36, 1), color 140ms cubic-bezier(0.22, 1, 0.36, 1);
}
nav.tabs button[role="tab"]:hover { background: var(--raised); color: var(--ink); }
nav.tabs button[role="tab"][aria-selected="true"] { background: var(--accent); color: #ffffff; }
section.panel {
  background: var(--surface); border: 1px solid var(--border); border-radius: 14px;
  padding: 24px 28px; margin-bottom: 20px;
}
section.panel[hidden] { display: none; }
section.panel h2 { margin: 0 0 12px; font-size: 19px; font-weight: 600; letter-spacing: -0.01em; }
section.panel h3 { margin: 20px 0 8px; font-size: 15.5px; font-weight: 600; }
.chart-box { width: 100%; min-height: 380px; margin: 12px 0 20px; }
.grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(460px, 1fr)); gap: 20px; }
.fig-card { border: 1px solid var(--border); border-radius: 12px; padding: 14px; background: #ffffff; }
.fig-card img { width: 100%; height: auto; display: block; border-radius: 6px; }
.fig-card figcaption { margin-top: 8px; font-size: 12.5px; color: var(--ink-2); }
.table-wrap { overflow-x: auto; border: 1px solid var(--border); border-radius: 10px; margin: 12px 0; }
table { width: 100%; border-collapse: collapse; font-size: 13.5px; font-variant-numeric: tabular-nums; }
th, td { padding: 9px 12px; text-align: left; border-bottom: 1px solid var(--border); white-space: nowrap; }
th { background: var(--raised); font-weight: 600; color: var(--ink); }
tr:last-child td { border-bottom: 0; }
.num { font-family: var(--mono); font-size: 12.5px; text-align: right; }
.notice { padding: 12px 16px; border-radius: 10px; background: var(--raised); border: 1px solid var(--border); font-size: 13.5px; color: var(--ink-2); margin: 12px 0; }
@media (max-width: 720px) { .wrap { padding: 12px; } .grid-2 { grid-template-columns: 1fr; } }
@media print { nav.tabs { display: none; } section.panel[hidden] { display: block !important; } }
"""

TAB_JS = """
const tabs = Array.from(document.querySelectorAll('nav.tabs [role="tab"]'));
const panels = Array.from(document.querySelectorAll('section[role="tabpanel"]'));
function activateTab(id) {
  tabs.forEach(t => {
    const on = t.getAttribute('aria-controls') === id;
    t.setAttribute('aria-selected', String(on));
    t.tabIndex = on ? 0 : -1;
  });
  panels.forEach(p => {
    if (p.id === id) p.removeAttribute('hidden');
    else p.setAttribute('hidden', '');
  });
  window.dispatchEvent(new Event('resize'));
  if (window.Plotly) {
    document.querySelectorAll('#' + id + ' .js-plotly-plot').forEach(el => Plotly.Plots.resize(el));
  }
}
tabs.forEach((t, idx) => {
  t.addEventListener('click', () => activateTab(t.getAttribute('aria-controls')));
  t.addEventListener('keydown', e => {
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
      const next = tabs[(idx + (e.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length];
      next.focus();
      activateTab(next.getAttribute('aria-controls'));
    }
  });
});
"""


def _b64_img(path):
    return "data:image/png;base64," + base64.b64encode(Path(path).read_bytes()).decode("ascii")


def _plotly_inline():
    js_path = C.GEO / "plotly-2.35.2.min.js"
    return js_path.read_text(encoding="utf-8") if js_path.exists() else ""


def _html_table(df, cols=None, num_cols=()):
    cols = cols or list(df.columns)
    th = "".join(f"<th class='{'num' if c in num_cols else ''}'>{html.escape(str(c))}</th>" for c in cols)
    rows = []
    for _, r in df.iterrows():
        tds = []
        for c in cols:
            v = r[c]
            cls = "num" if c in num_cols else ""
            if isinstance(v, float) and np.isnan(v):
                s = "—"
            elif isinstance(v, (float, np.floating)):
                s = f"{v:.4g}" if abs(v) < 0.01 and v != 0 else f"{v:.2f}"
            else:
                s = str(v)
            tds.append(f"<td class='{cls}'>{html.escape(s)}</td>")
        rows.append("<tr>" + "".join(tds) + "</tr>")
    return f"<div class='table-wrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"


def _shell_html(title, subtitle, badges, kpis, tab_defs, plot_calls):
    plotly_js = _plotly_inline()
    badge_html = "".join(f"<span class='badge {cls}'>{html.escape(txt)}</span>" for txt, cls in badges)
    kpi_html = "".join(
        f"<div class='kpi'><div class='label'>{html.escape(lbl)}</div>"
        f"<div class='val'>{html.escape(val)}</div>"
        f"<div class='sub'>{html.escape(sub)}</div></div>"
        for lbl, val, sub in kpis
    )
    tab_btns = "".join(
        f"<button role='tab' id='btn-{tid}' aria-controls='{tid}' aria-selected='{'true' if i==0 else 'false'}' tabindex='{0 if i==0 else -1}'>{html.escape(label)}</button>"
        for i, (tid, label, _) in enumerate(tab_defs)
    )
    tab_panels = "".join(
        f"<section role='tabpanel' class='panel' id='{tid}' aria-labelledby='btn-{tid}' {'' if i==0 else 'hidden'}>{body}</section>"
        for i, (tid, _, body) in enumerate(tab_defs)
    )
    plot_script = "\n".join(plot_calls)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>{BASE_CSS}</style>
<script>{plotly_js}</script>
</head>
<body>
<div class="wrap">
  <header class="hero">
    <h1>{html.escape(title)}</h1>
    <div class="meta-row"><span>Team TBD2 · Project 25 · Eastern North America Late-Quaternary Synthesis</span>{badge_html}</div>
    <p class="prose">{html.escape(subtitle)}</p>
  </header>
  <div class="kpi-strip">{kpi_html}</div>
  <nav class="tabs" role="tablist" aria-label="Report Sections">{tab_btns}</nav>
  {tab_panels}
</div>
<script>
{TAB_JS}
document.addEventListener('DOMContentLoaded', () => {{
  const cfg = {{responsive: true, displaylogo: false}};
  const baseLayout = {{
    font: {{family: '"Segoe UI", system-ui, sans-serif', size: 12, color: '#111827'}},
    paper_bgcolor: '#ffffff', plot_bgcolor: '#ffffff',
    margin: {{t: 36, r: 24, b: 48, l: 58}},
    xaxis: {{gridcolor: '#e5e7eb', zerolinecolor: '#cbd5e1'}},
    yaxis: {{gridcolor: '#e5e7eb', zerolinecolor: '#cbd5e1'}},
  }};
  {plot_script}
}});
</script>
</body>
</html>"""


def render_mid_html():
    mid = C.OUT / "mid_project"
    fig_dir = mid / "figures_modern"
    sites = pd.read_csv(C.PROC / "sites.csv")
    binned = pd.read_csv(C.PROC / "binned.csv")
    modern = pd.read_csv(C.PROC / "modern.csv")
    creg = pd.read_csv(C.PROC / "climate_regional.csv").sort_values("bin_age")
    temp_disp = (creg.temp_c - 273.15) if creg.temp_c.mean() > 150 else creg.temp_c
    lags = pd.read_csv(mid / "lag_summary_base.csv").sort_values("median_lag_yr")
    na = pd.read_csv(mid / "noanalogue_vs_climate_base.csv").sort_values("bin_age")
    mig = pd.read_csv(mid / "migration_base.csv").dropna(subset=["rate_m_per_yr"]).sort_values("rate_m_per_yr")
    vel = json.loads((mid / "velocity_comparison_base.json").read_text())
    tests = json.loads((mid / "tests_base.json").read_text())
    na_500 = float(na.loc[na.bin_age == 500, "frac_no_analogue"].iloc[0]) * 100

    kpis = [
        ("Filtered Fossil Sites", f"{len(sites)}", f"{len(binned):,} binned rows · {len(modern)} modern samples"),
        ("Kruskal-Wallis Lag Test", f"p = {tests['kruskal_p']:.2e}", f"{len(lags)} genera · median {lags.median_lag_yr.median():.0f} yr (raw)"),
        ("No-Analogue 500 BP Floor", f"{na_500:.1f}%", f"Peak {na.frac_no_analogue.max()*100:.1f}% at 12.0 ka (TRSH+UPHE)"),
        ("1D Migration vs Modern Vel.", f"{vel['median_genus_migration_m_per_yr']:.1f} m/yr", f"Modern velocity {vel['modern_climate_velocity_m_per_yr']:.0f} m/yr ({vel['modern_climate_velocity_m_per_yr']/vel['median_genus_migration_m_per_yr']:.1f}×)"),
    ]
    figs = ["fig1_sites.png", "fig2_rates.png", "fig3_lags.png", "fig4_noanalogue.png", "fig5_migration.png"]
    fig_cards = "".join(
        f"<figure class='fig-card'><img src='{_b64_img(fig_dir / f)}' alt='{f}'><figcaption>{f}</figcaption></figure>"
        for f in figs if (fig_dir / f).exists()
    )
    tab_defs = [
        ("mid-overview", "Baseline Overview", f"""
          <h2>Pre-Upgrade Snapshot & Known Diagnostics</h2>
          <div class='notice'><strong>Audit Note:</strong> This snapshot freezes all pre-upgrade outputs in <code>data/outputs/mid_project/</code> prior to Phase 1 fixes. Known defects preserved for comparison: (1) <code>climate_regional.csv</code> &amp; <code>climate_sites.csv</code> store Kelvin (262.88–278.41 K; converted to °C in charts for display only), (2) <code>modern.csv</code> retains <code>UPHE</code> agricultural weeds inflating 500 BP no-analogue to 33.1%, (3) raw level correlations inflate lag significance, (4) arbitrary 0.5 pine weight &amp; 1D OLS migration.</div>
          <div id='plot-mid-clim' class='chart-box'></div>
          <div class='grid-2'>{fig_cards}</div>
        """),
        ("mid-lags", "RQ1: Raw Lags", f"""
          <h2>Genus-Level Raw Cross-Correlation Lags</h2>
          <div id='plot-mid-lags' class='chart-box'></div>
          {_html_table(lags, num_cols=("n_sites", "median_lag_yr", "ci_low", "ci_high"))}
        """),
        ("mid-na", "RQ2: No-Analogue", f"""
          <h2>No-Analogue Fraction vs. |Climate Rate| (TRSH+UPHE)</h2>
          <div id='plot-mid-na' class='chart-box'></div>
          {_html_table(na, num_cols=tuple(na.columns))}
        """),
        ("mid-mig", "RQ3: 1D Migration", f"""
          <h2>1D Northward Arrival Gradients vs. Climate Velocity</h2>
          <div id='plot-mid-mig' class='chart-box'></div>
          {_html_table(mig, num_cols=("n_sites", "rate_m_per_yr", "ci_low", "ci_high", "p"))}
        """),
    ]
    plots = [
        f"Plotly.newPlot('plot-mid-clim', [{{x:{(creg.bin_age/1000).tolist()}, y:{temp_disp.round(3).tolist()}, type:'scatter', mode:'lines+markers', name:'TraCE TREFHT (°C display)', line:{{color:'#D55E00',width:2.5}}}}], {{...baseLayout, title:'TraCE-21ka Regional Temperature (Display K-273.15)', xaxis:{{...baseLayout.xaxis, title:'Age (ka BP)', autorange:'reversed'}}, yaxis:{{...baseLayout.yaxis, title:'Temperature (°C)'}}}}, cfg);",
        f"Plotly.newPlot('plot-mid-lags', [{{y:{lags.genus.tolist()}, x:{lags.median_lag_yr.tolist()}, error_x:{{type:'data', symmetric:false, array:{(lags.ci_high-lags.median_lag_yr).tolist()}, arrayminus:{(lags.median_lag_yr-lags.ci_low).tolist()}}}, type:'bar', orientation:'h', marker:{{color:'#0072B2'}}}}], {{...baseLayout, title:'Mid-Project Raw Lags (years)', xaxis:{{...baseLayout.xaxis, title:'Median Lag (yr)'}}, yaxis:{{...baseLayout.yaxis, automargin:true}}}}, cfg);",
        f"Plotly.newPlot('plot-mid-na', [{{x:{(na.bin_age/1000).tolist()}, y:{(na.frac_no_analogue*100).round(2).tolist()}, type:'bar', name:'No-analogue (%)', marker:{{color:'#56B4E9'}}}}, {{x:{(na.bin_age/1000).tolist()}, y:{na.abs_climate_rate.round(4).tolist()}, yaxis:'y2', type:'scatter', mode:'lines+markers', name:'|Climate rate| (°C/c.)', line:{{color:'#D55E00',width:2}}}}], {{...baseLayout, title:'No-Analogue Frequency vs |Climate Rate| (TRSH+UPHE)', xaxis:{{...baseLayout.xaxis, title:'Age (ka BP)', autorange:'reversed'}}, yaxis:{{...baseLayout.yaxis, title:'No-analogue (%)'}}, yaxis2:{{title:'|Climate rate| (°C/century)', overlaying:'y', side:'right'}}}}, cfg);",
        f"Plotly.newPlot('plot-mid-mig', [{{y:{mig.genus.tolist()}, x:{mig.rate_m_per_yr.round(1).tolist()}, type:'bar', orientation:'h', name:'1D Migration', marker:{{color:'#009E73'}}}}], {{...baseLayout, title:'1D Northward Migration Speeds vs Modern Velocity ({vel['modern_climate_velocity_m_per_yr']:.0f} m/yr)', xaxis:{{...baseLayout.xaxis, type:'log', title:'Speed (m/yr, log)'}}, shapes:[{{type:'line', x0:{vel['past_p95_climate_velocity_m_per_yr']}, x1:{vel['past_p95_climate_velocity_m_per_yr']}, y0:-0.5, y1:{len(mig)-0.5}, line:{{color:'#0072B2', dash:'dash', width:2}}}}, {{type:'line', x0:{vel['modern_climate_velocity_m_per_yr']}, x1:{vel['modern_climate_velocity_m_per_yr']}, y0:-0.5, y1:{len(mig)-0.5}, line:{{color:'#D55E00', dash:'dot', width:2.5}}}}]}}, cfg);",
    ]
    out_html = C.ROOT / "TBD2_MidProject_Baseline_Report.html"
    out_html.write_text(_shell_html(
        "TBD2 Mid-Project Baseline Report (Pre-Upgrade Snapshot)",
        "Frozen analytical baseline prior to Phase 1 climate unit fixes, TRSH-only filtering, Ebisuzaki detrending, RPP calibration, LegacyAge 1.0 chronologies, and 2D isochrones.",
        [("Mid-Project Snapshot", "warn"), ("72 sites · 1,782 bins", "accent"), ("100% Offline Bundle", "ok")],
        kpis, tab_defs, plots
    ), encoding="utf-8")
    print(f"[report] wrote {out_html}")


def render_final_html():
    mid = C.OUT / "mid_project"
    fig_dir = C.OUT / "figures_final"
    creg = pd.read_csv(C.PROC / "climate_regional.csv").sort_values("bin_age")
    ls_mid = pd.read_csv(mid / "lag_summary_base.csv")
    ls_fin = pd.read_csv(C.OUT / "lag_summary_final_2d.csv")
    lags_site = pd.read_csv(C.OUT / "lags_final_2d.csv")
    na_raw = pd.read_csv(C.OUT / "noanalogue_vs_climate_raw_celsius.csv").sort_values("bin_age")
    na_tr = pd.read_csv(C.OUT / "noanalogue_vs_climate_trsh_only.csv").sort_values("bin_age")
    na_fin = pd.read_csv(C.OUT / "noanalogue_vs_climate_final_2d.csv").sort_values("bin_age")
    mig_mid = pd.read_csv(mid / "migration_base.csv")
    mig_fin = pd.read_csv(C.OUT / "migration_final_2d.csv")
    vel_mid = json.loads((mid / "velocity_comparison_base.json").read_text())
    vel_fin = json.loads((C.OUT / "velocity_comparison_final_2d.json").read_text())
    tests_fin = json.loads((C.OUT / "tests_final_2d.json").read_text())
    ens = json.loads((C.OUT / "ensemble_summary_legacyage.json").read_text())
    ls_250 = pd.read_csv(C.OUT / "lag_summary_bin250.csv")
    manifest = json.loads((C.STAGE_LOGS / "pipeline_run_manifest.json").read_text())

    mid_500 = float(na_raw.loc[na_raw.bin_age == 500, "frac_no_analogue"].iloc[0]) * 100
    tr_500 = float(na_tr.loc[na_tr.bin_age == 500, "frac_no_analogue"].iloc[0]) * 100
    fin_500 = float(na_fin.loc[na_fin.bin_age == 500, "frac_no_analogue"].iloc[0]) * 100
    eb_rate = float((lags_site.p_ebisuzaki < 0.05).mean()) * 100
    mig_2d_med = vel_fin.get("median_genus_migration_2d_m_per_yr") or vel_fin["median_genus_migration_m_per_yr"]
    deficit_x = vel_fin["modern_climate_velocity_m_per_yr"] / mig_2d_med

    kpis = [
        ("Verified Climate Range", f"{creg.temp_c.min():.1f} to {creg.temp_c.max():.1f} °C",
         f"PRECT {creg.precip_mm_day.mean():.2f} mm/day mean" if "precip_mm_day" in creg.columns else "Annual TREFHT"),
        ("Ebisuzaki Significant Lags", f"{eb_rate:.1f}%",
         f"{int((lags_site.p_ebisuzaki<0.05).sum())}/{len(lags_site)} series p<0.05 (N=1000)"),
        ("500 BP No-Analogue Floor", f"{tr_500:.1f}% (Final {fin_500:.1f}%)",
         f"Down from {mid_500:.1f}% Mid-Project (UPHE fixed)"),
        ("2D Migration vs Modern Vel.", f"{mig_2d_med:.1f} m/yr",
         f"Modern {vel_fin['modern_climate_velocity_m_per_yr']:.0f} m/yr ({deficit_x:.1f}× deficit)"),
    ]

    # Stage table from manifest
    stage_rows = []
    for s in manifest["stages"]:
        km = s.get("key_metrics", {})
        stage_rows.append({
            "Stage": f"{s['stage']} · {s['name']}",
            "Tag": s.get("tag", ""),
            "Sites": km.get("n_sites", "—"),
            "Binned": km.get("n_binned", "—"),
            "500 BP NA (%)": round(km["no_analogue_500bp_floor"] * 100, 1) if km.get("no_analogue_500bp_floor") is not None else "—",
            "Ebisuzaki p<0.05 (%)": round(km["ebisuzaki_pass_rate_p05"] * 100, 1) if km.get("ebisuzaki_pass_rate_p05") is not None else "—",
            "Med. Lag (yr)": km.get("median_across_genera_lag_yr", "—"),
            "Mig. (m/yr)": km.get("median_migration_m_per_yr", "—"),
        })
    stage_df = pd.DataFrame(stage_rows)

    # Mid vs Final lag comparison df
    comp_lag = pd.merge(
        ls_mid[["genus", "n_sites", "median_lag_yr"]].rename(columns={"n_sites": "Mid Sites", "median_lag_yr": "Mid Raw Lag (yr)"}),
        ls_fin[["genus", "n_sites", "n_sig_05", "pct_sig_05", "median_lag_yr", "frac_pos_r"]].rename(
            columns={"n_sites": "Final Sites", "n_sig_05": "Sig (p<0.05)", "pct_sig_05": "Pass Rate", "median_lag_yr": "Final Diff Lag (yr)", "frac_pos_r": "Frac +r"}),
        on="genus", how="outer"
    )
    comp_lag["Delta (yr)"] = comp_lag["Final Diff Lag (yr)"] - comp_lag["Mid Raw Lag (yr)"]

    # Mid vs Final migration comparison df
    comp_mig = pd.merge(
        mig_mid[["genus", "n_sites", "rate_m_per_yr"]].rename(columns={"n_sites": "Mid Sites", "rate_m_per_yr": "Mid 1D (m/yr)"}),
        mig_fin[["genus", "n_sites", "rate_m_per_yr", "rate_2d_median_m_per_yr", "mean_azimuth_deg"]].rename(
            columns={"n_sites": "Final Sites", "rate_m_per_yr": "Final 1D (m/yr)", "rate_2d_median_m_per_yr": "Final 2D (m/yr)", "mean_azimuth_deg": "Azimuth (°)"}),
        on="genus", how="outer"
    )

    figs = [
        ("fig1_spatial_overview.png", "Fig 1. Eastern NA basemap showing retained LegacyAge 1.0 (n=57), Neotoma fallback (n=12), and TRSH-dropped (n=4) sites."),
        ("fig2_climate_turnover_events.png", "Fig 2. TraCE-21ka temperature (°C) & precipitation (mm/day) alongside community turnover and Bølling-Allerød / Younger Dryas / 8.2 ka events."),
        ("fig3a_lags_raincloud.png", "Fig 3a. Two-panel synthesis of postglacial forest lag dynamics: (A) Response delay (Median ± 95% CI) across ecological speed tiers, and (B) warming response polarity (% fossil cores cold-retreating −r vs warm-expanding +r with Ebisuzaki p < 0.05)."),
        ("fig3b_mid_vs_final_lags.png", "Fig 3b. Dumbbell comparison between Mid-Project raw lags and Final detrended/RPP/LegacyAge lags."),
        ("fig4_noanalogue_drivers.png", "Fig 4. TRSH+UPHE vs TRSH-only no-analogue trajectories and per-genus SCD driver heatmap."),
        ("fig5a_migration_isochrones.png", "Fig 5a. 2D equal-area arrival isochrones (ka BP) and local migration azimuth vectors."),
        ("fig5b_velocity_deficit.png", "Fig 5b. Log-scale velocity deficit showing 2D speeds (medians and full spatial surface ranges) against past and modern climate velocity ranges."),
    ]
    fig_gallery = "".join(
        f"<figure class='fig-card'><img src='{_b64_img(fig_dir / f)}' alt='{f}'><figcaption>{html.escape(cap)}</figcaption></figure>"
        for f, cap in figs if (fig_dir / f).exists()
    )

    tab_defs = [
        ("fin-overview", "Overview & Figures", f"""
          <h2>Phase 1 Synthesis & Publication Figure Gallery</h2>
          <p class='prose'>All methodological gaps flagged in the Mid-Project review have been resolved and audited across Stages 00–08: TraCE temperatures are verified in °C with annual precipitation (<code>PRECT</code>), agricultural weeds (<code>UPHE</code>) are separated in <code>TRSH-only</code> mode, correlations are first-differenced and tested against 1,000 Ebisuzaki phase-randomized surrogates, counts are RPP-calibrated (Wieczorek &amp; Herzschuh 2020 / Dawson et al. 2016), chronologies use Li et al. (2022) LegacyAge 1.0 with 50-member age-uncertainty ensembles, and migration is modeled as a 2D equal-area arrival surface.</p>
          <div class='grid-2'>{fig_gallery}</div>
        """),
        ("fin-mid-vs-final", "Mid vs. Final Comparison", f"""
          <h2>Direct Mid-Project Baseline vs. Final Methodological Deltas</h2>
          <figure class='fig-card' style='margin-bottom: 20px;'><img src='{_b64_img(fig_dir / "fig3b_mid_vs_final_lags.png")}' alt='Figure 3b'><figcaption>Fig 3b. Dumbbell comparison between Mid-Project raw lags and Final detrended/RPP/LegacyAge lags across tested genera.</figcaption></figure>
          <div class='grid-2'>
            <div id='plot-comp-lag' class='chart-box'></div>
            <div id='plot-comp-na' class='chart-box'></div>
          </div>
          <h3>Genus Lag Comparison (Mid Raw vs. Final Detrended + RPP + LegacyAge)</h3>
          {_html_table(comp_lag, num_cols=("Mid Sites", "Mid Raw Lag (yr)", "Final Sites", "Sig (p<0.05)", "Pass Rate", "Final Diff Lag (yr)", "Frac +r", "Delta (yr)"))}
          <h3>Migration Comparison (Mid 1D OLS vs. Final 2D Spatial Surface)</h3>
          {_html_table(comp_mig, num_cols=("Mid Sites", "Mid 1D (m/yr)", "Final Sites", "Final 1D (m/yr)", "Final 2D (m/yr)", "Azimuth (°)"))}
        """),
        ("fin-ablation", "Stage 00–08 Ablation", f"""
          <h2>Stage-by-Stage Incremental Audit Trail</h2>
          <p class='prose'>Every intermediate stage preserved its own tagged CSV/JSON outputs and structured delta log in <code>data/outputs/stage_logs/</code>.</p>
          {_html_table(stage_df, num_cols=("Sites", "Binned", "500 BP NA (%)", "Ebisuzaki p<0.05 (%)", "Med. Lag (yr)", "Mig. (m/yr)"))}
        """),
        ("fin-rq1", "RQ1: Climate & Lags", f"""
          <h2>Climate Trajectory, Precipitation &amp; Stationary Lags</h2>
          <div class='grid-2' style='margin-bottom: 20px;'>
            <figure class='fig-card'><img src='{_b64_img(fig_dir / "fig2_climate_turnover_events.png")}' alt='Figure 2'><figcaption>Fig 2. TraCE-21ka temperature (°C) &amp; precipitation (mm/day) alongside community turnover and Bølling-Allerød / Younger Dryas / 8.2 ka events.</figcaption></figure>
            <figure class='fig-card'><img src='{_b64_img(fig_dir / "fig3a_lags_raincloud.png")}' alt='Figure 3a'><figcaption>Fig 3a. Two-panel synthesis of postglacial forest lag dynamics: (A) Response delay (Median ± 95% CI) across ecological speed tiers, and (B) warming response polarity (% fossil cores cold-retreating −r vs warm-expanding +r with Ebisuzaki p &lt; 0.05).</figcaption></figure>
          </div>
          <div id='plot-fin-clim' class='chart-box'></div>
          <p class='prose'>Figure 3a synthesizes two fundamental dimensions of forest response: Panel A reveals the response clock across three ecological tiers (Fast pioneer conifer <i>Larix</i> at 750 yr, canopy reorganization taxa at 1,500 yr, and slow climax seeders <i>Fagus</i>/<i>Tsuga</i> at 2,500 yr); Panel B resolves response polarity, showing that while boreal conifers (<i>Picea</i>, 94.9% −r) suffered severe postglacial collapse, temperate hardwoods (<i>Quercus</i>, 79.1% +r; <i>Acer</i>, 67.2% +r) expanded vigorously into newly deglaciated territory.</p>
          {_html_table(ls_fin, num_cols=("n_sites", "n_sig_05", "pct_sig_05", "median_lag_yr", "ci_low", "ci_high", "median_lag_sig_yr", "frac_pos_r", "mean_r"))}
        """),
        ("fin-rq2", "RQ2: No-Analogue", f"""
          <h2>No-Analogue Reduction &amp; Taxonomic SCD Drivers</h2>
          <figure class='fig-card' style='margin-bottom: 20px;'><img src='{_b64_img(fig_dir / "fig4_noanalogue_drivers.png")}' alt='Figure 4'><figcaption>Fig 4. TRSH+UPHE vs TRSH-only no-analogue trajectories and per-genus SCD driver heatmap.</figcaption></figure>
          <p class='prose'>Removing post-settlement <code>UPHE</code> herbs reduces the 500 BP no-analogue floor from {mid_500:.1f}% to {tr_500:.1f}% ({fin_500:.1f}% with RPP + LegacyAge). Deglacial climate-rate Spearman rho = {tests_fin['spearman_noanalogue_vs_abs_climate_rate'][0]:.3f} (Ebisuzaki p = {tests_fin.get('ebisuzaki_p_climate', float('nan')):.4f}); turnover Spearman rho = {tests_fin['spearman_noanalogue_vs_veg_rate'][0]:.3f} (Ebisuzaki p = {tests_fin.get('ebisuzaki_p_veg', float('nan')):.4f}).</p>
          {_html_table(na_fin, num_cols=tuple(na_fin.columns))}
        """),
        ("fin-rq3", "RQ3: 2D Migration", f"""
          <h2>2D Spatial Migration Isochrones &amp; Velocity Deficit</h2>
          <div class='grid-2' style='margin-bottom: 20px;'>
            <figure class='fig-card'><img src='{_b64_img(fig_dir / "fig5a_migration_isochrones.png")}' alt='Figure 5a'><figcaption>Fig 5a. 2D equal-area arrival isochrones (ka BP) and local migration azimuth vectors for validated genera (p_2d ≤ 0.05).</figcaption></figure>
            <figure class='fig-card'><img src='{_b64_img(fig_dir / "fig5b_velocity_deficit.png")}' alt='Figure 5b'><figcaption>Fig 5b. Log-scale velocity deficit showing 2D speeds (medians and full spatial surface ranges) against past and modern climate velocity ranges.</figcaption></figure>
          </div>
          <div id='plot-fin-mig' class='chart-box'></div>
          <div class='notice'>Thermal spatial gradient = {vel_fin['spatial_gradient_c_per_km']:.5f} °C/km; past p95 climate velocity = {vel_fin['past_p95_climate_velocity_m_per_yr']:.1f} m/yr; modern velocity (1.9 °C/century) = {vel_fin['modern_climate_velocity_m_per_yr']:.0f} m/yr vs. Final 2D median migration = {mig_2d_med:.1f} m/yr ({deficit_x:.1f}× deficit).</div>
          {_html_table(mig_fin, num_cols=("n_sites", "rate_m_per_yr", "p", "rate_2d_median_m_per_yr", "rate_2d_iqr_low", "rate_2d_iqr_high", "mean_azimuth_deg", "azimuth_conc"))}
        """),
        ("fin-sens", "Sensitivity (LegacyAge & 250-yr)", f"""
          <h2>LegacyAge 1.0 N=50 Ensemble &amp; 250-yr Adaptive Binning</h2>
          <p class='prose'>Matched {ens.get('matched_sites', 'NA')}/{ens.get('total_sites', 'NA')} fossil sites directly to Li et al. (2022) LegacyAge 1.0 radiocarbon chronologies; remaining sites received depth-scaled uncertainty fallback. Across 50 age-model realizations, genus median lags remained centered at {ens.get('ensemble_median_lag_yr', 'NA')} yr (IQR {ens.get('ensemble_lag_iqr_yr', 'NA')}), and 250-yr adaptive binning reproduced consistent taxonomic ordering across {len(ls_250)} genera.</p>
          {_html_table(ls_250, num_cols=("n_sites", "n_sig_05", "pct_sig_05", "median_lag_yr", "ci_low", "ci_high", "median_lag_sig_yr", "frac_pos_r", "mean_r"))}
        """),
    ]

    comp_valid = comp_lag.dropna(subset=["Mid Raw Lag (yr)", "Final Diff Lag (yr)"])
    mig_valid = mig_fin.dropna(subset=["rate_2d_median_m_per_yr"]).sort_values("rate_2d_median_m_per_yr")
    precip_trace = ""
    if "precip_mm_day" in creg.columns:
        precip_trace = f", {{x:{(creg.bin_age/1000).tolist()}, y:{creg.precip_mm_day.round(3).tolist()}, yaxis:'y2', type:'scatter', mode:'lines', name:'Precip (mm/day)', line:{{color:'#0072B2', dash:'dash', width:2}}}}"
    plots = [
        f"Plotly.newPlot('plot-comp-lag', [{{y:{comp_valid.genus.tolist()}, x:{comp_valid['Mid Raw Lag (yr)'].tolist()}, mode:'markers', name:'Mid Raw Lag', marker:{{color:'#6B7487', size:10}}}}, {{y:{comp_valid.genus.tolist()}, x:{comp_valid['Final Diff Lag (yr)'].tolist()}, mode:'markers', name:'Final Detrended Lag', marker:{{color:'#0072B2', size:11}}}}], {{...baseLayout, title:'Mid-Project Raw vs Final Detrended Lags', xaxis:{{...baseLayout.xaxis, title:'Median Lag (yr)'}}, yaxis:{{...baseLayout.yaxis, automargin:true}}}}, cfg);",
        f"Plotly.newPlot('plot-comp-na', [{{x:{(na_raw.bin_age/1000).tolist()}, y:{(na_raw.frac_no_analogue*100).round(2).tolist()}, mode:'lines', name:'Mid TRSH+UPHE', line:{{color:'#D55E00', dash:'dash'}}}}, {{x:{(na_tr.bin_age/1000).tolist()}, y:{(na_tr.frac_no_analogue*100).round(2).tolist()}, mode:'lines', name:'TRSH-only', line:{{color:'#0072B2', width:2.5}}}}, {{x:{(na_fin.bin_age/1000).tolist()}, y:{(na_fin.frac_no_analogue*100).round(2).tolist()}, mode:'lines', name:'Final (TRSH+RPP+LegacyAge)', line:{{color:'#009E73', width:2}}}}], {{...baseLayout, title:'No-Analogue Reduction Across Upgrades', xaxis:{{...baseLayout.xaxis, title:'Age (ka BP)', autorange:'reversed'}}, yaxis:{{...baseLayout.yaxis, title:'No-analogue (%)'}}}}, cfg);",
        f"Plotly.newPlot('plot-fin-clim', [{{x:{(creg.bin_age/1000).tolist()}, y:{creg.temp_c.round(3).tolist()}, type:'scatter', mode:'lines+markers', name:'Temp (°C)', line:{{color:'#D55E00', width:2.5}}}}{precip_trace}], {{...baseLayout, title:'Verified TraCE-21ka Regional Temperature (°C) & Precipitation (mm/day)', xaxis:{{...baseLayout.xaxis, title:'Age (ka BP)', autorange:'reversed'}}, yaxis:{{...baseLayout.yaxis, title:'Temperature (°C)'}}, yaxis2:{{title:'Precip (mm/day)', overlaying:'y', side:'right'}}}}, cfg);",
        f"Plotly.newPlot('plot-fin-mig', [{{y:{mig_valid.genus.tolist()}, x:{mig_valid.rate_2d_median_m_per_yr.round(1).tolist()}, type:'bar', orientation:'h', name:'Final 2D Median Speed', marker:{{color:'#009E73'}}}}], {{...baseLayout, title:'Final 2D Migration Speeds vs Modern Velocity ({vel_fin['modern_climate_velocity_m_per_yr']:.0f} m/yr)', xaxis:{{...baseLayout.xaxis, type:'log', title:'Speed (m/yr, log)'}}, shapes:[{{type:'line', x0:{vel_fin['past_p95_climate_velocity_m_per_yr']}, x1:{vel_fin['past_p95_climate_velocity_m_per_yr']}, y0:-0.5, y1:{len(mig_valid)-0.5}, line:{{color:'#0072B2', dash:'dash', width:2}}}}, {{type:'line', x0:{vel_fin['modern_climate_velocity_m_per_yr']}, x1:{vel_fin['modern_climate_velocity_m_per_yr']}, y0:-0.5, y1:{len(mig_valid)-0.5}, line:{{color:'#D55E00', dash:'dot', width:2.5}}}}]}}, cfg);",
    ]
    out_html = C.ROOT / "TBD2_Final_Report.html"
    out_html.write_text(_shell_html(
        "TBD2 Final Report (Phase 1): Climate-Vegetation Lags, No-Analogue Attribution & 2D Migration",
        "Complete Phase 1 synthesis across 68–72 eastern North American fossil pollen sites, verified TraCE-21ka temperature & precipitation, REVEALS RPP calibration, LegacyAge 1.0 chronologies, Ebisuzaki stationary tests, and 2D spatial isochrones.",
        [("Phase 1 Final", "ok"), ("Stages 00–08 Audited", "accent"), ("100% Offline Self-Contained", "accent")],
        kpis, tab_defs, plots
    ), encoding="utf-8")
    print(f"[report] wrote {out_html}")


def render_standalone_html():
    fig_dir = C.OUT / "figures_standalone"
    creg = pd.read_csv(C.PROC / "climate_regional.csv").sort_values("bin_age")
    sites_fin = pd.read_csv(C.PROC / "sites_final_2d.csv")
    binned_fin = pd.read_csv(C.PROC / "binned_final_2d.csv")
    ls_fin = pd.read_csv(C.OUT / "lag_summary_final_2d.csv")
    lags_site = pd.read_csv(C.OUT / "lags_final_2d.csv")
    na_fin = pd.read_csv(C.OUT / "noanalogue_vs_climate_final_2d.csv").sort_values("bin_age")
    mig_fin = pd.read_csv(C.OUT / "migration_final_2d.csv")
    vel_fin = json.loads((C.OUT / "velocity_comparison_final_2d.json").read_text())
    tests_fin = json.loads((C.OUT / "tests_final_2d.json").read_text())
    ens = json.loads((C.OUT / "ensemble_summary_legacyage.json").read_text())
    ls_250 = pd.read_csv(C.OUT / "lag_summary_bin250.csv")

    fin_500 = float(na_fin.loc[na_fin.bin_age == 500, "frac_no_analogue"].iloc[0]) * 100
    na_peak = float(na_fin.frac_no_analogue.max()) * 100
    na_peak_ka = float(na_fin.loc[na_fin.frac_no_analogue.idxmax(), "bin_age"]) / 1000.0
    eb_rate = float((lags_site.p_ebisuzaki < 0.05).mean()) * 100
    mig_2d_med = vel_fin.get("median_genus_migration_2d_m_per_yr") or vel_fin["median_genus_migration_m_per_yr"]
    deficit_x = vel_fin["modern_climate_velocity_m_per_yr"] / mig_2d_med

    kpis = [
        ("Regional TraCE Climate", f"{creg.temp_c.min():.1f} to {creg.temp_c.max():.1f} °C",
         f"Mean precipitation {creg.precip_mm_day.mean():.2f} mm/day"),
        ("Ebisuzaki Significant Lags", f"{eb_rate:.1f}%",
         f"{int((lags_site.p_ebisuzaki<0.05).sum())}/{len(lags_site)} core-genus series (N=1000 surrogates)"),
        ("No-Analogue Dynamics", f"Peak {na_peak:.1f}% ({na_peak_ka:.1f} ka)",
         f"500 BP pre-colonial floor = {fin_500:.1f}% (threshold {tests_fin['no_analogue_threshold_scd']:.4f})"),
        ("2D Migration vs Modern Vel.", f"{mig_2d_med:.1f} m/yr",
         f"Modern {vel_fin['modern_climate_velocity_m_per_yr']:.0f} m/yr ({deficit_x:.1f}× climate deficit)"),
    ]

    figs = [
        ("fig1_study_sites.png", "Fig 1. Study corridor across Eastern North America (69 retained cores, 1,706 bins) showing LegacyAge 1.0 (blue, n=57), Neotoma fallback (amber, n=12), and excluded sites (red ×, n=4)."),
        ("fig2_climate_and_turnover.png", "Fig 2. TraCE-21ka regional temperature (°C) & precipitation (mm/day), warming rate, and median community turnover (± IQR ribbon) across abrupt climate events."),
        ("fig3_genus_lags_raincloud.png", "Fig 3. Two-panel synthesis of postglacial forest lag dynamics: (A) Response delay (Median ± 95% CI) across ecological speed tiers, and (B) warming response polarity (% fossil cores cold-retreating −r vs warm-expanding +r with Ebisuzaki p < 0.05)."),
        ("fig4_noanalogue_drivers.png", "Fig 4. Top: No-analogue forest prevalence (%) vs. |climate rate|. Bottom: Mean Squared Chord Distance (SCD) contribution heatmap across top taxonomic drivers."),
        ("fig5_migration_isochrones.png", "Fig 5. Postglacial 2D arrival age isochrones (ka BP) and local migration azimuth vectors for validated genera (p_2d ≤ 0.05)."),
        ("fig6_velocity_deficit.png", "Fig 6. Log-scale velocity deficit showing validated 2D migration medians and full spatial surface ranges against past and modern climate velocity ranges."),
    ]
    fig_gallery = "".join(
        f"<figure class='fig-card'><img src='{_b64_img(fig_dir / f)}' alt='{f}'><figcaption>{html.escape(cap)}</figcaption></figure>"
        for f, cap in figs if (fig_dir / f).exists()
    )

    tab_defs = [
        ("stan-overview", "Overview & Figures", f"""
          <h2>Eastern North American Late-Quaternary Forest Dynamics</h2>
          <p class='prose'>This synthesis integrates 15,000 years of fossil pollen across {len(sites_fin)} continuous sediment cores ({len(binned_fin):,} 500-year bins) and 611 quality-filtered modern surface samples. The experimental framework couples TraCE-21ka transient paleoclimate simulations (°C and mm/day), woody arboreal pollen isolation (TRSH-only), empirical REVEALS Relative Pollen Productivity calibration, LegacyAge 1.0 Bayesian radiocarbon chronologies with age-uncertainty ensembles, first-differenced stationary cross-correlation with 1,000-surrogate Ebisuzaki phase-randomization tests, additive Squared Chord Distance (SCD) driver attribution, and 2D equal-area arrival surfaces.</p>
          <div class='grid-2'>{fig_gallery}</div>
        """),
        ("stan-rq1", "RQ1: Climate Lags", f"""
          <h2>Stationary Genus-Level Response Lags Behind Climate</h2>
          <div class='grid-2' style='margin-bottom: 20px;'>
            <figure class='fig-card'><img src='{_b64_img(fig_dir / "fig3_genus_lags_raincloud.png")}' alt='Figure 3'><figcaption>Fig 3. Two-panel synthesis of postglacial forest lag dynamics: (A) Response delay timeline across ecological speed tiers, and (B) warming response polarity (% fossil cores cold-retreating −r vs warm-expanding +r with Ebisuzaki p &lt; 0.05).</figcaption></figure>
            <div id='plot-stan-lags' class='chart-box'></div>
          </div>
          <p class='prose'>First-differenced cross-correlation evaluates whether sudden climate shifts trigger tree abundance changes k bins later, controlling strictly for 15,000-year background trends. Kruskal–Wallis testing confirms robust genus differentiation (H = {tests_fin['kruskal_H']:.2f}, p = {tests_fin['kruskal_p']:.5f}). Figure 3 synthesizes this in two linked dimensions: Panel A tracks response delay across three ecological tiers (Fast pioneer conifer <i>Larix</i> at 750 yr, broadleaf canopy reorganization at 1,500 yr, and late climax seeders at 2,000–2,500 yr); Panel B separates the biological direction of change, contrasting cold-tracking boreal collapse (<i>Picea</i> 94.9% −r, 78% Ebisuzaki sig) with warm-tracking temperate expansion (<i>Quercus</i> 79.1% +r, <i>Acer</i> 67.2% +r).</p>
          {_html_table(ls_fin, num_cols=("n_sites", "n_sig_05", "pct_sig_05", "median_lag_yr", "ci_low", "ci_high", "median_lag_sig_yr", "frac_pos_r", "mean_r"))}
        """),
        ("stan-rq2", "RQ2: No-Analogue Forests", f"""
          <h2>No-Analogue Assemblages &amp; Taxonomic SCD Drivers</h2>
          <div class='grid-2' style='margin-bottom: 20px;'>
            <figure class='fig-card'><img src='{_b64_img(fig_dir / "fig4_noanalogue_drivers.png")}' alt='Figure 4'><figcaption>Fig 4. Top: No-analogue forest prevalence (%) vs. |climate rate|. Bottom: Mean Squared Chord Distance (SCD) contribution heatmap across top taxonomic drivers.</figcaption></figure>
            <div id='plot-stan-na' class='chart-box'></div>
          </div>
          <p class='prose'>No-analogue forest prevalence peaks during early deglaciation at {na_peak:.1f}% ({na_peak_ka:.1f} ka BP) and falls to {fin_500:.1f}% by 500 BP under the modern 5th-percentile threshold ({tests_fin['no_analogue_threshold_scd']:.4f}). Community turnover significantly correlates with no-analogue prevalence under 1,000 Ebisuzaki surrogates (rho = {tests_fin['spearman_noanalogue_vs_veg_rate'][0]:.3f}, p = {tests_fin.get('ebisuzaki_p_veg', float('nan')):.3f}).</p>
          {_html_table(na_fin, num_cols=tuple(na_fin.columns))}
        """),
        ("stan-rq3", "RQ3: 2D Tree Migration", f"""
          <h2>2D Spatial Migration Isochrones &amp; Modern Velocity Deficit</h2>
          <div class='grid-2' style='margin-bottom: 20px;'>
            <figure class='fig-card'><img src='{_b64_img(fig_dir / "fig5_migration_isochrones.png")}' alt='Figure 5'><figcaption>Fig 5. Postglacial 2D arrival age isochrones (ka BP) and local migration azimuth vectors for validated genera (p_2d ≤ 0.05).</figcaption></figure>
            <figure class='fig-card'><img src='{_b64_img(fig_dir / "fig6_velocity_deficit.png")}' alt='Figure 6'><figcaption>Fig 6. Log-scale velocity deficit showing validated 2D migration medians and full spatial surface ranges against past and modern climate velocity ranges.</figcaption></figure>
          </div>
          <div id='plot-stan-mig' class='chart-box'></div>
          <p class='prose'>Five genera pass the 2D planar F-test (p_2d ≤ 0.05), demonstrating coherent postglacial dispersal corridors (Carya 277.0 m/yr ENE, Alnus 264.6 m/yr WNW, Fagus 169.6 m/yr NNW, Larix 124.0 m/yr N, Tsuga 116.9 m/yr NNW). Overall median tree migration ({mig_2d_med:.1f} m/yr) trails modern anthropogenic climate velocity ({vel_fin['modern_climate_velocity_m_per_yr']:.0f} m/yr) by {deficit_x:.1f}×.</p>
          <div class='notice'>Thermal spatial gradient = {vel_fin['spatial_gradient_c_per_km']:.5f} °C/km; past p95 deglacial velocity = {vel_fin['past_p95_climate_velocity_m_per_yr']:.1f} m/yr; contemporary climate-zone velocity (1.9 °C/century) = {vel_fin['modern_climate_velocity_m_per_yr']:.0f} m/yr.</div>
          {_html_table(mig_fin, num_cols=("n_sites", "rate_m_per_yr", "p", "rate_2d_median_m_per_yr", "rate_2d_iqr_low", "rate_2d_iqr_high", "mean_azimuth_deg", "azimuth_conc"))}
        """),
        ("stan-climate-sens", "Climate & Sensitivity", f"""
          <h2>TraCE-21ka Climate, LegacyAge Ensemble &amp; 250-Year Binning</h2>
          <div class='grid-2' style='margin-bottom: 20px;'>
            <figure class='fig-card'><img src='{_b64_img(fig_dir / "fig1_study_sites.png")}' alt='Figure 1'><figcaption>Fig 1. Study corridor across Eastern North America (69 retained cores, 1,706 bins) showing LegacyAge 1.0 (blue, n=57), Neotoma fallback (amber, n=12), and excluded sites (red ×, n=4).</figcaption></figure>
            <figure class='fig-card'><img src='{_b64_img(fig_dir / "fig2_climate_and_turnover.png")}' alt='Figure 2'><figcaption>Fig 2. TraCE-21ka regional temperature (°C) &amp; precipitation (mm/day), warming rate, and median community turnover (± IQR ribbon) across abrupt climate events.</figcaption></figure>
          </div>
          <div id='plot-stan-clim' class='chart-box'></div>
          <p class='prose'>Across 50 Monte Carlo age-model draws from LegacyAge depth uncertainty, median genus lag remained locked at {ens['ensemble_median_lag_yr']:.0f} yr (IQR {ens['ensemble_lag_iqr_yr']}). High-resolution 250-year binning across {len(ls_250)} genera confirmed consistent pioneer-to-climax taxonomic ordering.</p>
          {_html_table(ls_250, num_cols=("n_sites", "n_sig_05", "pct_sig_05", "median_lag_yr", "ci_low", "ci_high", "median_lag_sig_yr", "frac_pos_r", "mean_r"))}
        """),
    ]

    mig_valid = mig_fin.dropna(subset=["rate_2d_median_m_per_yr"]).sort_values("rate_2d_median_m_per_yr")
    precip_trace = ""
    if "precip_mm_day" in creg.columns:
        precip_trace = f", {{x:{(creg.bin_age/1000).tolist()}, y:{creg.precip_mm_day.round(3).tolist()}, yaxis:'y2', type:'scatter', mode:'lines', name:'Precipitation (mm/day)', line:{{color:'#0072B2', dash:'dash', width:2}}}}"

    plots = [
        f"Plotly.newPlot('plot-stan-clim', [{{x:{(creg.bin_age/1000).tolist()}, y:{creg.temp_c.round(3).tolist()}, type:'scatter', mode:'lines+markers', name:'Temperature (°C)', line:{{color:'#D55E00', width:2.5}}}}{precip_trace}], {{...baseLayout, title:'TraCE-21ka Regional Temperature (°C) & Precipitation (mm/day)', xaxis:{{...baseLayout.xaxis, title:'Age (ka BP)', autorange:'reversed'}}, yaxis:{{...baseLayout.yaxis, title:'Temperature (°C)'}}, yaxis2:{{title:'Precipitation (mm/day)', overlaying:'y', side:'right'}}}}, cfg);",
        f"Plotly.newPlot('plot-stan-lags', [{{y:{ls_fin.genus.tolist()}, x:{ls_fin.median_lag_yr.tolist()}, error_x:{{type:'data', symmetric:false, array:{(ls_fin.ci_high-ls_fin.median_lag_yr).tolist()}, arrayminus:{(ls_fin.median_lag_yr-ls_fin.ci_low).tolist()}}}, type:'bar', orientation:'h', marker:{{color:'#0072B2'}}}}], {{...baseLayout, title:'Stationary Detrended Genus Lags Behind Temperature (years)', xaxis:{{...baseLayout.xaxis, title:'Median Lag (yr)'}}, yaxis:{{...baseLayout.yaxis, automargin:true}}}}, cfg);",
        f"Plotly.newPlot('plot-stan-na', [{{x:{(na_fin.bin_age/1000).tolist()}, y:{(na_fin.frac_no_analogue*100).round(2).tolist()}, type:'scatter', mode:'lines+markers', name:'No-analogue (%)', line:{{color:'#0072B2', width:2.5}}, fill:'tozeroy', fillcolor:'rgba(86,180,233,0.18)'}}, {{x:{(na_fin.bin_age/1000).tolist()}, y:{na_fin.abs_climate_rate.round(4).tolist()}, yaxis:'y2', type:'scatter', mode:'lines', name:'|Climate rate| (°C/c.)', line:{{color:'#D55E00', dash:'dash', width:2}}}}], {{...baseLayout, title:'No-Analogue Forest Frequency vs. Absolute Climate Rate', xaxis:{{...baseLayout.xaxis, title:'Age (ka BP)', autorange:'reversed'}}, yaxis:{{...baseLayout.yaxis, title:'No-analogue (%)'}}, yaxis2:{{title:'|Climate rate| (°C/century)', overlaying:'y', side:'right'}}}}, cfg);",
        f"Plotly.newPlot('plot-stan-mig', [{{y:{mig_valid.genus.tolist()}, x:{mig_valid.rate_2d_median_m_per_yr.round(1).tolist()}, type:'bar', orientation:'h', name:'2D Median Speed', marker:{{color:'#009E73'}}}}], {{...baseLayout, title:'Validated 2D Tree Migration Speeds vs. Modern Climate Velocity ({vel_fin['modern_climate_velocity_m_per_yr']:.0f} m/yr)', xaxis:{{...baseLayout.xaxis, type:'log', title:'Speed (m/yr, log scale)'}}, shapes:[{{type:'line', x0:{vel_fin['past_p95_climate_velocity_m_per_yr']}, x1:{vel_fin['past_p95_climate_velocity_m_per_yr']}, y0:-0.5, y1:{len(mig_valid)-0.5}, line:{{color:'#0072B2', dash:'dash', width:2}}}}, {{type:'line', x0:{vel_fin['modern_climate_velocity_m_per_yr']}, x1:{vel_fin['modern_climate_velocity_m_per_yr']}, y0:-0.5, y1:{len(mig_valid)-0.5}, line:{{color:'#D55E00', dash:'dot', width:2.5}}}}]}}, cfg);",
    ]
    out_html = C.ROOT / "TBD2_Project_Report_Standalone.html"
    out_html.write_text(_shell_html(
        "Late-Quaternary Climate–Vegetation Lags, No-Analogue Attribution & 2D Tree Migration",
        "Comprehensive paleoecological synthesis across 69 Eastern North American lake sediment cores (1,706 bins), TraCE-21ka paleoclimate, REVEALS RPP calibration, LegacyAge 1.0 chronologies, Ebisuzaki stationary tests, and 2D spatial isochrones.",
        [("Final Synthesis", "ok"), ("69 Sites · 1,706 Bins", "accent"), ("100% Offline Bundle", "accent")],
        kpis, tab_defs, plots
    ), encoding="utf-8")
    print(f"[report] wrote {out_html}")


def render_final_docx():
    return build_final_report_docx_and_pdf()


def render_standalone_docx():
    return build_standalone_report_docx_and_pdf()


def verify_reports():
    from selenium import webdriver
    from selenium.webdriver.edge.options import Options as EdgeOptions
    from selenium.webdriver.chrome.options import Options as ChromeOptions

    html_targets = ["TBD2_MidProject_Baseline_Report.html", "TBD2_Final_Report.html"]
    stan_html = C.ROOT / "TBD2_Project_Report_Standalone.html"
    if stan_html.exists():
        html_targets.append("TBD2_Project_Report_Standalone.html")

    for name in html_targets:
        p = C.ROOT / name
        assert p.exists() and p.stat().st_size > 100_000, f"missing/tiny {name}"

    for docx_name, pdf_name in [
        ("TBD2_Final_Project_Report.docx", "TBD2_Final_Project_Report.pdf"),
        ("TBD2_Project_Report_Standalone.docx", "TBD2_Project_Report_Standalone.pdf"),
    ]:
        dp = C.ROOT / docx_name
        if not dp.exists():
            continue
        d = docx.Document(dp)
        assert len(d.paragraphs) > 40 and len(d.tables) >= 4, f"{docx_name} structure incomplete"
        docx_txt = "\n".join(p.text for p in d.paragraphs).lower()
        assert "phase 1" not in docx_txt and "phase 2" not in docx_txt, f"Unexpected phase mention in {docx_name}"

        pp = C.ROOT / pdf_name
        assert pp.exists() and pp.stat().st_size > 100_000, f"missing/tiny {pdf_name}"
        with pymupdf.open(pp) as pdf_doc:
            assert len(pdf_doc) >= 6, f"{pdf_name} page count low: {len(pdf_doc)}"
            pdf_txt = "\n".join(page.get_text() for page in pdf_doc).lower()
            assert "phase 1" not in pdf_txt and "phase 2" not in pdf_txt, f"Unexpected phase mention in {pdf_name}"
            print(f"[verify] {pdf_name}: {len(pdf_doc)} pages, {pp.stat().st_size:,} bytes")

    driver = None
    for kind in ("edge", "chrome"):
        try:
            if kind == "edge":
                opts = EdgeOptions()
                opts.add_argument("--headless=new")
                opts.add_argument("--disable-gpu")
                driver = webdriver.Edge(options=opts)
            else:
                opts = ChromeOptions()
                opts.add_argument("--headless=new")
                opts.add_argument("--disable-gpu")
                driver = webdriver.Chrome(options=opts)
            break
        except Exception:
            continue
    assert driver is not None, "No headless Edge/Chrome driver available"
    try:
        for name in html_targets:
            url = (C.ROOT / name).resolve().as_uri()
            driver.get(url)
            res = driver.execute_script("""
              const imgs = Array.from(document.querySelectorAll('img'));
              const badImgs = imgs.filter(i => !i.complete || i.naturalWidth === 0).length;
              const tabs = document.querySelectorAll('[role="tab"]');
              tabs.forEach(t => t.click());
              const plots = document.querySelectorAll('.js-plotly-plot').length;
              return {title: document.title, imgs: imgs.length, badImgs, tabs: tabs.length, plots};
            """)
            assert res["badImgs"] == 0 and res["imgs"] >= 5 and res["plots"] >= 3, f"{name} DOM check failed: {res}"
            print(f"[verify] {name}: {res}")
    finally:
        driver.quit()
    print("G7_REPORTS_VERIFIED_OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["mid_project", "final", "standalone", "all"], default="standalone")
    ap.add_argument("--verify-only", action="store_true")
    a = ap.parse_args()
    if a.verify_only:
        verify_reports()
    elif a.mode == "mid_project":
        render_mid_html()
    elif a.mode == "final":
        render_final_html()
        render_final_docx()
    elif a.mode == "standalone":
        render_standalone_html()
        render_standalone_docx()
    elif a.mode == "all":
        render_mid_html()
        render_final_html()
        render_final_docx()
        render_standalone_html()
        render_standalone_docx()
        verify_reports()
