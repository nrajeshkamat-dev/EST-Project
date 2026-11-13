# Eastern North American Late-Quaternary Forest Dynamics
## Climate Lags, No-Analogue Attribution & 2D Tree Migration (Final Project Draft)

An end-to-end, publication-grade paleoecological research pipeline investigating postglacial vegetation reorganization across eastern North America from the Last Glacial Maximum (15,000 BP) to pre-industrial modern times (500 BP).

---

### Core Research Questions & Key Findings
1. **RQ1 (Climate–Vegetation Lags):** How rapidly did arboreal taxa respond to deglacial climate warming?
   * *Finding:* Significant genus differentiation ($H = 34.6$, $p = 0.0003$). Response times follow three distinct ecological speed tiers: fast pioneer conifers (*Larix*, 750 yr), broadleaf canopy reorganization (1,500 yr), and slow climax seeders (*Fagus* and *Tsuga*, 2,000–2,500 yr). Polarity separates cold-retreating boreal collapse (*Picea*, 94.9% negative correlation, 78% Ebisuzaki-significant) from warm-expanding temperate hardwoods (*Quercus*, 79.1% positive correlation).
2. **RQ2 (No-Analogue Communities):** What drove novel community emergence during deglaciation?
   * *Finding:* Novel forest prevalence peaked at 38.2% during early deglaciation (14.5 ka BP) and collapsed to a 0.0% pre-colonial floor at 500 BP under TRSH-only woody taxon filtering. Novelty was predominantly driven by high co-occurrence of *Picea* (mean Squared Chord Distance contribution 0.161) and *Fraxinus* (0.057) under non-analogue thermal regimes.
3. **RQ3 (2D Tree Migration vs. Climate Velocity):** Did postglacial tree dispersal keep pace with climate shifts?
   * *Finding:* Five genera exhibited spatially coherent 2D planar dispersal fronts ($p \le 0.05$): *Carya* (277.0 m/yr, azimuth 65.0° ENE), *Alnus* (264.6 m/yr, 308.2° WNW), *Fagus* (169.6 m/yr, 344.4° NNW), *Larix* (124.0 m/yr, 1.2° N), and *Tsuga* (116.9 m/yr, 344.3° NNW). Across all validated migrants, overall median tree spread (169.6 m/yr) fell strictly below past deglacial climate velocity (p95 = 331.8 m/yr) and trails projected contemporary anthropogenic warming velocity (1,574 m/yr) by 9.3×.

---

### Methodological Framework
* **Fossil Pollen & Core Harmonization:** 69 continuous sediment cores (1,706 500-yr bins) across eastern North America (25°–50° N, 95°–65° W), calibrated using empirical REVEALS Relative Pollen Productivity (RPP; Wieczorek & Herzschuh 2020) and Bayesian chronologies from LegacyAge 1.0 (Li et al. 2022) with 50-member Monte Carlo depth-age ensembles.
* **Independent Paleoclimate:** TraCE-21ka decadal transient simulations (°C surface temperature and mm/day precipitation; NCAR GDEX d651050).
* **Stationary Lag Testing:** First-differenced detrended cross-correlation tested against 1,000 Ebisuzaki phase-randomized surrogate time series.
* **2D Planar Spatial Migration:** Equal-area Albers projected coordinates calculating directional arrival velocity ($1 / |\nabla \text{Age}|$) and dispersal azimuths clipped to observed convex hulls.

---

### Project Deliverables
* **Interactive Dashboard:** `TBD2_Project_Report_Standalone.html` (5 tabs, 12 embedded figures, 4 interactive Plotly charts, 100% offline bundle).
* **Manuscript Documents:** `TBD2_Project_Report_Standalone.pdf` (12 pages, publication-formatted) and `TBD2_Project_Report_Standalone.docx`.
* **Publication Figures (300 dpi):** `data/outputs/figures_standalone/`
  * `fig1_study_sites.png`: Study corridor and core distribution.
  * `fig2_climate_and_turnover.png`: TraCE climate, warming rate & turnover.
  * `fig3_genus_lags_raincloud.png`: Response timeline & polarity breakdown.
  * `fig4_noanalogue_drivers.png`: No-analogue trajectory & SCD driver heatmap.
  * `fig5_migration_isochrones.png`: 2D arrival age contours & azimuth vectors.
  * `fig6_velocity_deficit.png`: Migration velocity deficit vs climate speed.

---

### Reproducing Deliverables
```bash
# 1. Generate standalone figures (300 dpi)
python 05_visualizations_modern.py --mode standalone

# 2. Build standalone HTML dashboard, DOCX, and PDF reports
python 06_build_report.py --mode standalone

# 3. Verify report structure and DOM integrity
python 06_build_report.py --verify-only
```
