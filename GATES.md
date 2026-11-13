# Gates: EST-Project Phase 1 Upgrade

OWNS: config.py, lib.py, stage_log.py, 01b_fetch_legacyage.py, 02_preprocess.py, 03a_climate_trace.py, 03_metrics.py, 04_migration_rates.py, 05_visualizations_modern.py, 06_build_report.py, synthetic_demo.py, data/outputs/**, TBD2_MidProject_Baseline_Report.html, TBD2_Final_Report.html, TBD2_Final_Project_Report.docx

Scope: Upgrade EST-Project Phase 1 with root-cause climate/TRSH fixes, stationary Ebisuzaki lags, RPP calibration, LegacyAge 1.0 chronologies, 2D arrival isochrones, full stage logs, and Mid-vs-Final interactive HTML and DOCX reports.

- [x] G0: ledger states outcomes that can fail
  CHECK: node C:/Users/vivek/.gemini/config/skills/unlazy/scripts/gate-lint.mjs GATES.md
  EXPECT: LINT OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=810a806af423ad13d2afe59dfe1c53992962d3dcf22defda7017513245a724f3; exit=0; EXPECT=matched; output-sha256=48630b7361dd44ee870917b12c3d19b9d7bdea738aaca16bb04d4cab83b772d2; output-bytes=8; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\vivek\EST\EST-Project; path=d6f435cc73e6/35 entries

- [x] G1: mid-project baseline snapshot and visual report exist from pre-upgrade outputs
  CHECK: python -c "from pathlib import Path; req=[Path('data/outputs/mid_project/lag_summary_base.csv'), Path('data/outputs/mid_project/figures_modern/fig1_sites.png'), Path('TBD2_MidProject_Baseline_Report.html')]; assert all(p.exists() and p.stat().st_size>100 for p in req); print('G1_MID_BASELINE_OK')"
  EXPECT: G1_MID_BASELINE_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=ebe5b3661de55eae05dcb3e9b7fb308eff55d462b2026cab170eb9c582ea59de; exit=0; EXPECT=matched; output-sha256=af4a1ff606a78f30011a9914452327240df1e0238df7402a745f20b947af39f0; output-bytes=20; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\vivek\EST\EST-Project; path=fc935e31ffb2/35 entries

- [x] G2: climate CSVs hold verified Celsius and TraCE precipitation within physical bounds
  CHECK: python -c "import pandas as pd; cr=pd.read_csv('data/processed/climate_regional.csv'); cs=pd.read_csv('data/processed/climate_sites.csv'); assert -30 < cr.temp_c.min() <= cr.temp_c.max() < 35; assert -35 < cs.temp_c.min() <= cs.temp_c.max() < 40; assert 'precip_mm_day' in cr.columns and (cr.precip_mm_day > 0).all() and (cr.precip_mm_day < 30).all(); print('G2_CLIMATE_OK')"
  EXPECT: G2_CLIMATE_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=1700c12612ca6d7cc00374cf67c1c7dc7d8f45edf1040b29255de6d8c50199ee; exit=0; EXPECT=matched; output-sha256=70a1ad5a51c26639eb38068ec6e3bb88208a2e52c0044a95b409d025a307b1a2; output-bytes=15; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\vivek\EST\EST-Project; path=d6f435cc73e6/35 entries

- [x] G3: TRSH-only cleans UPHE 500 BP weed floor relative to TRSH+UPHE while preserving both
  CHECK: python -c "import pandas as pd; raw=pd.read_csv('data/outputs/noanalogue_vs_climate_raw_celsius.csv'); tr=pd.read_csv('data/outputs/noanalogue_vs_climate_trsh_only.csv'); r500=float(raw.loc[raw.bin_age==500,'frac_no_analogue'].iloc[0]); t500=float(tr.loc[tr.bin_age==500,'frac_no_analogue'].iloc[0]); assert t500 < r500 and t500 < 0.22; assert pd.read_csv('data/outputs/no_analogue_drivers_trsh_only.csv').shape[0] > 0; print('G3_TRSH_OK')"
  EXPECT: G3_TRSH_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=15a7f7f2ed56f237c70d324ef825485fc236ad99b0a90e56dd30a0a865528a67; exit=0; EXPECT=matched; output-sha256=fa24f8b37d303ba8c2e47216fbc1d7f207e22e4cede1a7f645eee00485753488; output-bytes=12; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\vivek\EST\EST-Project; path=d6f435cc73e6/35 entries

- [x] G4: stationary diff lags, Ebisuzaki p-values, RPP, LegacyAge ensemble, and 2D isochrones finish cleanly
  CHECK: python -c "import json, pandas as pd; l=pd.read_csv('data/outputs/lags_final_2d.csv'); assert {'r','p_ebisuzaki'}.issubset(l.columns) and (l.p_ebisuzaki.between(0,1)).all(); m=pd.read_csv('data/outputs/migration_final_2d.csv'); assert 'rate_2d_median_m_per_yr' in m.columns and m.rate_2d_median_m_per_yr.notna().sum() >= 3; ens=json.load(open('data/outputs/ensemble_summary_legacyage.json')); assert ens['n_ensemble'] == 50; assert pd.read_csv('data/outputs/lag_summary_bin250.csv').shape[0] >= 5; print('G4_METHODS_OK')"
  EXPECT: G4_METHODS_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=aedbbcdbb902b1ce454aedfcd08ba1af6415878d8f135ef3ac25b5186ba08cc7; exit=0; EXPECT=matched; output-sha256=e8b6f01c4443df853450b2d153220901106c383a64c2902c43bd131f4e2d213b; output-bytes=15; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\vivek\EST\EST-Project; path=d6f435cc73e6/35 entries

- [x] G5: synthetic demo passes detrended lag, Ebisuzaki null rejection, and 2D migration assertions
  CHECK: python synthetic_demo.py --verify
  EXPECT: SYNTHETIC_VERIFY_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=7bb0aeed73d9a3fd383ab24d07c56d8b9764e328b3f2da619d07e59cf9d66257; exit=0; EXPECT=matched; output-sha256=1d70979dda9d7b0ec62d1e9af130b5fba10511a6022fcef358de465dda5f7f94; output-bytes=147; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\vivek\EST\EST-Project; path=d6f435cc73e6/35 entries

- [x] G6: all 9 stage logs, JSON deltas, manifest, and changelog exist and reconcile
  CHECK: python -c "import json; from pathlib import Path; m=json.load(open('data/outputs/stage_logs/pipeline_run_manifest.json')); ids=[s['stage'] for s in m['stages']]; assert ids == [f'{i:02d}' for i in range(9)]; assert all(Path(s['log_file']).exists() and Path(s['json_file']).exists() for s in m['stages']); assert Path('data/outputs/stage_logs/STAGE_CHANGELOG.md').exists(); print('G6_STAGE_LOGS_OK')"
  EXPECT: G6_STAGE_LOGS_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=e2b47db32a8616dc06525e4b3e48ba5942ab6d192daefa8a139b5681e15e2562; exit=0; EXPECT=matched; output-sha256=09d1ae0068025d395cb7babc435ce9248f930de1fb916aa34a251447a75fed11; output-bytes=18; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\vivek\EST\EST-Project; path=d6f435cc73e6/35 entries

- [x] G7: all 7 final 300-dpi PNGs, Final HTML, and Final DOCX render without missing assets or JS errors
  CHECK: python 06_build_report.py --verify-only
  EXPECT: G7_REPORTS_VERIFIED_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=618778cc8ecc39248b1b1ee5e3563315f08259e50d9897e48dc6d3b715f92616; exit=0; EXPECT=matched; output-sha256=dd5e789b894be2d7b46549498c5a52d3a74e6988efa1976f2803c8172905e781; output-bytes=377; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\vivek\EST\EST-Project; path=d6f435cc73e6/35 entries
