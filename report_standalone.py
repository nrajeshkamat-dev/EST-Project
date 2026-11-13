"""Builds the Standalone Single-Study Final Report (DOCX + native PDF via Word COM)."""
import json
import numpy as np
import pandas as pd
import docx
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import config as C
from report_paper import (
    NAVY,
    SLATE,
    _configure_doc,
    _h,
    _p,
    _bullet,
    _callout,
    _add_table,
    _add_single_fig,
    _export_pdf,
)


def _load_standalone_metrics():
    return {
        "sites_base": pd.read_csv(C.PROC / "sites.csv"),
        "sites": pd.read_csv(C.PROC / "sites_final_2d.csv"),
        "creg": pd.read_csv(C.PROC / "climate_regional.csv").sort_values("bin_age"),
        "cr": pd.read_csv(C.OUT / "climate_rate_final_2d.csv").sort_values("bin_age"),
        "ls": pd.read_csv(C.OUT / "lag_summary_final_2d.csv"),
        "ls_250": pd.read_csv(C.OUT / "lag_summary_bin250.csv"),
        "lags": pd.read_csv(C.OUT / "lags_final_2d.csv"),
        "na": pd.read_csv(C.OUT / "noanalogue_vs_climate_final_2d.csv").sort_values("bin_age"),
        "drv": pd.read_csv(C.OUT / "no_analogue_drivers_final_2d.csv").sort_values("bin_age"),
        "roc": pd.read_csv(C.OUT / "rate_of_change_final_2d.csv"),
        "mig": pd.read_csv(C.OUT / "migration_final_2d.csv"),
        "tests": json.loads((C.OUT / "tests_final_2d.json").read_text()),
        "vel": json.loads((C.OUT / "velocity_comparison_final_2d.json").read_text()),
        "ens": json.loads((C.OUT / "ensemble_summary_legacyage.json").read_text()),
        "audit_fin": json.loads((C.STAGE_LOGS / "audit_final_2d.json").read_text()),
        "audit_250": json.loads((C.STAGE_LOGS / "audit_bin250.json").read_text()),
    }


