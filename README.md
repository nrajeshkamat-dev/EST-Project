# TBD2 - Lags between climate change and tree-genus response (eastern North America)

Python pipeline. Run in order from this folder.

## Data sources
| Data | Source | How it is used |
|---|---|---|
| Fossil pollen (0-15 ka) | Neotoma Paleoecology Database, API v2.0 (`https://api.neotomadb.org/v2.0/data`), dataset type `pollen` | genus proportions per site and 500-yr bin |
| Modern pollen | Neotoma, dataset type `pollen surface sample` | reference set for no-analogue detection |
| Climate (primary) | TraCE-21ka, NCAR GDEX dataset d651050, DOI 10.5065/CXB5-TV56. Variable `TREFHT`, decadal averages | temperature at each site, 22 ka to present; independent of pollen |
| Climate (optional check) | Marsicek et al. 2018, NOAA NCEI `https://www.ncei.noaa.gov/pub/data/paleo/reconstructions/marsicek2018/` | Holocene only; **pollen-derived**, so using it to explain pollen is circular. Use only as a consistency check |
| Harmonised chronologies (optional) | LegacyAge 1.0 (Li et al. 2022) | better age models; not wired in, see "Extending" |

## Run
```
pip install -r requirements.txt
python 01_download_data.py --limit 3     # test first; inspect data/raw/fossil/*.json
python 01_download_data.py               # full download (hundreds of datasets, can take a while)
python 02_preprocess.py
# put TraCE TREFHT *.nc files in data/raw/trace/ (download from GDEX d651050)
python 03a_climate_trace.py              # READ the printed time-axis interpretation
python 03_metrics.py                     # lags (RQ1), no-analogue (RQ2)
python 04_migration_rates.py             # migration vs climate velocity (RQ3)
python 05_figures.py
```
Sensitivity runs:
```
python 02_preprocess.py --pinus-downweight && python 03_metrics.py --binned binned_pinus.csv --tag pinus && python 04_migration_rates.py --binned binned_pinus.csv --tag pinus
for k in 1 2 3 4 5; do python 02_preprocess.py --jitter $k; python 03_metrics.py --binned binned_jitter_$k.csv --tag j$k; done
```

## Pipeline test (synthetic data, NOT results)
```
DATA_DIR=data_demo python synthetic_demo.py
for s in 03_metrics 04_migration_rates 05_figures; do DATA_DIR=data_demo python $s.py; done
```
Plants known lags and a known migration rate, then checks they are recovered.

## Things to verify before trusting real-data output
1. Neotoma JSON layout (parsing in `01_download_data.py` is defensive but untested against the live API).
2. TraCE time axis and whether decadal files are annual means (script prints its assumption).
3. `MODERN_WARMING_C_PER_CENTURY` in `config.py` is a placeholder; cite a source.
4. Thresholds in `config.py` (arrival 5%, no-analogue 95th percentile, 500-yr bins) are choices; report sensitivity.
5. Lag = shift maximising |correlation| between genus proportion and temperature. Both series trend through the deglaciation, so correlations are inflated and p-values ignore autocorrelation.

## Files
config.py, lib.py (shared) | 01 download | 02 preprocess | 03a climate | 03 metrics | 04 migration | 05 figures | synthetic_demo.py
