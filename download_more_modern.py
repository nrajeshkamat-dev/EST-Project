"""Fetch more Neotoma modern pollen surface samples inside the study bbox.

This is a pragmatic fallback for when /datasets listing is too slow or ignores loc.
It probes dataset IDs above the current cache and saves only successful modern
surface-pollen downloads whose site coordinates fall inside config.BBOX.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path

import requests

import config as C
from importlib import import_module


d = import_module("01_download_data")

API = "https://api.neotomadb.org/v2.0/data"
CACHE = C.RAW / "modern"
CACHE.mkdir(parents=True, exist_ok=True)


def is_surface_pollen(js):
    return any(str(x).lower() == "pollen surface sample" for x in d.find_key(js, "datasettype"))


def inside_download(js):
    for entry in js.get("data", []):
        site = entry.get("site", entry)
        lat, lon = d.site_latlon(site)
        if d.inside_bbox(lat, lon):
            return True
    return False


def cached_inside_count():
    n = 0
    for p in CACHE.glob("*.json"):
        try:
            js = json.loads(p.read_text())
        except Exception:
            continue
        if is_surface_pollen(js) and inside_download(js):
            n += 1
    return n


def fetch_one(dsid):
    f = CACHE / f"{dsid}.json"
    if f.exists():
        return dsid, "cached"
    try:
        r = requests.get(f"{API}/downloads/{dsid}", timeout=25)
        r.raise_for_status()
        js = r.json()
    except Exception as e:
        return dsid, f"error:{type(e).__name__}"
    if js.get("status") != "success" or not js.get("data"):
        return dsid, "empty"
    if not is_surface_pollen(js):
        return dsid, "not-modern"
    if not inside_download(js):
        return dsid, "outside"
    f.write_text(json.dumps(js))
    return dsid, "saved"


def main(target=1000, start=3158, stop=7000, batch=250, workers=24):
    inside = cached_inside_count()
    print(f"inside cached modern datasets: {inside}", flush=True)
    dsid = start
    while inside < target and dsid <= stop:
        ids = list(range(dsid, min(dsid + batch, stop + 1)))
        saved = 0
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = [ex.submit(fetch_one, x) for x in ids]
            for fut in as_completed(futures):
                _, status = fut.result()
                if status == "saved":
                    saved += 1
        inside = cached_inside_count()
        print(f"checked {ids[0]}-{ids[-1]}: saved {saved}, inside cache {inside}", flush=True)
        dsid += batch
    if inside < target:
        raise SystemExit(f"Only reached {inside} inside modern datasets by id {stop}")


if __name__ == "__main__":
    main()
