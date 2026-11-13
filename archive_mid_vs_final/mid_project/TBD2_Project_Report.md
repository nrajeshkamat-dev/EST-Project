---
title: "Quantifying Lags Between Climate Change and Tree Genus Response in Eastern North America Using Fossil Pollen"
author: "Team TBD2: Vivek R, Nandan Rajesh Kamat, Shaurya Gupta"
date: "7 October 2026"
---

# Abstract

We analysed fossil pollen records from the Neotoma Paleoecology Database together with TraCE-21ka simulated temperature to estimate how tree genera in eastern North America responded to late Quaternary climate change. The working dataset contains 423 fossil pollen datasets and 1240 modern surface pollen datasets cached locally from Neotoma. After filtering to the study region, pollen-sum threshold, temporal coverage, and gap criteria, the real-data analysis used 72 fossil pollen sites, 1782 binned fossil samples, and 644 modern reference samples. Genus-level lags differed strongly among taxa (Kruskal-Wallis p = 1.66e-08). Picea and Tsuga showed the shortest median lags, while Pinus, Carya, and Fagus had longer lags. No-analogue samples were common (59.9 percent of binned fossil samples), and their frequency was positively associated with absolute climate rate and vegetation turnover. Migration estimates were available only for genera with a significant northward arrival gradient. Their median inferred migration rate was 164.7 m/yr, far below the climate-zone velocity implied by recent warming at 1572 m/yr.

# 1 Introduction

Past forest responses provide a long-term test of whether plant communities can keep pace with climate change. Fossil pollen records show that eastern North American forests reorganised after the last glacial period, but the literature review for this project identified a remaining gap: studies often describe ecological lag and no-analogue communities, while fewer analyses directly compare taxon-level response speed with climate-change speed. This project addresses that gap using open pollen and climate datasets.

# 2 Research questions

1. How long do different tree genera lag behind temperature change?
2. Do no-analogue communities coincide with fast climate change and high vegetation turnover?
3. Were past genus migration rates fast enough to match the speed at which climate zones moved?

# 3 Data

The pollen data came from the Neotoma Paleoecology Database API v2.0 for a bounding box over eastern North America (longitude -100 to -60, latitude 34 to 52). The pipeline used fossil pollen records from 0 to 15 ka BP and modern pollen surface samples as the no-analogue reference set. Climate data came from the TraCE-21ka transient climate simulation, NCAR GDEX dataset d651050, using TREFHT decadal-average NetCDF files already placed in `data/raw/trace`.

| Dataset | Datasets or sites | Rows or samples | Use |
| --- | --- | --- | --- |
| Cached fossil pollen | 423 | 742,380 | Used for fossil assemblages |
| Cached modern pollen | 1240 | 24,148 | Reference set before filtering |
| Filtered fossil sites | 72 | 1,782 | Used in lag, turnover, and migration analyses |
| Filtered modern samples | 644 | 644 | Used for no-analogue threshold |

# 4 Methods

The preprocessing script grouped pollen taxa into 14 focal genera plus Other, converted counts to proportions, binned samples into 500-year intervals, removed samples with fewer than 100 grains, and retained sites with at least 12 occupied bins and no gap larger than four bins. The final site coordinates fell within the target study region, with latitude 34.17 to 49.76 and longitude -98.93 to -62.09.

TraCE temperatures were extracted at the nearest grid cell for each site. The script interpreted the TraCE time axis as `ka_neg`, with raw range -22.00 to 0.03 ka, and converted temperatures to deg C. The estimated north-south gradient used for climate velocity was 0.0121 deg C/km.

Vegetation turnover was measured as Hellinger distance per century between adjacent 500-year bins. Lag was estimated by shifting each genus time series by 0 to 6 bins and selecting the lag with the largest absolute correlation with site temperature. No-analogue status used squared chord distance to the nearest modern sample, with the threshold set to the 95th percentile of modern nearest-neighbour distances. Migration rate was estimated from the slope of arrival age against northward distance, where arrival required a genus proportion of at least 5 percent for two consecutive bins.

# 5 Results

![Fossil pollen sites used in the analysis](data/outputs/figures/fig1_sites.png){width=5.8in}

## 5.1 Climate and vegetation rates

