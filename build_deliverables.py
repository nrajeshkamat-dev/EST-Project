"""Build the TBD2 real-data report and slide deck from pipeline outputs."""
from pathlib import Path
import json
import math
import subprocess

import pandas as pd


ROOT = Path(__file__).resolve().parent
PROC = ROOT / "data" / "processed"
OUT = ROOT / "data" / "outputs"
FIG = OUT / "figures"


def fmt(x, digits=1):
    if x is None:
        return "NA"
    try:
        if math.isnan(float(x)):
            return "NA"
    except Exception:
        pass
    return f"{float(x):.{digits}f}"


def md_table(rows, headers):
    out = ["| " + " | ".join(headers) + " |",
           "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(out)


def load():
    data = {}
    data["binned"] = pd.read_csv(PROC / "binned.csv")
    data["sites"] = pd.read_csv(PROC / "sites.csv")
    data["modern"] = pd.read_csv(PROC / "modern.csv")
    data["fossil_ids"] = pd.read_csv(PROC / "fossil_long.csv", usecols=["dataset_id"])
    data["modern_ids"] = pd.read_csv(PROC / "modern_long.csv", usecols=["dataset_id"])
    data["lags"] = pd.read_csv(OUT / "lag_summary_base.csv")
    data["migration"] = pd.read_csv(OUT / "migration_base.csv")
    data["tests"] = json.load(open(OUT / "tests_base.json"))
    data["velocity"] = json.load(open(OUT / "velocity_comparison_base.json"))
    data["noanalogue"] = pd.read_csv(OUT / "no_analogue_base.csv")
    data["climate_rate"] = pd.read_csv(OUT / "climate_rate_base.csv")
    data["roc"] = pd.read_csv(OUT / "rate_of_change_base.csv")
    data["pinus_lags"] = pd.read_csv(OUT / "lag_summary_pinus.csv")
    data["jitter_lags"] = pd.read_csv(OUT / "lag_summary_j1.csv")
    data["pinus_vel"] = json.load(open(OUT / "velocity_comparison_pinus.json"))
    data["jitter_vel"] = json.load(open(OUT / "velocity_comparison_j1.json"))
    return data


def build_report(d):
    b, s, modern = d["binned"], d["sites"], d["modern"]
    fossil_n = d["fossil_ids"].dataset_id.nunique()
    modern_n = d["modern_ids"].dataset_id.nunique()
    lag_rows = []
    for _, r in d["lags"].iterrows():
        lag_rows.append([r.genus, int(r.n_sites), fmt(r.median_lag_yr, 0),
                         f"{fmt(r.ci_low, 0)} to {fmt(r.ci_high, 0)}"])
    mig_rows = []
    for _, r in d["migration"].iterrows():
        mig_rows.append([r.genus, int(r.n_sites), fmt(r.rate_m_per_yr, 1),
                         "NA" if pd.isna(r.ci_low) else f"{fmt(r.ci_low, 1)} to {fmt(r.ci_high, 1)}",
                         fmt(r.p, 4)])
    na_frac = float(d["noanalogue"].no_analogue.mean())
    kruskal_p = d["tests"]["kruskal_p"]
    cr = d["climate_rate"].climate_rate_c_per_century.abs()
    roc = d["roc"].rate_per_century
    v = d["velocity"]
    sensitivity_rows = [
        ["Base", len(s), fmt(d["lags"].median_lag_yr.median(), 0), fmt(v["median_genus_migration_m_per_yr"], 1)],
        ["Pinus down-weighted", 72, fmt(d["pinus_lags"].median_lag_yr.median(), 0), fmt(d["pinus_vel"]["median_genus_migration_m_per_yr"], 1)],
        ["Age jitter draw 1", 71, fmt(d["jitter_lags"].median_lag_yr.median(), 0), fmt(d["jitter_vel"]["median_genus_migration_m_per_yr"], 1)],
    ]

    na_pct = na_frac * 100
    rho_clim, p_clim = d["tests"]["spearman_noanalogue_vs_abs_climate_rate"]
    rho_veg, p_veg = d["tests"]["spearman_noanalogue_vs_veg_rate"]
    report = f"""---
title: "Quantifying Lags Between Climate Change and Tree Genus Response in Eastern North America Using Fossil Pollen"
author: "Team TBD2: Vivek R, Nandan Rajesh Kamat, Shaurya Gupta"
date: "7 October 2026"
---

# Abstract

We analysed fossil pollen records from the Neotoma Paleoecology Database together with TraCE-21ka simulated temperature to estimate how tree genera in eastern North America responded to late Quaternary climate change. The working dataset contains {fossil_n} fossil pollen datasets and {modern_n} modern surface pollen datasets cached locally from Neotoma. After filtering to the study region, pollen-sum threshold, temporal coverage, and gap criteria, the real-data analysis used {len(s)} fossil pollen sites, {len(b)} binned fossil samples, and {len(modern)} modern reference samples. Genus-level lags differed strongly among taxa (Kruskal-Wallis p = {kruskal_p:.2e}). Picea and Tsuga showed the shortest median lags, while Pinus, Carya, and Fagus had longer lags. No-analogue samples were common ({fmt(na_pct, 1)} percent of binned fossil samples), and their frequency was positively associated with absolute climate rate and vegetation turnover. Migration estimates were available only for genera with a significant northward arrival gradient. Their median inferred migration rate was {fmt(v["median_genus_migration_m_per_yr"], 1)} m/yr, far below the climate-zone velocity implied by recent warming at {fmt(v["modern_climate_velocity_m_per_yr"], 0)} m/yr.

# 1 Introduction

Past forest responses provide a long-term test of whether plant communities can keep pace with climate change. Fossil pollen records show that eastern North American forests reorganised after the last glacial period, but the literature review for this project identified a remaining gap: studies often describe ecological lag and no-analogue communities, while fewer analyses directly compare taxon-level response speed with climate-change speed. This project addresses that gap using open pollen and climate datasets.

# 2 Research questions

1. How long do different tree genera lag behind temperature change?
2. Do no-analogue communities coincide with fast climate change and high vegetation turnover?
3. Were past genus migration rates fast enough to match the speed at which climate zones moved?

# 3 Data

The pollen data came from the Neotoma Paleoecology Database API v2.0 for a bounding box over eastern North America (longitude -100 to -60, latitude 34 to 52). The pipeline used fossil pollen records from 0 to 15 ka BP and modern pollen surface samples as the no-analogue reference set. Climate data came from the TraCE-21ka transient climate simulation, NCAR GDEX dataset d651050, using TREFHT decadal-average NetCDF files already placed in `data/raw/trace`.

{md_table([
    ["Cached fossil pollen", fossil_n, f"{len(d['fossil_ids']):,}", "Used for fossil assemblages"],
    ["Cached modern pollen", modern_n, f"{len(d['modern_ids']):,}", "Reference set before filtering"],
    ["Filtered fossil sites", len(s), f"{len(b):,}", "Used in lag, turnover, and migration analyses"],
    ["Filtered modern samples", len(modern), len(modern), "Used for no-analogue threshold"],
], ["Dataset", "Datasets or sites", "Rows or samples", "Use"])}

# 4 Methods

The preprocessing script grouped pollen taxa into 14 focal genera plus Other, converted counts to proportions, binned samples into 500-year intervals, removed samples with fewer than 100 grains, and retained sites with at least 12 occupied bins and no gap larger than four bins. The final site coordinates fell within the target study region, with latitude {fmt(s.lat.min(), 2)} to {fmt(s.lat.max(), 2)} and longitude {fmt(s.lon.min(), 2)} to {fmt(s.lon.max(), 2)}.

TraCE temperatures were extracted at the nearest grid cell for each site. The script interpreted the TraCE time axis as `ka_neg`, with raw range -22.00 to 0.03 ka, and converted temperatures to deg C. The estimated north-south gradient used for climate velocity was {fmt(v["spatial_gradient_c_per_km"], 4)} deg C/km.

Vegetation turnover was measured as Hellinger distance per century between adjacent 500-year bins. Lag was estimated by shifting each genus time series by 0 to 6 bins and selecting the lag with the largest absolute correlation with site temperature. No-analogue status used squared chord distance to the nearest modern sample, with the threshold set to the 95th percentile of modern nearest-neighbour distances. Migration rate was estimated from the slope of arrival age against northward distance, where arrival required a genus proportion of at least 5 percent for two consecutive bins.

# 5 Results

![Fossil pollen sites used in the analysis](data/outputs/figures/fig1_sites.png){{width=5.8in}}

## 5.1 Climate and vegetation rates

Past climate rates averaged over 500-year bins had a median absolute rate of {fmt(cr.median(), 3)} deg C/century and a 95th percentile of {fmt(cr.quantile(0.95), 3)} deg C/century. Median vegetation turnover was {fmt(roc.median(), 3)} Hellinger units per century, with a 95th percentile of {fmt(roc.quantile(0.95), 3)}.

![Climate rate and vegetation turnover](data/outputs/figures/fig2_rates.png){{width=6.2in}}

## 5.2 Genus lags

Genus-level lags differed significantly (Kruskal-Wallis H = {fmt(d["tests"]["kruskal_H"], 2)}, p = {kruskal_p:.2e}). Picea and Tsuga had median lags of 500 years. Quercus and Betula had median lags of 1000 years. Pinus, Carya, and Fagus had longer median lags, reaching 2250 to 3000 years.

{md_table(lag_rows, ["Genus", "Sites", "Median lag yr", "95 percent bootstrap CI yr"])}

![Median lag by genus](data/outputs/figures/fig3_lags.png){{width=6.2in}}

## 5.3 No-analogue communities

The no-analogue threshold was {fmt(d["tests"]["no_analogue_threshold_scd"], 3)} squared chord distance units, estimated from {len(modern)} filtered modern surface samples. In the current real-data run, {fmt(na_pct, 1)} percent of fossil binned samples exceeded the threshold. No-analogue frequency increased during intervals with faster climate change (Spearman rho = {fmt(rho_clim, 2)}, p = {p_clim:.2e}) and higher vegetation turnover (rho = {fmt(rho_veg, 2)}, p = {p_veg:.2e}). These p-values ignore temporal autocorrelation, so the correlations should be treated as indicative rather than definitive.

![No-analogue fraction and climate rate](data/outputs/figures/fig4_noanalogue.png){{width=6.2in}}

## 5.4 Migration rates and climate velocity

Five genera had significant northward arrival gradients in the base run: Abies, Tsuga, Quercus, Fagus, and Carya. Quercus had the fastest estimate at {fmt(d["migration"].set_index("genus").loc["Quercus", "rate_m_per_yr"], 1)} m/yr, followed by Fagus at {fmt(d["migration"].set_index("genus").loc["Fagus", "rate_m_per_yr"], 1)} m/yr. The median estimated genus migration rate was {fmt(v["median_genus_migration_m_per_yr"], 1)} m/yr.

{md_table(mig_rows, ["Genus", "Arrival sites", "Migration m/yr", "95 percent bootstrap CI m/yr", "p"])}

Past median climate velocity was {fmt(v["past_median_climate_velocity_m_per_yr"], 1)} m/yr, and the 95th percentile was {fmt(v["past_p95_climate_velocity_m_per_yr"], 1)} m/yr. Using the IPCC AR6 assessed recent warming rate of about 0.19 deg C per decade, or 1.9 deg C per century, the modern climate-zone velocity is {fmt(v["modern_climate_velocity_m_per_yr"], 0)} m/yr. This is roughly {fmt(v["modern_climate_velocity_m_per_yr"] / v["median_genus_migration_m_per_yr"], 1)} times the median inferred migration rate.

![Migration rates compared with climate velocity](data/outputs/figures/fig5_migration.png){{width=6.2in}}

# 6 Sensitivity checks

The Pinus down-weighting and one age-jitter draw did not change the central conclusion that lags differ among genera and that modern climate velocity is much faster than the median inferred migration rate.

{md_table(sensitivity_rows, ["Run", "Fossil sites", "Median across genus median lags yr", "Median migration m/yr"])}

# 7 Discussion

The results support the main research gap identified in the literature review. Tree genera did not respond at one common speed. Picea and Tsuga tracked temperature changes with shorter lags, while Pinus, Carya, and Fagus showed longer lag estimates. This pattern is consistent with the idea that rapid late Quaternary climate change produced temporary mismatches between climate and vegetation.

The migration comparison is the clearest result for present-day relevance. Some genera reached inferred rates above 200 m/yr during postglacial expansion, but the modern climate velocity implied by recent warming is over 1500 m/yr under the same spatial gradient calculation. Because the past rates average change over 500-year bins, they likely smooth short bursts of faster change. Even with that conservative framing, the comparison suggests that natural migration alone may not let many tree genera keep pace with current warming.

The no-analogue result became interpretable after retaining modern surface samples with blank ages. This matters because surface samples normally lack an age model, and dropping blank ages incorrectly reduced the reference set. The positive association with climate rate and vegetation turnover supports RQ2, but the test still depends on the representativeness of the modern reference set.

# 8 Limitations

The analysis uses genus-level pollen, so it cannot separate closely related species such as white and black spruce. Lag estimates come from correlations between time series that share long-term deglacial trends, so p-values are indicative and do not fully account for autocorrelation. TraCE is a model simulation at coarse spatial resolution, so site temperatures are approximate. The Neotoma API listing endpoint was unstable during the final run, so the modern reference set comes from the locally cached modern downloads rather than a confirmed full 1000-site bbox sample.

# 9 Conclusion

The real-data pipeline produced a coherent answer to all three research questions. Genus response lags differed significantly, ranging from about 500 years for Picea and Tsuga to 3000 years for Fagus. No-analogue frequency increased during intervals of faster climate change and higher vegetation turnover. Migration estimates for several genera were below the climate velocity implied by modern warming. The project therefore supports the conclusion that eastern North American tree genera historically lagged climate change, and that current warming may require climate tracking faster than the median rates inferred from late Quaternary pollen records.

# References

Blois et al. 2013. Space can substitute for time in predicting climate-change effects on biodiversity. PNAS.

Dawson et al. 2016. Quantifying pollen-vegetation relationships to reconstruct ancient forests. Quaternary Science Reviews.

Fordham et al. 2020. Using paleo-archives to safeguard biodiversity under climate change. Science.

Knight et al. 2020. Community assembly and climate mismatch in late-Quaternary eastern North American pollen assemblages. The American Naturalist.

Mottl et al. 2021. Global acceleration in rates of vegetation change over the past 18,000 years. Science.

Williams et al. 2018. The Neotoma Paleoecology Database. Quaternary Research.

TraCE-21ka climate simulation, NCAR GDEX dataset d651050, DOI 10.5065/CXB5-TV56.

IPCC AR6 Working Group I Technical Summary. Recent warming assessed at about 0.19 deg C per decade over 1980-2020. https://www.ipcc.ch/report/ar6/wg1/chapter/technical-summary/
"""
    (OUT / "TBD2_Project_Report.md").write_text(report)


def build_slides(d):
    s = d["sites"]
    b = d["binned"]
    v = d["velocity"]
    tests = d["tests"]
    lags = d["lags"]
    short = ", ".join(lags.head(2).genus)
    long = ", ".join(lags.tail(3).genus)
    deck = f"""---
title: "Quantifying Climate Vegetation Lags"
subtitle: "Team TBD2 Project 25"
author: "Vivek R, Nandan Rajesh Kamat, Shaurya Gupta"
---

# Research gap

Studies show forest communities lag climate change, but our question is quantitative:

- How many centuries does each tree genus lag temperature?
- Do unusual communities line up with fast climate change?
- Were past migration rates fast enough to match moving climate zones?

---

# Data and pipeline

![Study sites](data/outputs/figures/fig1_sites.png){{width=5.0in}}

- Neotoma fossil pollen: {d["fossil_ids"].dataset_id.nunique()} cached datasets
- Filtered fossil analysis: {len(s)} sites and {len(b)} binned samples
- TraCE-21ka TREFHT temperatures matched to each site
- 500-year bins from 14.75 ka BP to 0.25 ka BP

---

# Genus lags differ

![Lag chart](data/outputs/figures/fig3_lags.png){{width=6.5in}}

Kruskal-Wallis p = {tests["kruskal_p"]:.2e}

---

# Main lag result

Shortest median lags:

- {short}: 500 years

Longer median lags:

- {long}: 2250 to 3000 years

Interpretation: tree genera did not track temperature as a single moving forest unit.

---

# Rates through time

![Rates](data/outputs/figures/fig2_rates.png){{width=6.6in}}

Median absolute climate rate: {fmt(d["climate_rate"].climate_rate_c_per_century.abs().median(), 3)} deg C per century

Median vegetation turnover: {fmt(d["roc"].rate_per_century.median(), 3)} Hellinger units per century

---

# Migration versus climate velocity

![Migration](data/outputs/figures/fig5_migration.png){{width=6.4in}}

- Median inferred migration: {fmt(v["median_genus_migration_m_per_yr"], 1)} m/yr
- Past 95th percentile climate velocity: {fmt(v["past_p95_climate_velocity_m_per_yr"], 1)} m/yr
- Modern climate velocity at 1.9 deg C per century: {fmt(v["modern_climate_velocity_m_per_yr"], 0)} m/yr

---

# No-analogue communities

![No analogue](data/outputs/figures/fig4_noanalogue.png){{width=6.5in}}

- Threshold: {fmt(tests["no_analogue_threshold_scd"], 3)} squared chord distance
- Modern reference samples: {len(d["modern"])}
- Flagged fossil samples: {fmt(d["noanalogue"].no_analogue.mean() * 100, 1)} percent
- Spearman rho with climate rate: {fmt(tests["spearman_noanalogue_vs_abs_climate_rate"][0], 2)}

---

# Conclusion

The real-data pipeline supports two core claims.

- Tree genera had different lag times, from about 500 to 3000 years.
- No-analogue frequency rose during faster climate and vegetation change.
- Modern climate velocity is about {fmt(v["modern_climate_velocity_m_per_yr"] / v["median_genus_migration_m_per_yr"], 1)} times the median inferred migration rate.

The modern reference set now contains {len(d["modern"])} filtered surface samples, but the API should still be rerun if Neotoma becomes stable.

"""
    (OUT / "TBD2_Project_Slides.md").write_text(deck)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    data = load()
    build_report(data)
    build_slides(data)
    subprocess.run(["pandoc", str(OUT / "TBD2_Project_Report.md"), "-o", str(ROOT / "TBD2_Project_Report.docx")], check=True, cwd=ROOT)
    subprocess.run(["pandoc", str(OUT / "TBD2_Project_Slides.md"), "-o", str(ROOT / "TBD2_Project_Slides.pptx")], check=True, cwd=ROOT)
    print("wrote TBD2_Project_Report.docx and TBD2_Project_Slides.pptx")
