---
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

![Study sites](data/outputs/figures/fig1_sites.png){width=5.0in}

- Neotoma fossil pollen: 423 cached datasets
- Filtered fossil analysis: 72 sites and 1782 binned samples
- TraCE-21ka TREFHT temperatures matched to each site
- 500-year bins from 14.75 ka BP to 0.25 ka BP

---

# Genus lags differ

![Lag chart](data/outputs/figures/fig3_lags.png){width=6.5in}

Kruskal-Wallis p = 1.66e-08

---

# Main lag result

Shortest median lags:

- Picea, Tsuga: 500 years

Longer median lags:

- Pinus, Carya, Fagus: 2250 to 3000 years

Interpretation: tree genera did not track temperature as a single moving forest unit.

---

# Rates through time

![Rates](data/outputs/figures/fig2_rates.png){width=6.6in}

Median absolute climate rate: 0.034 deg C per century

Median vegetation turnover: 0.025 Hellinger units per century

---

# Migration versus climate velocity

![Migration](data/outputs/figures/fig5_migration.png){width=6.4in}

- Median inferred migration: 164.7 m/yr
- Past 95th percentile climate velocity: 331.8 m/yr
- Modern climate velocity at 1.9 deg C per century: 1572 m/yr

---

# No-analogue communities

![No analogue](data/outputs/figures/fig4_noanalogue.png){width=6.5in}

- Threshold: 0.066 squared chord distance
- Modern reference samples: 644
- Flagged fossil samples: 59.9 percent
- Spearman rho with climate rate: 0.66

---

# Conclusion

The real-data pipeline supports two core claims.

- Tree genera had different lag times, from about 500 to 3000 years.
- No-analogue frequency rose during faster climate and vegetation change.
- Modern climate velocity is about 9.5 times the median inferred migration rate.

The modern reference set now contains 644 filtered surface samples, but the API should still be rerun if Neotoma becomes stable.

