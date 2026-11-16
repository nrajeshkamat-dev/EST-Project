"""Shared helpers."""
import numpy as np
import pandas as pd
from scipy import stats
import config as C


def ensure_dirs():
    for d in (C.RAW, C.PROC, C.OUT, C.STAGE_LOGS):
        d.mkdir(parents=True, exist_ok=True)


def to_genus(taxon: str) -> str:
    """Map a Neotoma taxon name to a genus in C.GENERA, else 'Other'."""
    if not isinstance(taxon, str) or not taxon.strip():
        return "Other"
    first = taxon.replace("/", " ").replace("-", " ").split()[0].strip().capitalize()
    return first if first in C.GENERA else "Other"


def hellinger(p, q):
    """Hellinger distance between two proportion vectors (0..1)."""
    return float(np.sqrt(0.5 * np.sum((np.sqrt(p) - np.sqrt(q)) ** 2)))


def scd_matrix(A, B):
    """Squared chord distance between every row of A and every row of B."""
    sa, sb = np.sqrt(A), np.sqrt(B)
    d = (sa ** 2).sum(1)[:, None] + (sb ** 2).sum(1)[None, :] - 2 * sa @ sb.T
    return np.maximum(d, 0)


def site_bins(bin_width=None):
    bw = bin_width or C.BIN_WIDTH
    return np.arange(C.AGE_MIN + bw / 2, C.AGE_MAX, bw)


def load_binned(path=None):
    path = path or C.PROC / "binned.csv"
    return pd.read_csv(path)


def latlon_to_xy_km(lat, lon, lat0=None, lon0=None):
    """Local equal-area tangent-plane projection (km) centered at (lat0, lon0)."""
    lat = np.asarray(lat, dtype=float)
    lon = np.asarray(lon, dtype=float)
    lat0 = float(np.mean(lat) if lat0 is None else lat0)
    lon0 = float(np.mean(lon) if lon0 is None else lon0)
    km_per_deg_lat = 111.32
    km_per_deg_lon = 111.32 * np.cos(np.radians(lat0))
    return (lon - lon0) * km_per_deg_lon, (lat - lat0) * km_per_deg_lat, lat0, lon0


def ebisuzaki_surrogates(x, n_sim=1000, rng=None):
    """Generate FFT phase-randomized surrogates preserving x's power spectrum (Ebisuzaki 1997)."""
    rng = rng or np.random.default_rng(0)
    x = np.asarray(x, dtype=float)
    n = len(x)
    xc = x - x.mean()
    spec = np.fft.rfft(xc)
    amp = np.abs(spec)
    n_freq = len(spec)
    phases = rng.uniform(0.0, 2.0 * np.pi, size=(n_sim, n_freq))
    phases[:, 0] = 0.0
    if n % 2 == 0:
        phases[:, -1] = rng.choice([0.0, np.pi], size=n_sim)
    return np.fft.irfft(amp[None, :] * np.exp(1j * phases), n=n, axis=1) + x.mean()


def ebisuzaki_p(x, y, r_obs=None, n_sim=1000, method="pearson", rng=None):
    """Two-sided Ebisuzaki phase-randomization p-value for Pearson or Spearman correlation."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if len(x) < 4 or np.std(x) == 0 or np.std(y) == 0:
        return np.nan
    surr = ebisuzaki_surrogates(x, n_sim=n_sim, rng=rng)
    if method == "spearman":
        if r_obs is None:
            r_obs = float(stats.spearmanr(x, y).statistic)
        yr = stats.rankdata(y)
        yc = yr - yr.mean()
        sr = np.apply_along_axis(stats.rankdata, 1, surr)
        sc = sr - sr.mean(axis=1, keepdims=True)
    else:
        if r_obs is None:
            r_obs = float(np.corrcoef(x, y)[0, 1])
        yc = y - y.mean()
        sc = surr - surr.mean(axis=1, keepdims=True)
    denom = np.linalg.norm(sc, axis=1) * np.linalg.norm(yc)
    r_sim = np.where(denom > 0, (sc @ yc) / np.maximum(denom, 1e-12), 0.0)
    return float((np.sum(np.abs(r_sim) >= abs(r_obs)) + 1) / (n_sim + 1))


COLS = C.GENERA + ["Other"]
