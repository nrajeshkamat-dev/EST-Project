"""Step 1: download fossil pollen (and modern surface pollen) from the Neotoma API v2.0.

Output: data/processed/fossil_long.csv, modern_long.csv
NOTE: Neotoma's JSON layout can change. Parsing below is defensive, but run with --limit 3
first and check data/raw/*.json against the printed summary before a full download.
"""
import argparse, json, time
import pandas as pd
import requests
import config as C
from lib import ensure_dirs

API = "https://api.neotomadb.org/v2.0/data"


def get(url, params=None, tries=4):
    for i in range(tries):
        try:
            r = requests.get(url, params=params, timeout=120)
            if r.status_code >= 400:
                print(f"  HTTP {r.status_code}: {r.text[:300]}")
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"  retry {i+1}: {e}")
            time.sleep(2 * (i + 1))
    return None


def find_key(obj, key):
    """Yield every value stored under `key` anywhere in a nested JSON object."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key:
                yield v
            yield from find_key(v, key)
    elif isinstance(obj, list):
        for v in obj:
            yield from find_key(v, key)


def bbox_polygons():
    """Neotoma v2.0 wants `loc` as WKT or GeoJSON, not a bare 'lonW,latS,lonE,latN' string."""
    w, s_, e, n = C.BBOX
    ring = [(w, s_), (e, s_), (e, n), (w, n), (w, s_)]
    wkt = "POLYGON((" + ", ".join(f"{x} {y}" for x, y in ring) + "))"
    gj = json.dumps({"type": "Polygon", "coordinates": [[list(p) for p in ring]]})
    return [("WKT", wkt), ("GeoJSON", gj)]


def inside_bbox(lat, lon):
    if lat is None or lon is None:
        return False
    w, s_, e, n = C.BBOX
    return w <= float(lon) <= e and s_ <= float(lat) <= n


def dataset_ids_on_site(site):
    vals = []
    for key in ("dataset", "datasets"):
        data = site.get(key)
        if isinstance(data, dict) and data.get("datasetid") is not None:
            vals.append(int(data["datasetid"]))
        elif isinstance(data, list):
            vals += [int(x["datasetid"]) for x in data if isinstance(x, dict) and x.get("datasetid") is not None]
    return vals


def list_dataset_ids(datasettype, with_ages, local_bbox_filter=False):
    for fmt, loc in bbox_polygons():
        for page in (500, 100, 25):
            ids, offset = set(), 0
            ok = True
            while True:
                params = {"datasettype": datasettype, "loc": loc, "limit": page, "offset": offset}
                if with_ages:
                    params.update({"ageold": C.AGE_MAX, "ageyoung": C.AGE_MIN})
                js = get(f"{API}/datasets", params, tries=2)
                if js is None:
                    ok = False
                    break
                if not js.get("data"):
                    break
                if local_bbox_filter:
                    for entry in js["data"]:
                        site = entry.get("site", entry)
                        lat, lon = site_latlon(site)
                        if inside_bbox(lat, lon):
                            ids |= set(dataset_ids_on_site(site))
                else:
                    ids |= {int(x) for x in find_key(js["data"], "datasetid")}
                if len(js["data"]) < page:
                    break
                offset += page
            if ok and ids:
                print(f"  (loc as {fmt}, page size {page})")
                return sorted(ids)
    return []


def site_latlon(site):
    g = site.get("geography")
    if isinstance(g, str):
        try: g = json.loads(g)
        except Exception: g = None
    if isinstance(g, dict) and g.get("coordinates"):
        c = g["coordinates"]
        if g.get("type") == "Point":
            return c[1], c[0]
        ring = c[0] if isinstance(c[0][0], list) else c
        lons, lats = [p[0] for p in ring], [p[1] for p in ring]
        return sum(lats) / len(lats), sum(lons) / len(lons)
    return site.get("latitude"), site.get("longitude")


def sample_age(s):
    ages = s.get("ages") or []
    cal = [a for a in ages if "calendar" in str(a.get("agetype", "")).lower()] or ages
    for a in cal:
        if a.get("age") is not None:
            return a["age"]
        if a.get("ageolder") is not None and a.get("ageyounger") is not None:
            return (a["ageolder"] + a["ageyounger"]) / 2
    return s.get("sampleage", None)


def parse_download(js, dsid):
    rows = []
    for entry in js.get("data", []):
        site = entry.get("site", entry)
        lat, lon = site_latlon(site)
        for samples in find_key(site, "samples"):
            for s in samples:
                age = sample_age(s)
                for d in s.get("datum", []) or []:
                    grp = str(d.get("ecologicalgroup", ""))
                    el = str(d.get("elementtype", "pollen")).lower()
                    if grp not in ("TRSH", "UPHE") or "pollen" not in el:
                        continue
                    rows.append(dict(dataset_id=dsid, site_id=site.get("siteid"),
                                     sitename=site.get("sitename"), lat=lat, lon=lon,
                                     depth=s.get("depth"), age_bp=age,
                                     taxon=d.get("variablename", d.get("taxonname")),
                                     group=grp, count=d.get("value")))
    return rows


def cached_dataset_ids(tag):
    cache = C.RAW / tag
    if not cache.exists():
        return []
    return sorted(int(p.stem) for p in cache.glob("*.json") if p.stem.isdigit())


def fetch(ids, tag, limit=None):
    cache = C.RAW / tag
    cache.mkdir(parents=True, exist_ok=True)
    allrows = []
    for n, dsid in enumerate(ids[:limit] if limit else ids, 1):
        f = cache / f"{dsid}.json"
        if f.exists():
            js = json.loads(f.read_text())
        else:
            js = get(f"{API}/downloads/{dsid}")
            if js is None:
                continue
            f.write_text(json.dumps(js))
            time.sleep(0.2)
        allrows += parse_download(js, dsid)
        if n % 25 == 0:
            print(f"  {tag}: {n}/{len(ids)} datasets")
    return pd.DataFrame(allrows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="only first N datasets (testing)")
    ap.add_argument("--modern-max", type=int, default=None,
                    help="download a random sample of at most N modern surface-pollen datasets")
    ap.add_argument("--offline-cache", action="store_true",
                    help="skip Neotoma listing and build processed CSVs from cached data/raw JSON files")
    ap.add_argument("--only", choices=["fossil", "modern"], default=None,
                    help="download/rebuild only one dataset group")
    a = ap.parse_args()
    ensure_dirs()
    for dtype, tag, ages, out in [("pollen", "fossil", True, "fossil_long.csv"),
                                   ("pollen surface sample", "modern", False, "modern_long.csv")]:
        if a.only and tag != a.only:
            continue
        ids = cached_dataset_ids(tag) if a.offline_cache else list_dataset_ids(dtype, ages, local_bbox_filter=(tag == "modern"))
        if not ids and not a.offline_cache:
            ids = cached_dataset_ids(tag)
            if ids:
                print(f"  Neotoma listing unavailable; using {len(ids)} cached {tag} JSON files")
        print(f"{dtype}: {len(ids)} datasets in bbox/cache")
        if not ids:
            print(f"  no API/cache datasets for {tag}; leaving {out} unchanged")
            continue
        if tag == "modern" and a.modern_max and len(ids) > a.modern_max:
            import random
            random.Random(0).shuffle(ids)
            ids = sorted(ids[: a.modern_max])
            print(f"  using a random sample of {len(ids)} modern datasets")
        df = fetch(ids, tag, a.limit)
        df.to_csv(C.PROC / out, index=False)
        print(f"  wrote {out}: {len(df)} rows, {df['dataset_id'].nunique() if len(df) else 0} datasets")
