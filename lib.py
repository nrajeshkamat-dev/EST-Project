"""Shared helpers."""
import json
import numpy as np
import pandas as pd
import config as C


def ensure_dirs():
    for d in (C.RAW, C.PROC, C.OUT):
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


def site_bins():
    return np.arange(C.AGE_MIN + C.BIN_WIDTH / 2, C.AGE_MAX, C.BIN_WIDTH)


def load_binned(path=None):
    path = path or C.PROC / "binned.csv"
    return pd.read_csv(path)


COLS = C.GENERA + ["Other"]
