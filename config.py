"""Central settings for the TBD2 pipeline. Edit here, nowhere else."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get("DATA_DIR", ROOT / "data"))   # set DATA_DIR=data_demo for the synthetic test
RAW, PROC, OUT = DATA / "raw", DATA / "processed", DATA / "outputs"
GEO = ROOT / "data" / "geo"
STAGE_LOGS = OUT / "stage_logs"

# Study region: eastern North America (lon W, lat S, lon E, lat N)
BBOX = (-100.0, 34.0, -60.0, 52.0)
AGE_MAX, AGE_MIN = 15000, 0          # years BP
BIN_WIDTH = 500                      # years

# Genera analysed (everything else is pooled into "Other")
GENERA = ["Picea", "Abies", "Larix", "Pinus", "Tsuga", "Betula", "Quercus",
          "Fagus", "Fraxinus", "Ulmus", "Carya", "Acer", "Alnus", "Populus"]

# Site / sample filters
MIN_GRAINS = 100          # minimum pollen sum per sample
MIN_BINS = 12             # minimum occupied bins per site (of 30)
MAX_GAP_BINS = 4          # largest allowed gap between occupied bins

# Lag analysis: vegetation lags climate by k bins, k = 0..MAX_LAG_BINS
MAX_LAG_BINS = 6
MIN_BINS_LAG = 12
MIN_MEAN_PROP = 0.02      # genus must average >=2% at a site to be analysed there

# No-analogue: threshold = this percentile of nearest-neighbour SCD among modern samples
NOANALOG_PERCENTILE = 95

# Migration: genus "arrives" when proportion >= threshold for 2 consecutive bins
ARRIVAL_THRESHOLD = 0.05
MIN_SITES_MIGRATION = 8

# Sensitivity analyses (NOT calibrated values - they test how much results depend on them)
PINUS_DOWNWEIGHT = 0.5    # multiplies Pinus counts to test pine over-representation
AGE_SD_FRAC = 0.05        # age jitter sd as a fraction of age (simple stand-in for age-model draws)

# Empirical Relative Pollen Productivity (RPP v2, relative to Poaceae = 1.0)
# Sources: Wieczorek & Herzschuh (2020) ESSD Table 5 (North America / NH consensus);
# Tsuga (~1.60) from Calcote (1995) / Dawson et al. (2016) STEPPS; Carya (1.00) moderate fallback.
RPP_WEIGHTS = {
    "Picea": 2.80, "Abies": 6.88, "Larix": 1.24, "Pinus": 14.10, "Tsuga": 1.60,
    "Betula": 6.19, "Quercus": 2.08, "Fagus": 2.35, "Fraxinus": 2.42, "Ulmus": 2.24,
    "Carya": 1.00, "Acer": 0.23, "Alnus": 2.70, "Populus": 0.67, "Other": 1.00,
}

# Statistical & chronological parameters (Phase 1)
EBISUZAKI_N = 1000
LEGACYAGE_ENSEMBLE_N = 50
LEGACYAGE_URL = "https://download.pangaea.de/reference/111162/attachments/Table-S5_legacyage_1_0_chronology.csv"

# Recent global warming rate, deg C per century.
# IPCC AR6 assessed about 0.19 C per decade over 1980-2020.
MODERN_WARMING_C_PER_CENTURY = 1.9

# TraCE-21ka
TRACE_VAR = "TREFHT"      # reference-height temperature
TRACE_PRECT_VAR = "PRECT" # total precipitation rate (m/s -> mm/day)
TRACE_TREFHT_GLOB = "*TREFHT*decavg_400BCE.nc"
TRACE_PRECT_GLOB = "*PRECT*decavg_400BCE.nc"
TRACE_PRECT_URLS = [
    "https://osdf-director.osg-htc.org/ncar/gdex/d651050/TraCE/TraCE-Main/atm/proc/tavg/decadal/trace.01-36.22000BP.cam2.PRECT.22000BP_decavg_400BCE.nc",
    "https://tds.gdex.ucar.edu/thredds/fileServer/files/d651050/TraCE/TraCE-Main/atm/proc/tavg/decadal/trace.01-36.22000BP.cam2.PRECT.22000BP_decavg_400BCE.nc",
]