Past climate rates averaged over 500-year bins had a median absolute rate of 0.034 deg C/century and a 95th percentile of 0.401 deg C/century. Median vegetation turnover was 0.025 Hellinger units per century, with a 95th percentile of 0.060.

![Climate rate and vegetation turnover](data/outputs/figures/fig2_rates.png){width=6.2in}

## 5.2 Genus lags

Genus-level lags differed significantly (Kruskal-Wallis H = 58.63, p = 1.66e-08). Picea and Tsuga had median lags of 500 years. Quercus and Betula had median lags of 1000 years. Pinus, Carya, and Fagus had longer median lags, reaching 2250 to 3000 years.

| Genus | Sites | Median lag yr | 95 percent bootstrap CI yr |
| --- | --- | --- | --- |
| Picea | 66 | 500 | 500 to 1000 |
| Tsuga | 31 | 500 | 0 to 1500 |
| Betula | 52 | 1000 | 500 to 2500 |
| Quercus | 70 | 1000 | 500 to 1500 |
| Acer | 20 | 1500 | 500 to 2250 |
| Fraxinus | 30 | 1500 | 1000 to 2000 |
| Ulmus | 31 | 1500 | 500 to 3000 |
| Abies | 5 | 2000 | 1500 to 3000 |
| Alnus | 28 | 2000 | 1250 to 2500 |
| Pinus | 72 | 2250 | 2000 to 2500 |
| Carya | 21 | 2500 | 1000 to 3000 |
| Fagus | 33 | 3000 | 2500 to 3000 |

![Median lag by genus](data/outputs/figures/fig3_lags.png){width=6.2in}

## 5.3 No-analogue communities

The no-analogue threshold was 0.066 squared chord distance units, estimated from 644 filtered modern surface samples. In the current real-data run, 59.9 percent of fossil binned samples exceeded the threshold. No-analogue frequency increased during intervals with faster climate change (Spearman rho = 0.66, p = 9.36e-05) and higher vegetation turnover (rho = 0.81, p = 1.11e-07). These p-values ignore temporal autocorrelation, so the correlations should be treated as indicative rather than definitive.

![No-analogue fraction and climate rate](data/outputs/figures/fig4_noanalogue.png){width=6.2in}

## 5.4 Migration rates and climate velocity

Five genera had significant northward arrival gradients in the base run: Abies, Tsuga, Quercus, Fagus, and Carya. Quercus had the fastest estimate at 284.5 m/yr, followed by Fagus at 218.3 m/yr. The median estimated genus migration rate was 164.7 m/yr.

| Genus | Arrival sites | Migration m/yr | 95 percent bootstrap CI m/yr | p |
| --- | --- | --- | --- | --- |
| Abies | 9 | 59.4 | 32.3 to 526.3 | 0.0107 |
| Pinus | 21 | NA | NA | 0.6205 |
| Tsuga | 27 | 108.5 | 75.5 to 143.0 | 0.0000 |
| Betula | 29 | NA | NA | 0.5509 |
| Quercus | 40 | 284.5 | 180.1 to 531.0 | 0.0001 |
| Fagus | 34 | 218.3 | 163.5 to 611.9 | 0.0003 |
| Fraxinus | 10 | NA | NA | 0.4848 |
| Ulmus | 24 | NA | NA | 0.9804 |
| Carya | 15 | 164.7 | 104.0 to 557.8 | 0.0196 |
| Acer | 14 | NA | NA | 0.5152 |
| Alnus | 26 | NA | NA | 0.1189 |

Past median climate velocity was 28.2 m/yr, and the 95th percentile was 331.8 m/yr. Using the IPCC AR6 assessed recent warming rate of about 0.19 deg C per decade, or 1.9 deg C per century, the modern climate-zone velocity is 1572 m/yr. This is roughly 9.5 times the median inferred migration rate.

![Migration rates compared with climate velocity](data/outputs/figures/fig5_migration.png){width=6.2in}

# 6 Sensitivity checks

The Pinus down-weighting and one age-jitter draw did not change the central conclusion that lags differ among genera and that modern climate velocity is much faster than the median inferred migration rate.

| Run | Fossil sites | Median across genus median lags yr | Median migration m/yr |
| --- | --- | --- | --- |
| Base | 72 | 1500 | 164.7 |
| Pinus down-weighted | 72 | 1500 | 189.1 |
| Age jitter draw 1 | 71 | 1500 | 145.0 |

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
