"""Modular stage-by-stage audit logging, numeric delta snapshots, and manifest tracking."""
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import config as C


def _read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8")) if Path(path).exists() else None


def extract_tag_metrics(tag, out_dir=None, proc_dir=None, binned_name=None):
    """Read standard metrics from tagged outputs into a flat, diffable dict."""
    out_dir = Path(out_dir or C.OUT)
    proc_dir = Path(proc_dir or C.PROC)
    m = {"tag": tag}

    # Climate check
    creg_p = proc_dir / "climate_regional.csv"
    if creg_p.exists():
        creg = pd.read_csv(creg_p)
        m["temp_c_min"] = round(float(creg.temp_c.min()), 3)
        m["temp_c_max"] = round(float(creg.temp_c.max()), 3)
        if "precip_mm_day" in creg.columns:
            m["precip_mm_day_mean"] = round(float(creg.precip_mm_day.mean()), 3)

    # Binned sample & site counts
    b_candidates = [proc_dir / binned_name] if binned_name else [
        proc_dir / f"binned_{tag}.csv",
        proc_dir / "binned.csv",
    ]
    for bp in b_candidates:
        if bp.exists():
            b = pd.read_csv(bp)
            m["n_sites"] = int(b.site_id.nunique())
            m["n_binned"] = int(len(b))
            break

    # Lag summary + Ebisuzaki pass rate
    ls_p = out_dir / f"lag_summary_{tag}.csv"
    if ls_p.exists():
        ls = pd.read_csv(ls_p)
        m["lag_genera_count"] = int(len(ls))
        m["median_across_genera_lag_yr"] = round(float(ls.median_lag_yr.median()), 1) if len(ls) else None
        m["per_genus_median_lag_yr"] = {
            r.genus: float(r.median_lag_yr) for _, r in ls.iterrows()
        }
    l_p = out_dir / f"lags_{tag}.csv"
    if l_p.exists():
        ldf = pd.read_csv(l_p)
        m["n_site_genus_lag_pairs"] = int(len(ldf))
        if "p_ebisuzaki" in ldf.columns and len(ldf):
            m["ebisuzaki_pass_rate_p05"] = round(float((ldf.p_ebisuzaki < 0.05).mean()), 4)
            m["ebisuzaki_n_sig_p05"] = int((ldf.p_ebisuzaki < 0.05).sum())

    # No-analogue
    na_p = out_dir / f"no_analogue_{tag}.csv"
    if na_p.exists():
        na = pd.read_csv(na_p)
        m["no_analogue_overall_frac"] = round(float(na.no_analogue.mean()), 4)
    nac_p = out_dir / f"noanalogue_vs_climate_{tag}.csv"
    if nac_p.exists():
        nac = pd.read_csv(nac_p)
        row500 = nac[nac.bin_age == 500.0]
        if len(row500):
            m["no_analogue_500bp_floor"] = round(float(row500.frac_no_analogue.iloc[0]), 4)
        m["no_analogue_peak_frac"] = round(float(nac.frac_no_analogue.max()), 4)
        idx_pk = int(nac.frac_no_analogue.idxmax())
        m["no_analogue_peak_age_bp"] = float(nac.loc[idx_pk, "bin_age"])

    tests_p = out_dir / f"tests_{tag}.json"
    if tests_p.exists():
        t = _read_json(tests_p)
        m["no_analogue_threshold_scd"] = round(float(t.get("no_analogue_threshold_scd", np.nan)), 5)
        m["kruskal_p"] = float(t["kruskal_p"]) if "kruskal_p" in t else None
        if "spearman_noanalogue_vs_abs_climate_rate" in t:
            m["spearman_na_vs_clim"] = round(float(t["spearman_noanalogue_vs_abs_climate_rate"][0]), 4)
        if "spearman_noanalogue_vs_veg_rate" in t:
            m["spearman_na_vs_veg"] = round(float(t["spearman_noanalogue_vs_veg_rate"][0]), 4)

    # Migration & velocity
    mig_p = out_dir / f"migration_{tag}.csv"
    if mig_p.exists():
        mig = pd.read_csv(mig_p)
        rate_col = "rate_2d_median_m_per_yr" if "rate_2d_median_m_per_yr" in mig.columns else "rate_m_per_yr"
        sig_1d = mig["rate_m_per_yr"].notna().sum() if "rate_m_per_yr" in mig.columns else 0
        sig_2d = mig["rate_2d_median_m_per_yr"].notna().sum() if "rate_2d_median_m_per_yr" in mig.columns else 0
        m["n_sig_mig_genera_1d"] = int(sig_1d)
        if "rate_2d_median_m_per_yr" in mig.columns:
            m["n_2d_surface_genera"] = int(sig_2d)
            m["median_migration_2d_m_per_yr"] = round(float(mig.rate_2d_median_m_per_yr.median()), 2) if sig_2d else None
        if "rate_m_per_yr" in mig.columns and sig_1d:
            m["median_migration_1d_m_per_yr"] = round(float(mig.rate_m_per_yr.median()), 2)
        m["median_migration_m_per_yr"] = m.get("median_migration_2d_m_per_yr") or m.get("median_migration_1d_m_per_yr")

    vel_p = out_dir / f"velocity_comparison_{tag}.json"
    if vel_p.exists():
        v = _read_json(vel_p)
        m["modern_climate_velocity_m_per_yr"] = round(float(v["modern_climate_velocity_m_per_yr"]), 1) if v.get("modern_climate_velocity_m_per_yr") else None
        m["past_p95_climate_velocity_m_per_yr"] = round(float(v["past_p95_climate_velocity_m_per_yr"]), 1) if v.get("past_p95_climate_velocity_m_per_yr") else None
    return m