def build_standalone_report_docx_and_pdf():
    m = _load_standalone_metrics()
    doc = docx.Document()
    _configure_doc(doc)

    fig_dir = C.OUT / "figures_standalone"
    creg = m["creg"]
    vel = m["vel"]
    tests = m["tests"]
    ens = m["ens"]
    ls = m["ls"]
    na = m["na"]
    roc_bin = m["roc"].groupby("bin_age").rate_per_century.median()

    n_sig_pairs = int((m["lags"].p_ebisuzaki < 0.05).sum())
    n_pos_sig = int(((m["lags"].p_ebisuzaki < 0.05) & (m["lags"].r >= 0)).sum())
    n_neg_sig = int(((m["lags"].p_ebisuzaki < 0.05) & (m["lags"].r < 0)).sum())
    eb_rate = n_sig_pairs / len(m["lags"]) * 100.0
    na500 = float(na.loc[na.bin_age == 500, "frac_no_analogue"].iloc[0]) * 100.0
    na_peak = float(na.frac_no_analogue.max()) * 100.0
    na_peak_ka = float(na.loc[na.frac_no_analogue.idxmax(), "bin_age"]) / 1000.0
    mig2d_med = vel.get("median_genus_migration_2d_m_per_yr") or vel["median_genus_migration_m_per_yr"]
    deficit_x = vel["modern_climate_velocity_m_per_yr"] / mig2d_med

    # --- Title Block ---
    tp = doc.add_paragraph()
    tp.paragraph_format.space_before = Pt(4)
    tp.paragraph_format.space_after = Pt(3)
    tr = tp.add_run("How Fast Can Eastern North American Forests Track Climate Change? Fifteen Millennia of Pollen Evidence")
    tr.bold = True
    tr.font.size = Pt(17)
    tr.font.color.rgb = NAVY

    sub = doc.add_paragraph()
    sub.paragraph_format.space_after = Pt(2)
    sr = sub.add_run("Late-Quaternary Climate–Vegetation Lags, No-Analogue Forest Attribution, and 2D Spatial Tree Migration")
    sr.italic = True
    sr.font.size = Pt(11)
    sr.font.color.rgb = SLATE

    auth = doc.add_paragraph()
    auth.paragraph_format.space_after = Pt(8)
    auth.add_run("Team TBD2 (Project 25)  ·  Environmental Science & Technology Synthesis  ·  Study Window: 15,000–0 yr BP").font.size = Pt(9.5)

    _callout(
        doc,
        "Plain-Language Abstract",
        f"Modern global warming is shifting climate zones rapidly, yet forestry studies lasting only a few years cannot reveal how whole tree populations respond across centuries. "
        f"In this study, we analyzed 15,000 years of fossil pollen from {len(m['sites'])} Eastern North American lake sediment cores (1,706 time bins alongside 611 quality-filtered modern lake samples) paired with TraCE-21ka climate simulations. "
        f"Our experimental design isolated woody tree and shrub pollen (excluding post-settlement farm weeds), calibrated counts using Relative Pollen Productivity (REVEALS RPP) factors, anchored ages to LegacyAge 1.0 Bayesian radiocarbon models (57 direct matches, 12 Neotoma fallbacks), controlled temporal autocorrelation using bin-to-bin first differences and 1,000 Ebisuzaki phase-randomized surrogates, and mapped postglacial spread on a 2D equal-area plane. "
        f"Three ecological conclusions emerge: (1) tree genera lag behind warming at distinct speeds (Kruskal–Wallis H = {tests['kruskal_H']:.2f}, p = {tests['kruskal_p']:.5f}), spanning pioneer Larix (750 yr) to shade-tolerant Fagus and Tsuga (2,500 yr); (2) late-glacial warming created genuinely novel no-analogue forests (peaking at {na_peak:.1f}% at {na_peak_ka:.1f} ka BP from co-occurring Quercus, Alnus, Betula, and Populus mixes, before falling to {na500:.1f}% by 500 BP), tightly linked to vegetation reorganization turnover (Ebisuzaki p = {tests['ebisuzaki_p_veg']:.3f}); and (3) even when diagonal 2D dispersal corridors around mountains and lakes are resolved, validated tree migration (median {mig2d_med:.1f} m/yr; Carya 277.0 m/yr ENE, Alnus 264.6 m/yr WNW) falls roughly {deficit_x:.1f}× slower than today's anthropogenic climate velocity ({vel['modern_climate_velocity_m_per_yr']:.0f} m/yr).",
    )

    # --- 1. Introduction ---
    _h(doc, "1. Introduction & Three Core Research Questions")
    _p(
        doc,
        "As Earth warms at roughly 0.19 °C per decade (1.9 °C/century), species must adapt in place, shift across the landscape, or suffer local decline. Because trees live for decades to centuries, field observations spanning only a few years miss slow population turnover. Lake-mud sediment cores solve that gap: layers deposited since the last Ice Age trap fossil pollen grain by grain across 15,000 years of massive natural warming.",
    )
    _p(doc, "We designed one unified empirical pipeline across Eastern North America (34°–52° N, -100° to -60° E) to answer three linked questions:")
    _bullet(doc, "RQ1 — Unequal Climate Lags: ", "Do different tree genera adjust to abrupt temperature and moisture shifts at the same speed, or do biological traits split fast pioneers from slow shade-tolerant canopy trees?")
    _bullet(doc, "RQ2 — Alien ('No-Analogue') Forests: ", "Did rapid Ice Age climate transitions scramble tree species into forest combinations with no modern counterpart, and which exact taxa created that novelty?")
    _bullet(doc, "RQ3 — Two-Dimensional Migration vs. Modern Warming: ", "Along which real geographic corridors did trees spread after glacial retreat, how fast did they travel, and does natural dispersal velocity keep pace with contemporary climate change?")

    # --- 2. Study Area & Data ---
    _h(doc, "2. Study Corridor & Primary Datasets")
    _p(
        doc,
        "Our experiment combines four open paleoclimate and paleoecological archives covering the transition from glacial ice retreat (~15,000 years ago) through the Holocene warm period to pre-industrial times (0 yr BP):",
    )
    _bullet(doc, "Neotoma Paleoecology Database (Fossil Cores): ", f"We extracted 423 pollen datasets across North America, filtering to {m['audit_fin']['fossil_audit']['inside_bbox_datasets']} sites inside Eastern North America (-100° to -60° E, 34° to 52° N) spanning {m['audit_fin']['fossil_audit']['raw_rows']:,} raw pollen datum rows.")
    _bullet(doc, "Modern Surface Analogues (Neotoma Modern): ", f"We compiled {m['audit_fin']['modern_audit']['inside_bbox_datasets']} modern surface sediment and moss samples inside the corridor (611 meeting quality thresholds) to serve as today's baseline yardstick of forest composition.")
    _bullet(doc, "LegacyAge 1.0 Harmonized Chronologies (Li et al., 2022): ", f"Radiocarbon depth-age calibrations from PANGAEA Table-S5 (55,821 depth-age rows across 14,000+ calibrated years) matched directly to {ens['matched_inside_bbox_datasets']} of {ens['total_inside_bbox_datasets']} regional datasets ({ens['matched_sites']} of {ens['total_sites']} final retained cores), with depth-scaled age uncertainty for the remaining {ens['total_sites']-ens['matched_sites']} Neotoma sites.")
    _bullet(doc, "TraCE-21ka Transient Climate Simulation (NCAR): ", f"Annual mean surface air temperature (TREFHT, converted cleanly from Kelvin to °C: {creg.temp_c.min():.2f} to +{creg.temp_c.max():.2f} °C) and annual precipitation (PRECT: {creg.precip_mm_day.min():.2f}–{creg.precip_mm_day.max():.2f} mm/day, mean {creg.precip_mm_day.mean():.3f} mm/day), extracted directly at each lake's grid cell in 500-year windows.")

    # --- 3. Methodology & Experimental Design ---
    _h(doc, "3. Methodology & Experimental Design")
    _p(
        doc,
        "Fossil pollen records reflect complex physical and biological filters—some species broadcast huge clouds of wind-borne pollen, post-colonial farming adds invasive herbs to modern lakes, and smooth 15,000-year climate trends can create fake statistical correlations. We structured our experimental workflow into six tightly controlled analytical stages designed specifically to prevent those pitfalls:",
    )

    _h(doc, "3.1 Woody-Taxa Isolation (TRSH-Only Filtering) & Temporal Binning", level=2)
    _p(
        doc,
        "Post-settlement forest clearing and agriculture flooded modern lake mud with upland herb and ragweed pollen ('UPHE'), which can skew compositional comparisons with pre-industrial tree canopies. We therefore restricted our pollen sum strictly to woody arboreal trees and shrubs ('TRSH', spanning 14 dominant Eastern North American tree genera plus minor woody taxa grouped into 'Other') BEFORE applying our minimum sample quality screen of ≥100 counted woody grains. Samples with fewer than 100 woody grains were discarded (removing 4 herb-dominated western prairie and coastal margin cores), and remaining samples were binned into uniform 500-year intervals (14,750 to 250 yr BP). Cores were required to span at least 12 occupied bins with no interior hiatus longer than 4 bins (2,000 yr), yielding 69 continuous lake records across 1,706 bins.",
    )

    _h(doc, "3.2 Relative Pollen Productivity (REVEALS RPP) Calibration", level=2)
    _p(
        doc,
        "Raw pollen percentages misrepresent real forest biomass because wind-pollinated species like Pinus shed vastly more pollen per tree than insect-pollinated species like Acer. Following the REVEALS framework (Sugita, 2007) and Northern Hemisphere consensus productivity syntheses (Wieczorek & Herzschuh, 2020; Dawson et al., 2016), we divided each taxon's grain count by its empirical RPP factor prior to computing proportions (e.g., Pinus ÷ 14.10, Abies ÷ 6.88, Betula ÷ 6.19, Picea ÷ 2.80, vs. Acer ÷ 0.23; Table 1). Thus, high pollen producers no longer drown out ecologically dominant but quiet canopy hardwoods.",
    )

    _h(doc, "3.3 Bayesian Chronologies & Age-Uncertainty Ensemble Design", level=2)
    _p(
        doc,
        "Mixing uncalibrated radiocarbon dates blurs abrupt events like the Younger Dryas across cores. We assigned every core its harmonized LegacyAge 1.0 Bayesian median age (IntCal20) whenever available (57/69 cores) and used depth-interpolated Neotoma age models with empirical uncertainty bounds for the remaining 12 cores. To prove that conclusions do not depend on single age-model estimates, we also built a 50-member Monte Carlo ensemble resampling calibrated ages across depth uncertainty distributions and tested temporal resolution sensitivity using 250-year bins across 57 high-density cores (2,342 bins).",
    )

    _h(doc, "3.4 Stationary Cross-Correlation & Ebisuzaki Autocorrelation Control (RQ1)", level=2)
    _p(
        doc,
        "Because both temperature and tree abundances trend steadily over 15,000 years, correlating raw curves produces inflated significance between unrelated series. To measure genuine time lags honestly, we first-differenced every regularized lake pollen series and local TraCE temperature series (bin-to-bin ΔPollen vs. ΔTemp) while keeping interior chronological gaps strictly as NaN. For each core and genus with ≥12 overlapping steps and variance >0, we tested lags k ∈ [0, 3,000 yr] in 500-year steps, selecting the lag maximizing |r(k)| so that both positive warm-tracking expansions (+r) and negative cold-tracking retreats (-r) are detected symmetrically. Every site-genus correlation was tested against 1,000 Ebisuzaki (1997) FFT phase-randomized surrogates that scramble exact event timing while preserving autocorrelation memory. Across-genus lag differences were evaluated with non-parametric Kruskal–Wallis tests and Bonferroni post-hoc comparisons, and replicated against TraCE precipitation (ΔPrecip) to verify whether thermal or moisture forcing paced communities.",
    )

    _h(doc, "3.5 No-Analogue Squared Chord Distance (SCD) & Taxon Attribution (RQ2)", level=2)
    _p(
        doc,
        "For every fossil bin i, we calculated its minimum Squared Chord Distance (SCD) against all 611 quality-filtered modern surface pollen assemblages j: SCD_ij = Σ_t (√p_it − √q_jt)². Because SCD sums squared differences additively across taxa t, decomposing the nearest-analogue SCD immediately quantifies how much each individual genus contributes to community novelty. Following Williams et al. (2004), samples exceeding the 5th percentile of within-modern pairwise SCD distances (threshold = {tests['no_analogue_threshold_scd']:.4f}) were classified as non-analogue. We paired bin-level no-analogue fractions against climate speed (|dTemp/dt|) and Hellinger vegetation turnover rate using Spearman rank correlation and 1,000-surrogate Ebisuzaki tests.",
    )

    _h(doc, "3.6 2D Equal-Area Migration Isochrones & Climate Velocity Comparison (RQ3)", level=2)
    _p(
        doc,
        "Postglacial migration rarely followed straight North meridians because the Appalachian Mountains and the Great Lakes deflected tree expansion diagonally. We defined local arrival age at each site as the oldest 500-yr bin where a genus first reached and maintained ≥20% of its site peak abundance. Site coordinates were projected onto a local equal-area tangent plane (kilometers centered on core centroids). For every genus with ≥8 qualifying arrivals, we first ran a planar 2D F-test (arrival_age ~ x_km + y_km): only genera passing spatial coherence at p_2d ≤ 0.05 advanced to surface mapping. For validated migrants, we fit smooth thin-plate splines (RBFInterpolator, clipped strictly inside each genus's observed Delaunay convex hull to prevent border extrapolation) and extracted grid spatial speeds 1 / |∇age| (median and IQR in m/yr) alongside vector mean azimuths (0° = North, 90° = East). Finally, migration speeds were benchmarked against past 95th-percentile climate velocity and modern warming velocity (1.9 °C/century divided by the regional spatial temperature gradient, -0.01207 °C/km).",
    )

    p1_rows = [
        {"Category": "Spatial & Temporal Domain", "Experimental Setting": "(-100°, 34° N, -60°, 52° N) · 15,000–0 yr BP", "Rationale / Empirical Basis": "Covers deglacial corridor in 500-yr bins (min 12 bins, max 4-bin gap); 69 cores, 1,706 bins."},
        {"Category": "Taxonomic Scope", "Experimental Setting": "TRSH woody taxa only (≥100 grains/sample)", "Rationale / Empirical Basis": "Removes modern post-settlement UPHE farm herbs; evaluates 14 tree genera + minor woody 'Other'."},
        {"Category": "REVEALS RPP Divisors", "Experimental Setting": "Pinus 14.10 · Abies 6.88 · Betula 6.19 · Picea 2.80 · Alnus 2.70 · Fraxinus 2.42 · Fagus 2.35 · Ulmus 2.24 · Quercus 2.08 · Tsuga 1.60 · Larix 1.24 · Carya 1.00 · Populus 0.67 · Acer 0.23", "Rationale / Empirical Basis": "Normalizes pollen over- vs. under-production using Wieczorek & Herzschuh (2020) and Dawson et al. (2016)."},
        {"Category": "Chronology Calibration", "Experimental Setting": "LegacyAge 1.0 (57/69 direct) + 12 fallback + N=50 ensemble", "Rationale / Empirical Basis": "IntCal20 harmonized Bayesian depth-age models (Li et al., 2022) + radiocarbon jitter stress check."},
        {"Category": "Climate & Modern Velocity", "Experimental Setting": "TraCE Annual TREFHT (°C) & PRECT (mm/day); 1.9 °C/century modern", "Rationale / Empirical Basis": "Spatial gradient -0.01207 °C/km -> modern climate-zone velocity 1,573.8 m/yr."},
        {"Category": "RQ1–RQ3 Hypothesis Gates", "Experimental Setting": "ΔPollen vs ΔTemp; Ebisuzaki N=1,000; SCD p05; 2D planar F-test (p≤0.05)", "Rationale / Empirical Basis": "Prevents trend-correlation false positives, identifies SCD taxa drivers, and isolates valid 2D expansion waves."},
    ]
    _add_table(doc, pd.DataFrame(p1_rows), "Table 1. Summary of experimental design parameters, REVEALS RPP calibration weights, and statistical significance controls.")

    # --- 4. Results & Visual Inferences ---
    _h(doc, "4. Results & Detailed Inferences Across All Visualizations")
    _p(
        doc,
        "Below we present all six static publication figures and explain why each visual form was selected, alongside complete quantitative findings and links to the four interactive offline HTML charts.",
    )

    _h(doc, "4.1 Spatial Sampling Network & Chronological Coverage (Figure 1)", level=2)
    _add_single_fig(
        doc,
        fig_dir / "fig1_study_sites.png",
        "Figure 1. Eastern North America study network (69 retained cores, 1,706 bins) showing LegacyAge 1.0 cores (blue, n=57), Neotoma fallback cores (amber, n=12), and excluded low-tree cores (red ×, n=4).",
        width_in=5.6,
    )
    _p(doc, "Mapping retained and excluded cores on an Equal-Area-proportioned Natural Earth basemap alongside Great Lakes coastlines makes regional sampling density and chronology source coverage immediately transparent.", bold_prefix="Why this visualization was chosen: ")
    _p(doc, "Only 4 of 73 candidate cores fell below the 100-grain woody pollen threshold—all situated on open western grasslands or marginal Atlantic fringes. Across the remaining 69 forest cores, 57 (82.6%) rest on upgraded LegacyAge 1.0 Bayesian chronologies evenly spanning the Midwest, Great Lakes (n = 44 cores ≥42° N), New England, and the Southeast (n = 25 cores <42° N). Active sample coverage starts at 37 cores (54%) at 14.75 ka BP and rises above 55 cores across nearly the entire Holocene.", bold_prefix="Detailed Inferences: ")

    _h(doc, "4.2 Regional Climate Trajectory, Moisture & Community Turnover (Figure 2)", level=2)
    _add_single_fig(
        doc,
        fig_dir / "fig2_climate_and_turnover.png",
        "Figure 2. TraCE-21ka regional temperature (°C) and precipitation (mm/day), thermal warming rate (°C/century), and median Hellinger community turnover (± IQR ribbon) across abrupt climate events.",
    )
    _p(doc, "Aligning mean temperature, rainfall, warming rate, and vegetation turnover vertically across a shared 15 → 0 ka BP timeline reveals cause-and-effect timing across abrupt climate transitions without splitting eyes across separate charts.", bold_prefix="Why this visualization was chosen: ")
    _p(doc, f"Top panel: Regional temperature climbs rapidly from -10.27 °C toward -3.3 °C across the Bølling–Allerød (14.7–12.9 ka), pauses across the Younger Dryas cold snap (12.9–11.7 ka), and reaches modern stability near +5.0 to +5.26 °C by 6.0 ka. Notably, dashed blue rainfall (PRECT) lags warming—staying relatively dry (2.22–2.24 mm/day) until after 11.7 ka before rising smoothly toward 2.49 mm/day in mid-Holocene. Middle & bottom panels: Warming rate spikes twice past 0.40 °C/century (14.5–13.5 ka and the 12.0 ka exit from the Younger Dryas, 0.401 °C/century), plus a smaller 0.21 °C/century pulse near 8.0 ka, before settling at a quiet Holocene median of 0.023 °C/century (≤8 ka). Median forest turnover peaks sharply right on the 12.0 ka warming burst at {roc_bin.max():.4f} Hellinger/century (overall study median {roc_bin.median():.4f}) and remains calm (~0.020–0.029) throughout the late Holocene.", bold_prefix="Detailed Inferences: ")

    _h(doc, "4.3 Genus-Level Stationary Lags, Polarity & Ecological Guilds (RQ1: Figure 3)", level=2)
    _add_single_fig(
        doc,
        fig_dir / "fig3_genus_lags_raincloud.png",
        "Figure 3. Two-panel synthesis of postglacial forest lag dynamics: (A) Response delay (Median ± 95% bootstrap CI) across three ecological speed tiers, paired with (B) 100% horizontal stacked bars showing fossil site response polarity (% cores cold-retreating −r vs. warm-expanding +r, with filled segments denoting Ebisuzaki p < 0.05 significance).",
    )
    _p(doc, "A single distribution or bar obscures whether trees expanded or collapsed during warming. A dual-panel linked layout resolves this: Panel A reveals the response clock (median lag ± 95% CI across fast pioneer, canopy reorganization, and late climax stages), while Panel B displays the biological reaction (100% horizontal stacked bar of cold-retreating -r vs. warm-expanding +r sites, with verified Ebisuzaki autocorrelation significance). This separates response delay from response direction, making continental forest reorganizations intuitive at a glance.", bold_prefix="Why this visualization was chosen: ")
    _p(doc, f"After removing 15,000-year shared trends via first-differencing, {n_sig_pairs} of {len(m['lags'])} core-genus series ({eb_rate:.1f}%: {n_pos_sig} warm-tracking +r and {n_neg_sig} cold-tracking −r) survive strict 1,000-surrogate Ebisuzaki testing (p < 0.05), confirming genuine lagged responses rather than coincidental trends. Cross-genus lag timing differs significantly (Kruskal–Wallis H = {tests['kruskal_H']:.2f}, p = {tests['kruskal_p']:.5f}; pairwise Bonferroni Picea vs. Tsuga p = 0.0127, Picea vs. Fagus p = 0.0462). Panel A reveals three distinct ecological speed tiers: pioneer conifer Larix leads with the shortest median lag (750 yr, 80.0% sig), nine canopy reorganization taxa cluster at 1,500 yr, and shade-tolerant climax dominants Fagus and Tsuga trail slowest at 2,500 yr. Crucially, Panel B demonstrates why the 1,500-year cluster is not ecologically uniform: while cold-boreal Picea underwent severe collapse (94.9% negative −r retreat correlations, mean r = -0.637, 78.0% sig) and Fraxinus retreated (68.8% −r), temperate hardwoods expanded aggressively into the newly opened canopy space (Quercus 79.1% +r with 41.8% sig; Acer 67.2% +r with 31.2% sig; Ulmus 63.6% +r). Climax trees Fagus (71.9% +r) and Tsuga (64.7% +r) show lower jump-by-jump significance (15.6%–23.5% sig) because animal dispersal and soil maturation unfold gradually over millennia. Running the identical detrended test against TraCE precipitation (ΔPrecip) yielded much weaker genus separation (Kruskal p = {tests['precip_kruskal_p']:.3f}; {tests['precip_ebisuzaki_pass_rate_p05']*100:.1f}% sig), confirming temperature as the primary continental pacemaker.", bold_prefix="Detailed Inferences: ")

    lag_tbl = ls[["genus", "n_sites", "n_sig_05", "pct_sig_05", "median_lag_yr", "ci_low", "ci_high", "frac_pos_r", "mean_r"]].copy()
    lag_tbl.columns = ["Genus", "Sites", "Sig (p<0.05)", "Sig (%)", "Median Lag (yr)", "CI Low", "CI High", "+r (%)", "Mean r"]
    lag_tbl["Sig (%)"] = (lag_tbl["Sig (%)"] * 100).round(1)
    lag_tbl["+r (%)"] = (lag_tbl["+r (%)"] * 100).round(1)
    _add_table(doc, lag_tbl.sort_values(["Median Lag (yr)", "Genus"]), "Table 2. Stationary first-differenced lag statistics, Ebisuzaki pass rates (p < 0.05), and correlation polarity across 13 genera.")

    _h(doc, "4.4 No-Analogue Forests & Per-Taxon SCD Drivers (RQ2: Figure 4)", level=2)
    _add_single_fig(
        doc,
        fig_dir / "fig4_noanalogue_drivers.png",
        "Figure 4. Top: No-analogue forest prevalence (%) vs. absolute temperature rate (°C/century). Bottom: Mean Squared Chord Distance (SCD) contribution by top taxonomic drivers across 15 → 0 ka BP.",
    )
    _p(doc, "Pairing the continental no-analogue percentage curve directly above a Taxon × Time SCD heat matrix links WHEN alien forests occurred (Top) with WHICH exact tree genera mathematically created those unfamiliar pollen mixtures (Bottom).", bold_prefix="Why this visualization was chosen: ")
    _p(doc, f"Top panel: Using the modern 5th-percentile SCD threshold ({tests['no_analogue_threshold_scd']:.4f}), no-analogue forests dominate late-glacial Eastern North America—peaking at {na_peak:.1f}% at {na_peak_ka:.1f} ka BP and holding near 69%–79% through the Younger Dryas—before declining smoothly through early Holocene and reaching just {na500:.1f}% by 500 BP (validating that pre-colonial late-Holocene forests closely matched modern tree assemblages once farm weeds are excluded). Bottom heatmap: Between 14.75 and 12.0 ka, deep crimson cells show that Quercus (mean deglacial SCD 0.0192), Alnus (0.0164), Betula (0.0161), Populus (0.0139), Pinus (0.0136), and Acer (0.0118) co-occurred at mixes rarely seen together in modern separated boreal vs. temperate biomes. After 8.0 ka, almost every taxon fades into pale yellow (≤0.006), leaving only modest mid-Holocene Fagus novelty (0.0085). Statistically, no-analogue prevalence correlates strongly with both |climate rate| (Spearman rho = {tests['spearman_noanalogue_vs_abs_climate_rate'][0]:.3f}, raw p = {tests['spearman_noanalogue_vs_abs_climate_rate'][1]:.2e}) and community turnover (rho = {tests['spearman_noanalogue_vs_veg_rate'][0]:.3f}, raw p = {tests['spearman_noanalogue_vs_veg_rate'][1]:.2e}); under strict 1,000-surrogate Ebisuzaki testing, vegetation turnover stays significant (p = {tests['ebisuzaki_p_veg']:.3f}) while thermal rate softens to p = {tests['ebisuzaki_p_climate']:.4f}, showing that active community reorganization directly sustains non-analogue mixtures.", bold_prefix="Detailed Inferences: ")

    _h(doc, "4.5 2D Migration Corridors & Modern Velocity Deficit (RQ3: Figures 5 & 6)", level=2)
    _add_single_fig(
        doc,
        fig_dir / "fig5_migration_isochrones.png",
        "Figure 5. Postglacial 2D arrival age isochrones (ka BP) and local migration azimuth vectors across the five genera passing the 2D planar F-test (p_2d ≤ 0.05), clipped strictly to observed convex hulls.",
    )
    _p(doc, "Contour surfaces gated by a 2D planar significance test—clipped tightly to convex hulls of observed sites and annotated with local directional arrows—capture curved, diagonal colonization paths around the Appalachian Mountains and Great Lakes without hallucinating patterns onto non-migrating trees.", bold_prefix="Why Figure 5 was chosen: ")
    _p(doc, "Five genera exhibit spatially coherent postglacial migration waves (p_2d ≤ 0.05), revealing strikingly diverse geographic corridors:\n• Carya (hickory — 277.0 m/yr, IQR 267.7–287.1, azimuth 65.0° ENE, r²_2d = 0.344, p_2d = 4.15e-3): Spread vigorously East-Northeast from interior Mississippi/Ohio valley refugia along warm river valleys toward the Atlantic seaboard.\n• Alnus (alder — 264.6 m/yr, IQR 258.0–268.5, azimuth 308.2° WNW, r²_2d = 0.708, p_2d = 3.78e-7): Expanded in a tight diagonal West-Northwest corridor from New England across the St. Lawrence and Great Lakes into northern Minnesota.\n• Fagus (beech — 169.6 m/yr, IQR 166.2–175.8, azimuth 344.4° NNW, r²_2d = 0.354, p_2d = 9.15e-4) & Tsuga (hemlock — 116.9 m/yr, IQR 114.5–118.3, azimuth 344.3° NNW, r²_2d = 0.496, p_2d = 3.42e-5): Advanced along nearly parallel North-Northwest tracks (dark blue 12–10 ka refugia in the Mid-Atlantic/Appalachians reaching 6–4 ka green contours across Michigan, Ontario, and Maine).\n• Larix (tamarack — 124.0 m/yr, IQR 122.4–126.4, azimuth 1.2° N, r²_2d = 0.774, p_2d = 2.62e-3): Tracked retreating glacial ice almost straight due North across the Upper Midwest.\n• Remaining Genera: Seven taxa showed diffuse, multi-refugia, or already-present distributions (p_2d > 0.05; Pinus p_2d = 0.064, Quercus p_2d = 0.095) and were deliberately excluded from contouring.", bold_prefix="Detailed Inferences from Figure 5: ")

    _add_single_fig(
        doc,
        fig_dir / "fig6_velocity_deficit.png",
        "Figure 6. Log-scale comparison of validated 2D postglacial tree migration speeds showing medians (circles) and full 2D spatial surface ranges (whiskered bars, min–max) against past deglacial climate velocity (range 28–343 m/yr, p95 = 332 m/yr) and modern warming velocity (range 1,242–2,071 m/yr for 1.5–2.5 °C/century, central 1.9 °C = 1,574 m/yr).",
    )
    _p(doc, "A logarithmic speed axis keeps slow conifers (117 m/yr) and rapid modern warming (1,574 m/yr) both cleanly legible on the same scale, while explicitly displaying medians and full spatial surface ranges (min–max whiskers) across 2D arrival surfaces alongside climate velocity uncertainty bands.", bold_prefix="Why Figure 6 was chosen: ")
    _p(doc, f"Even after resolving fastest diagonal 2D corridors and evaluating local maximum speeds (Carya up to 296 m/yr [IQR 268–287], Alnus up to 278 m/yr [IQR 258–269], Fagus up to 185 m/yr [IQR 166–176], Larix up to 129 m/yr [IQR 122–126], and Tsuga up to 120 m/yr [IQR 115–118]), every tree genus migrated slower than past abrupt p95 deglacial climate velocity ({vel['past_p95_climate_velocity_m_per_yr']:.1f} m/yr). Across the five validated migrants, overall median tree spread is {mig2d_med:.1f} m/yr—falling roughly {deficit_x:.1f}× short of contemporary climate velocity ({vel['modern_climate_velocity_m_per_yr']:.1f} m/yr, computed from 1.9 °C/century warming divided by the {vel['spatial_gradient_c_per_km']:.5f} °C/km Eastern North American thermal gradient; modern range 1,242–2,071 m/yr for 1.5–2.5 °C/century).", bold_prefix="Detailed Inferences from Figure 6: ")

    mig_tbl = m["mig"][["genus", "n_sites", "r2_2d", "p_2d", "rate_2d_median_m_per_yr", "rate_2d_iqr_low", "rate_2d_iqr_high", "mean_azimuth_deg", "azimuth_conc"]].copy()
    mig_tbl.columns = ["Genus", "Sites", "2D R²", "2D p", "2D Med (m/yr)", "IQR Low", "IQR High", "Azimuth (°)", "Vector Conc."]
    mig_tbl = mig_tbl.sort_values(["2D Med (m/yr)", "2D p"], ascending=[False, True])
    _add_table(doc, mig_tbl, "Table 3. 2D planar F-test significance, equal-area migration speeds (median and IQR), and mean dispersal azimuths across tested genera.")

    _h(doc, "4.6 Interactive Offline HTML Explorer (TBD2_Project_Report_Standalone.html)", level=2)
    _p(
        doc,
        "Alongside Figures 1–6 embedded above, our companion offline browser dashboard (TBD2_Project_Report_Standalone.html) provides five interactive tabs hosting four Plotly charts and filterable tables: (1) Climate & Precipitation Dual-Axis Explorer showing °C temperature and mm/day rainfall across every 500-yr bin; (2) Stationary Genus Lag Chart displaying median lags and 95% confidence bars with Ebisuzaki significance counts; (3) No-Analogue & |Climate Rate| Overlay tracking 14.5 ka peak novelty down to 500 BP pre-colonial stability; and (4) Log-Scale 2D Migration Velocity Chart contrasting Carya, Alnus, Fagus, Larix, and Tsuga against 332 and 1,574 m/yr climate velocity lines.",
    )

    # --- 5. Discussion ---
    _h(doc, "5. Discussion: Ecological & Conservation Synthesis")
    _bullet(doc, "1. Taxon-Specific Inertia Governs Forest Reorganization (RQ1): ", "Consistent differences spanning pioneer Larix (750 yr) to canopy dominants Fagus and Tsuga (2,500 yr) confirm that forests do not march northward as intact biomes. Seed dispersal mode, shade tolerance, soil development, and cold-edge retreat (-r Picea vs. +r Quercus/Acer) generate multi-century compositional inertia.")
    _bullet(doc, "2. Novel Ice Age Forests Recombined Existing Genera Under Fast Turnover (RQ2): ", "Deglacial no-analogue assemblages (79.0% at 14.5 ka) emerged when oak, birch, alder, and poplar mixed under non-modern seasonal and moisture regimes (dry early-deglacial rainfall lagging temperature). Once climates stabilized and modern assemblages assembled, pre-colonial mismatch dropped to 8.0% at 500 BP.")
    _bullet(doc, "3. Natural Dispersal Cannot Keep Pace With 21st-Century Climate Velocity (RQ3): ", "Accounting for diagonal 2D corridors around the Appalachians and Great Lakes reveals vigorous directional migrations (Carya 277.0 m/yr ENE, Alnus 264.6 m/yr WNW), yet the 169.6 m/yr continental median remains ~9.3× slower than modern isotherm velocity (~1,574 m/yr). Modern habitat fragmentation makes unassisted natural tracking even less viable without targeted conservation corridors or assisted migration.")

    # --- 6. Experimental Validation, Limitations & Future Work ---
    _h(doc, "6. Experimental Validation, Limitations & Future Outlook")
    _bullet(doc, "Age-Uncertainty Monte Carlo Ensemble (N = 50): ", f"Resampling LegacyAge depth-age bounds 50 times kept the cross-genus median lag locked at {ens['ensemble_median_lag_yr']:.0f} yr (IQR {ens['ensemble_lag_iqr_yr']}), proving our lag hierarchy is insensitive to radiocarbon calibration noise.")
    _bullet(doc, "250-Year High-Resolution Binning Validation: ", f"Re-running preprocessing at double temporal resolution (250-yr bins across {m['audit_250']['sites_retained']} high-density lakes, {m['audit_250']['binned_rows']:,} bins; Table 4) shortened raw lag estimates slightly because narrower windows resolve earlier onset shifts, while keeping the exact pioneer-to-climax rank order intact (Larix/Picea/Populus 625–750 yr vs. Fagus/Tsuga 2,000 yr).")
    _bullet(doc, "Synthetic Planted-Truth Calibration Tests: ", "Benchmarking our pipeline on synthetic cores with planted stepped lags (250–2,500 yr), pure random-walk AR(1) nulls, TraCE precipitation series, and known 200 m/yr diagonal wavefronts recovered planted lags within ±500 yr, held random-walk false positives cleanly to 5.0% via Ebisuzaki phase randomization, and accurately recovered 2D migration speeds.")
    _bullet(doc, "Study Limitations: ", f"(1) {ens['total_sites']-ens['matched_sites']} of {ens['total_sites']} cores lacked direct LegacyAge 1.0 matches and rely on Neotoma fallback age models; (2) genus-level taxonomy blends ecologically distinct species (e.g., white vs. black spruce); (3) coarse TraCE climate grid cells smooth local topographic refugia; and (4) 500-year bin averages smooth sub-century ecological pulses.")
    _bullet(doc, "Future Directions: ", "Integrating Sporormiella dung fungal spores (Late-Pleistocene megafaunal collapse), sedimentary charcoal fire histories, and downscaled CMIP6 future climate projections will extend this synthesis directly into applied forest management.")

    val_tbl = m["ls"][["genus", "n_sites", "median_lag_yr"]].merge(
        m["ls_250"][["genus", "n_sites", "n_sig_05", "median_lag_yr"]],
        on="genus", suffixes=("_500", "_250"), how="inner"
    )
    val_tbl["ens_med"] = [ens["per_genus_lag_iqr_yr"][g]["median"] for g in val_tbl["genus"]]
    val_tbl["ens_iqr"] = [f"{ens['per_genus_lag_iqr_yr'][g]['q25']:.0f}–{ens['per_genus_lag_iqr_yr'][g]['q75']:.0f}" for g in val_tbl["genus"]]
    val_tbl = val_tbl[["genus", "n_sites_500", "median_lag_yr_500", "ens_med", "ens_iqr", "n_sites_250", "median_lag_yr_250"]]
    val_tbl.columns = ["Genus", "Sites (500-yr)", "Lag 500-yr (yr)", "Ens. Med (yr)", "Ens. IQR (yr)", "Sites (250-yr)", "Lag 250-yr (yr)"]
    _add_table(doc, val_tbl.sort_values(["Lag 500-yr (yr)", "Genus"]), "Table 4. Chronological sensitivity validation across LegacyAge N=50 ensemble draws and 250-year binning resolution.")

    # --- 7. References ---
    _h(doc, "7. References")
    refs = [
        "Blois, J. L., Williams, J. W., Fitzpatrick, M. C., Jackson, S. T., & Ferrier, S. (2013). Space can substitute for time in predicting climate-change effects on biodiversity. PNAS, 110(23), 9374–9379.",
        "Dawson, A., Paciorek, C. J., McLachlan, J. S., Goring, S., Williams, J. W., & Jackson, S. T. (2016). Quantifying pollen–vegetation relationships to reconstruct ancient forests using 19th-century forest composition and pollen data. Quaternary Science Reviews, 137, 156–175.",
        "Ebisuzaki, W. (1997). A method to estimate the statistical significance of a correlation when the data are serially correlated. Journal of Climate, 10(9), 2147–2153.",
        "Fordham, D. A., Jackson, S. T., Brown, S. C., Huntley, B., Brook, B. W., Dahl-Jensen, D., et al. (2020). Using paleo-archives to safeguard biodiversity under climate change. Science, 369(6507), eabc5654.",
        "Gill, J. L., Williams, J. W., Jackson, S. T., Lininger, K. B., & Robinson, G. S. (2009). Pleistocene megafaunal collapse, novel plant communities, and enhanced fire regimes in North America. Science, 326(5956), 1100–1103.",
        "Knight, C. A., Baskaran, A., Li, Y., et al. (2020). Community assembly and climate mismatch in late-Quaternary eastern North American pollen assemblages. The American Naturalist, 195(2), 184–200.",
        "Li, C., Cao, X., Tian, F., Dallmeyer, A., & Herzschuh, U. (2022). LegacyAge 1.0: harmonised chronologies for global late-Quaternary pollen records. Earth System Science Data, 14(3), 1331–1343.",
        "Marsicek, J., Shuman, B. N., Bartlein, P. J., Shafer, S. L., & Brewer, S. (2018). Reconciling divergent trends and millennial variations in Holocene temperatures. Nature, 554(7690), 92–96.",
        "Mottl, O., Flantua, S. G., Bhatta, K. P., Felde, V. A., Giesecke, T., Goring, S., et al. (2021). Global acceleration in rates of vegetation change over the past 18,000 years. Science, 372(6544), 860–864.",
        "Nolan, C., Overpeck, J. T., Allen, J. R., Anderson, P. M., Betancourt, J. L., Binney, H. A., et al. (2018). Past and future global transformation of terrestrial ecosystems under climate change. Science, 361(6405), 920–923.",
        "Shuman, B. N., & Marsicek, J. (2016). The structure of Holocene climate change in mid-latitude North America. Quaternary Science Reviews, 141, 38–51.",
        "Sugita, S. (2007). Theory of quantitative reconstruction of vegetation I: pollen from large sites REVEALS regional vegetation composition. The Holocene, 17(2), 229–241.",
        "Wieczorek, M., & Herzschuh, U. (2020). Compilation of relative pollen productivity (RPP) estimates and taxonomically harmonised pollen datasets for the Northern Hemisphere. Earth System Science Data, 12(4), 3515–3545.",
        "Williams, J. W., Shuman, B. N., Webb, T., Bartlein, P. J., & Leduc, P. L. (2004). Late-Quaternary vegetation dynamics in North America: scaling from taxa to biomes. Ecological Monographs, 74(2), 309–334.",
        "Williams, J. W., Grimm, E. C., Blois, J. L., et al. (2018). The Neotoma Paleoecology Database, a multiproxy, international, community-curated data resource. Quaternary Research, 89(1), 156–177.",
        "NCAR TraCE-21ka Simulation (Dataset d651050, DOI 10.5065/CXB5-TV56) & IPCC AR6 Working Group I Technical Summary (~0.19 °C/decade warming rate).",
    ]
    for ref in refs:
        p = doc.add_paragraph(ref, style="List Bullet")
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.line_spacing = 1.05
        for run in p.runs:
            run.font.size = Pt(8.5)

    out_docx = C.ROOT / "TBD2_Project_Report_Standalone.docx"
    out_pdf = C.ROOT / "TBD2_Project_Report_Standalone.pdf"
    doc.save(out_docx)
    print(f"[report] wrote {out_docx}")
    _export_pdf(out_docx, out_pdf)
    print(f"[report] wrote {out_pdf}")
    return out_docx, out_pdf