def _compute_deltas(curr_metrics, prev_metrics):
    if not prev_metrics:
        return {}
    deltas = {}
    for k, val in curr_metrics.items():
        if k in ("tag", "per_genus_median_lag_yr") or val is None or isinstance(val, (str, dict, list)):
            continue
        pval = prev_metrics.get(k)
        if isinstance(val, (int, float)) and isinstance(pval, (int, float)):
            d = round(float(val) - float(pval), 6)
            if d != 0.0:
                deltas[k] = d
    curr_g = curr_metrics.get("per_genus_median_lag_yr") or {}
    prev_g = prev_metrics.get("per_genus_median_lag_yr") or {}
    g_delta = {}
    for g in sorted(set(curr_g) | set(prev_g)):
        if g in curr_g and g in prev_g:
            diff = curr_g[g] - prev_g[g]
            if diff != 0:
                g_delta[g] = diff
        elif g in curr_g:
            g_delta[g] = f"added ({curr_g[g]:.0f})"
        else:
            g_delta[g] = f"dropped (was {prev_g[g]:.0f})"
    if g_delta:
        deltas["per_genus_lag_shift_yr"] = g_delta
    return deltas


def record_stage(
    stage_num,
    name,
    cli_cmd,
    inputs,
    outputs,
    metrics,
    counts=None,
    dropped=None,
    warnings=None,
    notes=None,
    started_at=None,
    ended_at=None,
):
    """Write stage_<NN>_<name>.log + .json, update manifest, and refresh STAGE_CHANGELOG.md."""
    C.STAGE_LOGS.mkdir(parents=True, exist_ok=True)
    sn = f"{int(stage_num):02d}"
    stem = f"stage_{sn}_{name}"
    log_path = C.STAGE_LOGS / f"{stem}.log"
    json_path = C.STAGE_LOGS / f"{stem}.json"
    manifest_path = C.STAGE_LOGS / "pipeline_run_manifest.json"
    changelog_path = C.STAGE_LOGS / "STAGE_CHANGELOG.md"

    now_iso = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    started_at = started_at or now_iso
    ended_at = ended_at or now_iso

    manifest = _read_json(manifest_path) or {"project": "EST-Project Phase 1", "stages": []}
    prev_metrics = None
    for s in reversed(manifest["stages"]):
        if int(s["stage"]) < int(stage_num):
            prev_json = _read_json(Path(C.ROOT) / s["json_file"]) if not Path(s["json_file"]).is_absolute() else _read_json(s["json_file"])
            prev_metrics = (prev_json or {}).get("metrics")
            break

    deltas = _compute_deltas(metrics, prev_metrics)
    payload = {
        "stage": sn,
        "name": name,
        "started_at": started_at,
        "ended_at": ended_at,
        "cli_command": cli_cmd,
        "inputs": [str(x) for x in inputs],
        "outputs": [str(x) for x in outputs],
        "counts": counts or {},
        "dropped": dropped or [],
        "warnings": warnings or [],
        "notes": notes or [],
        "metrics": metrics,
        "deltas_vs_previous_stage": deltas,
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Human-readable log
    lines = [
        f"=== Stage {sn}: {name} ===",
        f"Start:   {started_at}",
        f"End:     {ended_at}",
        f"Command: {cli_cmd}",
        "",
        "Inputs:",
        *[f"  - {x}" for x in inputs],
        "Outputs:",
        *[f"  - {x}" for x in outputs],
    ]
    if counts:
        lines += ["", "Counts (before / after filtering):"]
        lines += [f"  {k}: {v}" for k, v in counts.items()]
    if dropped:
        lines += ["", f"Dropped sites/taxa ({len(dropped)} entries):"]
        lines += [f"  - {d}" for d in dropped[:50]]
        if len(dropped) > 50:
            lines.append(f"  ... ({len(dropped) - 50} more)")
    if warnings:
        lines += ["", "Warnings / Fallbacks:"]
        lines += [f"  ! {w}" for w in warnings]
    if notes:
        lines += ["", "Notes:"]
        lines += [f"  * {n}" for n in notes]
    lines += ["", "Summary Metrics:", json.dumps(metrics, indent=2)]
    if deltas:
        lines += ["", "Deltas vs Previous Stage:", json.dumps(deltas, indent=2)]
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Update manifest (replace existing stage if re-run, keep sorted by stage)
    rel = lambda p: str(Path(p).resolve().relative_to(C.ROOT.resolve())).replace("\\", "/")
    entry = {
        "stage": sn,
        "name": name,
        "tag": metrics.get("tag"),
        "ended_at": ended_at,
        "log_file": rel(log_path),
        "json_file": rel(json_path),
        "key_metrics": {k: v for k, v in metrics.items() if k != "per_genus_median_lag_yr"},
        "deltas_vs_previous_stage": deltas,
    }
    stages = [s for s in manifest["stages"] if s["stage"] != sn]
    stages.append(entry)
    stages.sort(key=lambda x: int(x["stage"]))
    manifest["updated_at"] = now_iso
    manifest["stages"] = stages
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Rebuild STAGE_CHANGELOG.md cleanly
    md = ["# EST-Project Phase 1 — Stage Execution Changelog", "", f"Last updated: `{now_iso}`", ""]
    for s in stages:
        sj = _read_json(C.ROOT / s["json_file"]) or {}
        km = s.get("key_metrics", {})
        dl = s.get("deltas_vs_previous_stage", {})
        md += [
            f"## Stage {s['stage']} — {s['name']} (`tag={s.get('tag')}`)",
            f"- **Command:** `{sj.get('cli_command', '')}`",
            f"- **Inputs:** {', '.join(f'`{Path(x).name}`' for x in sj.get('inputs', []))}",
            f"- **Outputs:** {', '.join(f'`{Path(x).name}`' for x in sj.get('outputs', []))}",
            f"- **Key Metrics:** sites=`{km.get('n_sites', 'NA')}`, binned=`{km.get('n_binned', 'NA')}`, "
            f"500 BP no-analogue=`{km.get('no_analogue_500bp_floor', 'NA')}`, "
            f"Ebisuzaki p<0.05=`{km.get('ebisuzaki_pass_rate_p05', 'NA')}`, "
            f"median migration=`{km.get('median_migration_m_per_yr', 'NA')}` m/yr",
        ]
        if dl:
            md.append(f"- **Deltas vs previous stage:** `{json.dumps(dl)}`")
        if sj.get("warnings"):
            md.append(f"- **Warnings/Fallbacks:** {'; '.join(sj['warnings'])}")
        md.append("")
    changelog_path.write_text("\n".join(md), encoding="utf-8")
    print(f"[stage {sn}] logged -> {rel(log_path)}")
    return payload

