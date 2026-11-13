"""Builds the publication-grade Final Project Report (DOCX + native PDF via Word COM)."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import config as C


NAVY = RGBColor(0x16, 0x2A, 0x45)
SLATE = RGBColor(0x33, 0x41, 0x55)
MUTED = RGBColor(0x52, 0x60, 0x71)


def _set_cell_shading(cell, hex_fill):
    cell._tc.get_or_add_tcPr().append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_fill}"/>'))


def _set_cell_margins(cell, top=90, bottom=90, left=130, right=130):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for side, val in (("top", top), ("bottom", bottom), ("left", left), ("right", right)):
        node = OxmlElement(f"w:{side}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def _set_row_cant_split(row):
    row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))


def _set_row_header(row):
    row._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))


def _add_page_number(run):
    for fld_type, text in (("begin", None), (None, " PAGE "), ("separate", None), ("end", None)):
        if fld_type:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), fld_type)
            run._r.append(el)
        else:
            it = OxmlElement("w:instrText")
            it.set(qn("xml:space"), "preserve")
            it.text = text
            run._r.append(it)


def _configure_doc(doc):
    for sec in doc.sections:
        sec.top_margin = Inches(0.75)
        sec.bottom_margin = Inches(0.75)
        sec.left_margin = Inches(0.75)
        sec.right_margin = Inches(0.75)
        sec.different_first_page_header_footer = True
        hp = sec.header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hr = hp.add_run("Team TBD2 · Final Project Report — Eastern North America Pollen Synthesis")
        hr.font.size = Pt(8.5)
        hr.font.color.rgb = MUTED
        fp = sec.footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        fr1 = fp.add_run("Late-Quaternary Climate–Vegetation Lags, No-Analogue Attribution & 2D Tree Migration   |   Page ")
        fr1.font.size = Pt(8.5)
        fr1.font.color.rgb = MUTED
        fr_pg = fp.add_run()
        fr_pg.font.size = Pt(8.5)
        fr_pg.font.color.rgb = MUTED
        _add_page_number(fr_pg)

    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
    normal.paragraph_format.line_spacing = 1.15
    normal.paragraph_format.space_after = Pt(5)


def _h(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    h.paragraph_format.keep_with_next = True
    h.paragraph_format.space_before = Pt(14 if level == 1 else 10)
    h.paragraph_format.space_after = Pt(4)
    for r in h.runs:
        r.font.name = "Calibri"
        r.font.color.rgb = NAVY if level == 1 else SLATE
        r.font.size = Pt({1: 14, 2: 12, 3: 10.5}.get(level, 10.5))
    return h


def _p(doc, text, bold_prefix=None, space_after=5):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    if bold_prefix:
        rb = p.add_run(bold_prefix)
        rb.bold = True
    p.add_run(text)
    return p


def _bullet(doc, lead, body):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(3)
    rb = p.add_run(lead)
    rb.bold = True
    p.add_run(body)
    return p


def _callout(doc, title, text, accent_hex="0072B2", fill_hex="F1F5F9"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    row = tbl.rows[0]
    _set_row_cant_split(row)
    cell = row.cells[0]
    cell.width = Inches(7.0)
    _set_cell_shading(cell, fill_hex)
    _set_cell_margins(cell, top=110, bottom=110, left=160, right=150)
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="none"/><w:right w:val="none"/><w:bottom w:val="none"/>'
        f'<w:left w:val="single" w:sz="24" w:space="0" w:color="{accent_hex}"/>'
        f'</w:tcBorders>'
    )
    cell._tc.get_or_add_tcPr().append(borders)
    cp = cell.paragraphs[0]
    cp.paragraph_format.space_after = Pt(2)
    rt = cp.add_run(title + "\n")
    rt.bold = True
    rt.font.size = Pt(10)
    rt.font.color.rgb = NAVY
    rb = cp.add_run(text)
    rb.font.size = Pt(9.5)
    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(3)


def _add_table(doc, df, caption=None):
    if caption:
        cp = doc.add_paragraph()
        cp.paragraph_format.keep_with_next = True
        cp.paragraph_format.space_before = Pt(6)
        cp.paragraph_format.space_after = Pt(2)
        r = cp.add_run(caption)
        r.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = SLATE
    tbl = doc.add_table(rows=1, cols=len(df.columns))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.style = "Table Grid"
    hdr = tbl.rows[0]
    _set_row_header(hdr)
    _set_row_cant_split(hdr)
    for j, col in enumerate(df.columns):
        c = hdr.cells[j]
        _set_cell_shading(c, "1E293B")
        _set_cell_margins(c, top=80, bottom=80, left=90, right=90)
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(str(col))
        run.bold = True
        run.font.size = Pt(8.5)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    for idx, (_, row_data) in enumerate(df.iterrows()):
        row = tbl.add_row()
        _set_row_cant_split(row)
        bg = "F8FAFC" if idx % 2 else "FFFFFF"
        for j, col in enumerate(df.columns):
            val = row_data[col]
            c = row.cells[j]
            _set_cell_shading(c, bg)
            _set_cell_margins(c, top=65, bottom=65, left=90, right=90)
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            if isinstance(val, (float, np.floating)):
                if np.isnan(val):
                    txt = "—"
                elif abs(val) < 0.01 and val != 0:
                    txt = f"{val:.2e}"
                elif col in ("Mid Sites", "Fin Sites", "Sites", "Sig (p<0.05)", "Mid Lag (yr)", "Final Lag (yr)", "Median Lag (yr)", "Lag Sig (yr)", "CI Low", "CI High", "Delta (yr)", "Mid n", "Fin n") or (abs(val) >= 100 and abs(val - round(val)) < 1e-6):
                    txt = f"{int(round(val))}"
                elif col in ("Sig (%)", "+r (%)", "Azimuth (°)"):
                    txt = f"{val:.1f}"
                else:
                    txt = f"{val:.2f}"
            else:
                txt = str(val)
            run = p.add_run(txt)
            run.font.size = Pt(8.5)
    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(4)


def _add_single_fig(doc, img_path, caption, width_in=6.5):
    if not img_path.exists():
        return
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.keep_with_next = True
    p_img.paragraph_format.space_before = Pt(4)
    p_img.paragraph_format.space_after = Pt(2)
    p_img.add_run().add_picture(str(img_path), width=Inches(width_in))

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_after = Pt(6)
    rc = p_cap.add_run(caption)
    rc.italic = True
    rc.font.size = Pt(9)
    rc.font.color.rgb = MUTED


def _add_mid_pair(doc, orig_path, mod_path, orig_label, mod_label, caption):
    tbl = doc.add_table(rows=2, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r in tbl.rows:
        _set_row_cant_split(r)
    no_borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        '<w:top w:val="none"/><w:left w:val="none"/><w:bottom w:val="none"/>'
        '<w:right w:val="none"/><w:insideH w:val="none"/><w:insideV w:val="none"/>'
        '</w:tblBorders>'
    )
    tbl._tbl.tblPr.append(no_borders)
    for col_idx, (lbl, path) in enumerate(((orig_label, orig_path), (mod_label, mod_path))):
        hc = tbl.cell(0, col_idx)
        _set_cell_margins(hc, top=30, bottom=20, left=40, right=40)
        hp = hc.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        hp.paragraph_format.space_after = Pt(0)
        hp.paragraph_format.keep_with_next = True
        hr = hp.add_run(lbl)
        hr.bold = True
        hr.font.size = Pt(8.5)
        hr.font.color.rgb = SLATE

        ic = tbl.cell(1, col_idx)
        _set_cell_margins(ic, top=20, bottom=30, left=40, right=40)
        ip = ic.paragraphs[0]
        ip.alignment = WD_ALIGN_PARAGRAPH.CENTER
        ip.paragraph_format.space_after = Pt(0)
        ip.paragraph_format.keep_with_next = True
        if path.exists():
            ip.add_run().add_picture(str(path), width=Inches(3.35))

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_after = Pt(5)
    rc = p_cap.add_run(caption)
    rc.italic = True
    rc.font.size = Pt(9)
    rc.font.color.rgb = MUTED


def _load_metrics():
    mid = C.OUT / "mid_project"
    return {
        "mid_sites": pd.read_csv(C.PROC / "sites.csv"),
        "fin_sites": pd.read_csv(C.PROC / "sites_final_2d.csv"),
        "mid_binned": pd.read_csv(C.PROC / "binned.csv"),
        "fin_binned": pd.read_csv(C.PROC / "binned_final_2d.csv"),
        "mod_raw": pd.read_csv(C.PROC / "modern.csv"),
        "mod_tr": pd.read_csv(C.PROC / "modern_trsh_only.csv"),
        "mod_fin": pd.read_csv(C.PROC / "modern_final_2d.csv"),
        "creg": pd.read_csv(C.PROC / "climate_regional.csv").sort_values("bin_age"),
        "grad": json.loads((C.PROC / "gradient.json").read_text()),
        "ls_mid": pd.read_csv(mid / "lag_summary_base.csv"),
        "ls_pin": pd.read_csv(mid / "lag_summary_pinus.csv"),
        "ls_j1": pd.read_csv(mid / "lag_summary_j1.csv"),
        "ls_fin": pd.read_csv(C.OUT / "lag_summary_final_2d.csv"),
        "lags_fin": pd.read_csv(C.OUT / "lags_final_2d.csv"),
        "ls_250": pd.read_csv(C.OUT / "lag_summary_bin250.csv"),
        "mig_mid": pd.read_csv(mid / "migration_base.csv"),
        "mig_fin": pd.read_csv(C.OUT / "migration_final_2d.csv"),
        "na_mid": pd.read_csv(mid / "noanalogue_vs_climate_base.csv"),
        "na_raw": pd.read_csv(C.OUT / "noanalogue_vs_climate_raw_celsius.csv"),
        "na_tr": pd.read_csv(C.OUT / "noanalogue_vs_climate_trsh_only.csv"),
        "na_rpp": pd.read_csv(C.OUT / "noanalogue_vs_climate_rpp.csv"),
        "na_fin": pd.read_csv(C.OUT / "noanalogue_vs_climate_final_2d.csv"),
        "na_rows_mid": pd.read_csv(mid / "no_analogue_base.csv"),
        "na_rows_fin": pd.read_csv(C.OUT / "no_analogue_final_2d.csv"),
        "drv_raw": pd.read_csv(C.OUT / "no_analogue_drivers_raw_celsius.csv"),
        "drv_fin": pd.read_csv(C.OUT / "no_analogue_drivers_final_2d.csv"),
        "roc_fin": pd.read_csv(C.OUT / "rate_of_change_final_2d.csv"),
        "tests_mid": json.loads((mid / "tests_base.json").read_text()),
        "tests_fin": json.loads((C.OUT / "tests_final_2d.json").read_text()),
        "vel_mid": json.loads((mid / "velocity_comparison_base.json").read_text()),
        "vel_fin": json.loads((C.OUT / "velocity_comparison_final_2d.json").read_text()),
        "ens": json.loads((C.OUT / "ensemble_summary_legacyage.json").read_text()),
        "manifest": json.loads((C.STAGE_LOGS / "pipeline_run_manifest.json").read_text()),
        "audit_fin": json.loads((C.STAGE_LOGS / "audit_final_2d.json").read_text()),
        "audit_250": json.loads((C.STAGE_LOGS / "audit_bin250.json").read_text()),
        "la_audit": pd.read_csv(C.STAGE_LOGS / "legacyage_match_audit.csv"),
    }


def _export_pdf(docx_path, pdf_path):
    import win32com.client
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    doc_com = None
    try:
        doc_com = word.Documents.Open(str(docx_path.resolve()), ReadOnly=True)
        doc_com.SaveAs2(str(pdf_path.resolve()), FileFormat=17)  # 17 = wdFormatPDF
    finally:
        if doc_com is not None:
            doc_com.Close(False)
        word.Quit()


def build_final_report_docx_and_pdf():
    m = _load_metrics()
    doc = docx.Document()
    _configure_doc(doc)

    mid_dir = C.OUT / "mid_project"
    mid_orig = mid_dir / "figures"
    mid_mod = mid_dir / "figures_modern"
    fin_fig = C.OUT / "figures_final"

    creg = m["creg"]
    vel_m, vel_f = m["vel_mid"], m["vel_fin"]
    tests_m, tests_f = m["tests_mid"], m["tests_fin"]
    ens = m["ens"]
    na500_mid = float(m["na_mid"].loc[m["na_mid"].bin_age == 500, "frac_no_analogue"].iloc[0]) * 100
    na500_tr = float(m["na_tr"].loc[m["na_tr"].bin_age == 500, "frac_no_analogue"].iloc[0]) * 100
    na500_rpp = float(m["na_rpp"].loc[m["na_rpp"].bin_age == 500, "frac_no_analogue"].iloc[0]) * 100
    na500_fin = float(m["na_fin"].loc[m["na_fin"].bin_age == 500, "frac_no_analogue"].iloc[0]) * 100
    eb_rate = float((m["lags_fin"].p_ebisuzaki < 0.05).mean()) * 100
    n_sig_pairs = int((m["lags_fin"].p_ebisuzaki < 0.05).sum())
    mig2d_med = vel_f["median_genus_migration_2d_m_per_yr"]
    deficit_fin = vel_f["modern_climate_velocity_m_per_yr"] / mig2d_med
    deficit_mid = vel_m["modern_climate_velocity_m_per_yr"] / vel_m["median_genus_migration_m_per_yr"]

    # --- Title Banner ---
    tp = doc.add_paragraph()
    tp.paragraph_format.space_before = Pt(4)
    tp.paragraph_format.space_after = Pt(4)
    r_title = tp.add_run(
        "Did Forests Keep Pace When the Ice Age Ended? Climate–Vegetation Lags, "
        "No-Analogue Forests, and 2D Tree Migration in Eastern North America"
    )
    r_title.bold = True
    r_title.font.size = Pt(18)
    r_title.font.color.rgb = NAVY

    sub = doc.add_paragraph()
    sub.paragraph_format.space_after = Pt(8)
    r_sub = sub.add_run(
        "Final Project Report · Team TBD2 (Project 25): Vivek R, Nandan Rajesh Kamat, Shaurya Gupta · 11 November 2026"
    )
    r_sub.font.size = Pt(10)
    r_sub.font.color.rgb = MUTED

    _callout(
        doc,
        "Abstract — Plain-English Overview",
        f"When the last Ice Age ended around 15,000 years ago, eastern North America warmed by more than 15 °C and forest habitats shifted hundreds of kilometers north. Fossil pollen trapped layer by layer in ancient lake mud lets us watch that real-world experiment unfold and ask whether trees move fast enough when climate changes rapidly.\n\n"
        f"This report tells the complete scientific and engineering story of our project—first explaining how we built and interpreted our Mid-Evaluation Baseline ({len(m['mid_sites'])} lakes, {len(m['mid_binned']):,} time slices), then walking through the five hidden flaws our post-midterm audit uncovered, and finally presenting our fully upgraded Final Methodology ({len(m['fin_sites'])} lakes, {len(m['fin_binned']):,} time slices).\n\n"
        f"After fixing climate unit errors and adding precipitation ({creg.temp_c.min():.2f} to +{creg.temp_c.max():.2f} °C; {creg.precip_mm_day.min():.2f}–{creg.precip_mm_day.max():.2f} mm/day), removing post-settlement agricultural weeds (cutting the 500 BP no-analogue floor fourfold from {na500_mid:.1f}% down to {na500_fin:.1f}%), detrending time series with 1,000 Ebisuzaki autocorrelation checks ({eb_rate:.1f}% pairs p < 0.05), applying REVEALS pollen-productivity calibration, adopting LegacyAge 1.0 radiocarbon chronologies ({ens['matched_sites']}/{ens['total_sites']} sites), and mapping 2D arrival surfaces: (1) tree genera genuinely lag climate at distinct speeds (Kruskal–Wallis H = {tests_f['kruskal_H']:.2f}, p = {tests_f['kruskal_p']:.5f}; median 1,500 yr), (2) true late-glacial no-analogue forests (peaking at {m['na_fin'].frac_no_analogue.max()*100:.1f}% at 14.5 ka BP) track forest turnover (rho = {tests_f['spearman_noanalogue_vs_veg_rate'][0]:.3f}, Ebisuzaki p = {tests_f['ebisuzaki_p_veg']:.3f}), and (3) 2D migration uncovers diagonal corridors missed at Mid Evaluations (such as Alnus moving WNW at 264.6 m/yr and Carya ENE at 277.0 m/yr), yet the median forest spread of {mig2d_med:.1f} m/yr still trails today's climate velocity ({vel_f['modern_climate_velocity_m_per_yr']:.0f} m/yr) by {deficit_fin:.1f}×.",
        accent_hex="162A45",
        fill_hex="F8FAFC",
    )

    # --- 1. Introduction ---
    _h(doc, "1. Introduction: The Story Behind the Research Questions")
    _p(
        doc,
        "Imagine trying to outrun a rising ocean tide when your family can only take one step each time a child grows up and drops seeds a few hundred meters away. That is the exact challenge wild forests face whenever Earth's climate shifts rapidly. Over the past 15,000 years (15 ka BP to the present), eastern North America experienced one of the most dramatic warming transitions in recent geological history. As the giant Laurentide Ice Sheet melted back into Canada, climate did not warm in a gentle, straight line. Instead, temperatures jumped sharply during the Bølling–Allerød (~14.7–12.9 ka BP), snapped back into an abrupt freeze during the Younger Dryas (~12.9–11.7 ka BP), warmed steeply into the early Holocene, and dipped briefly again at the 8.2 ka BP cooling event.",
    )
    _p(
        doc,
        "Lakes across the continent recorded those upheavals automatically. Every spring, wind and insects swept tree pollen onto lake surfaces, where grains sank into layered bottom mud. By counting ancient pollen grains core-by-core and pairing them with simulated paleoclimate trajectories from TraCE-21ka, we set out to answer three linked questions identified as open gaps in our literature review:",
    )
    _bullet(doc, "RQ1 — Climate Response Lags: ", "How many centuries do major tree genera lag behind temperature change, and do fast pioneers react sooner than slow, shade-tolerant hardwoods?")
    _bullet(doc, "RQ2 — No-Analogue Communities: ", "Did unfamiliar, extinct forest mixes ('no-analogue communities') emerge specifically during moments of rapid climate change and heavy vegetation turnover?")
    _bullet(doc, "RQ3 — The Migration Velocity Race: ", "Did trees spread fast enough across eastern North America after the Ice Age to keep pace with shifting temperature zones—and how do those natural speeds compare with modern warming?")
    _p(
        doc,
        "Rather than treating our initial pipeline as a finished answer, we designed this project in two transparent acts: first freezing a clean Mid-Evaluation Baseline so every original finding could be scrutinized, and then running a stage-by-stage diagnostic upgrade in which every change was isolated, measured, and compared directly against the Mid-Evaluation snapshot.",
    )

    # --- 2. Study Region & Data ---
    _h(doc, "2. Study Region & Datasets")
    _p(
        doc,
        "We restricted our study region to eastern North America between longitude -100° and -60° E and latitude 34° and 52° N. West of -100° lies dry prairie with few deep, continuous lakes; north of 52° stayed buried under glacial ice far into the Holocene. Within this window sits the densest network of continuous fossil pollen records on Earth, spanning southern refugia through the Appalachian corridor and Great Lakes into New England and Atlantic Canada.",
    )
    _bullet(doc, "Neotoma Fossil Pollen Cores: ", f"{m['audit_fin']['fossil_audit']['raw_datasets']} raw fossil datasets ({m['audit_fin']['fossil_audit']['raw_rows']:,} datum rows), with {m['audit_fin']['fossil_audit']['inside_bbox_datasets']} inside our bounding box.")
    _bullet(doc, "Neotoma Modern Surface Reference Samples: ", f"{m['audit_fin']['modern_audit']['raw_datasets']:,} cached modern surface-mud samples ({m['audit_fin']['modern_audit']['raw_rows']:,} rows), of which {m['audit_fin']['modern_audit']['inside_bbox_datasets']} lie inside our bounding box and represent what forests look like today.")
    _bullet(doc, "TraCE-21ka Transient Paleoclimate Simulation (NCAR d651050): ", "Because weather stations did not exist 12,000 years ago, we extracted decadal-average surface temperature (TREFHT) and—in the Final analysis—total precipitation (PRECT) at the nearest climate grid cell for every site.")
    _bullet(doc, "Focal Genera Grouping: ", "Individual lake counts list hundreds of rare herbs and shrubs that would inject noise into multi-site statistical tests. Following regional paleoecological standards, we aggregated taxa into 14 dominant tree/shrub genera (Picea, Abies, Larix, Pinus, Tsuga, Betula, Quercus, Fagus, Fraxinus, Ulmus, Carya, Acer, Alnus, Populus) plus a catch-all 'Other' group.")

    tbl_data = pd.DataFrame([
        {"Dataset Stage": "Raw Neotoma Cache", "Sites / Cores": "423 fossil / 1,240 modern", "Samples / Rows": "742,380 fossil rows · 24,148 modern rows", "Role": "Continent-wide pollen archive prior to regional & continuity filters"},
        {"Dataset Stage": "Mid-Eval Filtered (TRSH+UPHE)", "Sites / Cores": f"{len(m['mid_sites'])} sites / {len(m['mod_raw'])} modern", "Samples / Rows": f"{len(m['mid_binned']):,} 500-yr bins", "Role": "Frozen initial baseline preserving original Kelvin & weed inputs"},
        {"Dataset Stage": "Final Filtered (TRSH-only + LegacyAge)", "Sites / Cores": f"{len(m['fin_sites'])} sites / {len(m['mod_fin'])} modern", "Samples / Rows": f"{len(m['fin_binned']):,} 500-yr bins", "Role": "Weeds excluded, RPP-calibrated counts, harmonized Bayesian ages"},
        {"Dataset Stage": "High-Res Sensitivity (250-yr Bins)", "Sites / Cores": f"{m['audit_250']['sites_retained']} sites / {len(m['mod_fin'])} modern", "Samples / Rows": f"{m['audit_250']['binned_rows']:,} 250-yr bins", "Role": "Tests whether 500-yr smoothing alters genus lag rankings"},
    ])
    _add_table(doc, tbl_data, "Table 1. Data inventory across Mid-Evaluation Baseline and Final upgraded pipelines.")

    # --- 3. Act I: Mid-Evaluation Pipeline ---
    _h(doc, "3. Act I — Mid-Evaluation Pipeline: Initial Decisions & Rationale")
    _p(
        doc,
        "During the first half of the project, our priority was clarity and end-to-end verification: pick established textbook paleoecological metrics, filter messy sediment records cleanly, and make sure every number could be reproduced in minutes.",
    )
    _h(doc, "3.1 Core Preprocessing & Metric Choices at Mid Evaluations", level=2)
    _bullet(doc, "Why 500-Year Uniform Bins (15,000 → 0 BP): ", "Different lakes were sampled at irregular depth intervals. Grouping samples into 500-year windows puts all cores onto one synchronized clock (30 bins centered at 14,750, 14,250, ..., 250 BP) and pools grain counts to steady noisy percentages.")
    _bullet(doc, "Why Strict Quality Floors (MIN_GRAINS = 100, MIN_BINS = 12, MAX_GAP = 4): ", "Counting too few grains per mud slice causes percentages to swing randomly; requiring ≥100 grains per bin, ≥12 occupied bins per core, and no continuous gap wider than 2,000 years kept 72 reliable lake sequences.")
    _bullet(doc, "Crucial Mid-Eval Fix (Retaining Blank-Age Modern Samples): ", "Modern surface-mud samples naturally lack radiocarbon age models (their age column is blank). Early filtering accidentally threw them out until we corrected the modern loader to keep blank-age surface samples, unlocking 644 reference forests.")
    _bullet(doc, "Hellinger Distance for Forest Turnover: ", "Comparing raw percentage differences exaggerates dominant pines and ignores shifts in rare hardwoods. Hellinger distance takes the square root of each taxon's proportion first, making turnover equally sensitive across abundant and mid-tier trees.")
    _bullet(doc, "Squared Chord Distance (SCD) for No-Analogue Status: ", "SCD is the standard measure of fossil-to-modern mismatch. First, we measured every modern lake's distance to its single closest modern neighbor and set our 'no-analogue' alarm at the 95th percentile (0.06587 at Mid Evals). Any ancient bin farther from all 644 modern samples than that threshold was flagged as having no modern analogue.")
    _bullet(doc, "Shifted Level Correlations for Lags & 1D Northward Migration: ", "For each genus averaging ≥2% at a lake, we tested time shifts k = 0..6 bins (0–3,000 years) against site temperature and picked the lag maximizing |r| (absolute value, so cooling-adapted Picea shrinking as climate warms counts just like heat-loving Quercus expanding). For migration, we marked genus 'arrival' at the first bin reaching ≥5% pollen for two consecutive bins (ignoring southern sites already ≥5% at the start) and regressed arrival age against straight-North distance across ≥8 sites.")
    _bullet(doc, "Early Sensitivity Spot-Checks (_pinus and _j1): ", "Before Mid Evaluations, we ran two quick sanity probes: halving pine pollen (_pinus, multiplier 0.5) and adding one random 5% age-jitter draw (_j1). Median lags and the modern speed deficit held up overall, yet subtle cracks appeared—under _j1, Fagus migration collapsed to non-significance (p = 0.128) and Abies lost too many sites to estimate.")

    # --- 3.2 All 5 Mid-Eval Visualisations ---
    _h(doc, "3.2 Mid-Evaluation Visualizations: Design Choices & What They Revealed", level=2)
    _p(
        doc,
        "Because raw numbers alone do not expose spatial blind spots or statistical traps, we froze all Mid-Evaluation results cleanly and built an interactive baseline dashboard alongside five paired figures—showing our original Mid-Eval renders on the left and redesigned baseline renders (using Natural Earth maps and log scales) on the right without modifying the underlying Mid-Eval data.",
    )

    # Mid Fig 1
    _add_mid_pair(
        doc,
        mid_orig / "fig1_sites.png",
        mid_mod / "fig1_sites.png",
        "Original Mid-Eval Render",
        "Modernized Baseline Render",
        "Mid Figure 1. Study lake network across eastern North America (n = 72 sites, 1,782 bins).",
    )
    _p(doc, "Putting all 72 retained sites onto coordinates lets readers judge regional representativeness before interpreting continental averages. The original white-box scatter plot showed dots without geography, so we added Natural Earth coastlines, the Great Lakes, state borders, and a Viridis color bar showing how many 500-year bins each core covered (12–30).", bold_prefix="Why chosen & improved: ")
    _p(doc, "Sampling is densest around the Great Lakes (42°–48° N) and New England (40°–45° N), leaving the Southeast (34°–38° N) relatively thin. Yellow-green markers (26–30 occupied bins) follow southern Wisconsin, Ohio, and coastal New England where lakes stayed ice-free all 15,000 years, whereas darker purple dots (13–17 bins) trace northern cores whose basins opened only after glacier retreat.", bold_prefix="Detailed Inference: ")

    # Mid Fig 2
    _add_mid_pair(
        doc,
        mid_orig / "fig2_rates.png",
        mid_mod / "fig2_rates.png",
        "Original Mid-Eval Render",
        "Modernized Baseline Render",
        "Mid Figure 2. Regional TraCE warming rate (°C/century) and Hellinger vegetation turnover.",
    )
    _p(doc, "Stacking climate speed above vegetation turnover along a reversed 15 → 0 ka BP timeline lets us check visually whether sudden climate jolts triggered forest shakeups. In the modernized baseline, we added the underlying TraCE temperature curve on top (explicitly labeled '[disp. K-273.15]' to record that the underlying CSV still held Kelvin) and shaded three abrupt climate events: Bølling–Allerød, Younger Dryas, and 8.2 ka.", bold_prefix="Why chosen & improved: ")
    _p(doc, "Two sharp fast-warming pulses exceed 0.36–0.41 °C/century—early deglaciation (14.5–13.5 ka) and the exit from the Younger Dryas freeze (12.0 ka, 0.40 °C/century)—followed by a smaller 0.21 °C/century jump near 8.0 ka and a quiet Holocene (median = 0.034 °C/century). Meanwhile, baseline forest turnover peaks at 0.0407 Hellinger/century at 11.5 ka (half a step after the 12.0 ka jolt) and drops to ~0.020–0.023 in mid-Holocene. Crucially, notice the suspicious upward hook at the far right edge (1.0 → 0.5 ka, rising to 0.0273) even though climate was flat—our earliest clue that modern weeds were distorting recent samples.", bold_prefix="Detailed Inference: ")

    # Mid Fig 3
    _add_mid_pair(
        doc,
        mid_orig / "fig3_lags.png",
        mid_mod / "fig3_lags.png",
        "Original Mid-Eval Render",
        "Modernized Baseline Render",
        "Mid Figure 3. Genus-level raw cross-correlation lags ranked shortest to longest (RQ1).",
    )
    _p(doc, "Ranking all 12 qualifying genera horizontally gives a fast visual test of RQ1's unequal-response hypothesis. Replacing heavy solid bars with clean dot-and-CI whiskers plus (n=...) site counts stops tiny samples like Abies (n=5) from looking visually identical to dense genera like Pinus (n=72).", bold_prefix="Why chosen & improved: ")
    _p(doc, "At Mid Evaluations, genera separated strongly (Kruskal–Wallis H = 58.63, p = 1.66e-8): Picea and Tsuga showed rapid 500-year median lags, Quercus and Betula sat at 1,000 yr, Acer/Fraxinus/Ulmus at 1,500 yr, Abies/Alnus at 2,000 yr, Pinus at 2,250 yr, Carya at 2,500 yr, and Fagus slowest at 3,000 yr. However, Tsuga sitting beside Picea at 500 yr raised an ecological red flag—hemlock is a slow, shade-loving tree, hinting that correlating raw upward trends over 15,000 years was faking fast agreement.", bold_prefix="Detailed Inference: ")

    # Mid Fig 4
    _add_mid_pair(
        doc,
        mid_orig / "fig4_noanalogue.png",
        mid_mod / "fig4_noanalogue.png",
        "Original Mid-Eval Render",
        "Modernized Baseline Render",
        "Mid Figure 4. Mid-Evaluation no-analogue prevalence (%) vs. absolute climate rate (RQ2).",
    )
    _p(doc, "Pairing no-analogue bars against an overlaid |climate rate| curve directly tests RQ2. In the modernized baseline, we preserved the raw TRSH+UPHE numbers untouched and explicitly highlighted the '500 BP weed floor: 33.1%' callout to spotlight the post-midterm bug diagnosis.", bold_prefix="Why chosen & improved: ")
    _p(doc, "Alien forest prevalence peaks at 81.1% at 12.0 ka BP and correlates strongly with both climate speed (Spearman rho = 0.661) and vegetation turnover (rho = 0.809). Yet look closely at the right half of the chart: between 6.0 and 0.5 ka BP, when Holocene climate barely moved, 45%–58% of samples still look 'no-analogue,' and even 500 BP forests (right before modern times) sit at an implausible 33.1% mismatch! Forests 500 years ago were not alien—our modern yardstick was contaminated.", bold_prefix="Detailed Inference: ")

    # Mid Fig 5
    _add_mid_pair(
        doc,
        mid_orig / "fig5_migration.png",
        mid_mod / "fig5_migration.png",
        "Original Mid-Eval Render",
        "Modernized Baseline Render",
        "Mid Figure 5. 1D northward migration speed vs. past and modern climate-zone velocity (RQ3).",
    )
    _p(doc, "Plotting tree dispersal speeds right beside vertical reference lines for climate velocity gives an instant visual verdict on RQ3. In the original linear chart, placing modern velocity at 1,572 m/yr compressed all five genera into a cramped strip on the left; switching to a logarithmic scale lets readers inspect both 59 m/yr Abies and 1,572 m/yr modern climate side by side.", bold_prefix="Why chosen & improved: ")
    _p(doc, f"Only 5 of 14 genera passed straight-North regression (Quercus 284.5, Fagus 218.3, Carya 164.7, Tsuga 108.5, Abies 59.4 m/yr; median 164.7 m/yr). Every genus median fell short of Past p95 climate velocity (331.8 m/yr) and sat nearly an order of magnitude behind Modern climate velocity ({vel_m['modern_climate_velocity_m_per_yr']:.1f} m/yr = {deficit_mid:.1f}× deficit). Still, losing 9 genera—including prominent trees like Pinus and Alnus—hinted that forcing straight-North lines ignored sideways postglacial routes.", bold_prefix="Detailed Inference: ")

    _p(
        doc,
        "In addition to these static figures, our frozen baseline interactive HTML report bundled four interactive Plotly widgets—an inspectable TraCE Temperature Curve (with Kelvin-to-Celsius hover inspection), an interactive Mid Raw Lags bar chart, a hoverable No-Analogue vs. |Climate Rate| overlay, and a log-scale 1D Migration bar chart—allowing exact bin-by-bin hovering over the Younger Dryas plateau and the 33.1% 500 BP shelf.",
        bold_prefix="Mid-Baseline Interactive Plotly Views: ",
    )

    # --- 4. The Detective Audit ---
    _h(doc, "4. Forensic Audit: Five Scientific Cracks Uncovered After Mid Evaluations")
    _p(
        doc,
        "Freezing the Mid-Evaluation snapshot allowed us to question every assumption systematically. Diagnosing why unexpected anomalies appeared in those five figures uncovered five concrete flaws:",
    )
    _bullet(doc, "Crack #1 — Kelvin in Climate CSVs, Seasonal File Mixing & Missing Rain: ", "Inspecting climate_regional.csv (min 262.88, max 278.41) proved temperatures were stored in Kelvin rather than Celsius, and worse, the TraCE file glob (*.nc) mixed seasonal DJF/JJA/MAM/SON averages into annual files. Meanwhile, moisture (PRECT precipitation) was completely absent.")
    _bullet(doc, "Crack #2 — The 33.1% Agricultural Weed Mirage (UPHE): ", "Why did 500 BP pre-colonial forests diverge from modern lakes? Modern surface samples sit in landscapes heavily cleared for farms and roads, where ragweed, grasses, and other upland herbs ('UPHE') flood the 'Other' bucket (averaging 31.66% in raw modern.csv vs. only 10.31% once UPHE is stripped). Matching pre-colonial tree canopies against plowed-field weed percentages created fake dissimilarity and crushed the modern SCD threshold artificially low (0.06587).")
    _bullet(doc, "Crack #3 — The 'Two Smooth Lines' Autocorrelation Illusion: ", "Correlating raw pollen proportions with raw warming temperatures over 15,000 years violates independence assumptions because both series drift monotonically upward or downward. That inflated significance (flagging 66%–68% of raw site pairs as 'p < 0.05') and let Tsuga fake a 500-yr lag.")
    _bullet(doc, "Crack #4 — The Pine Megaphone Problem (Uncalibrated Pollen Counts): ", "One wind-pollinated pine tree releases ~14.1× more pollen relative to grass than one insect-pollinated maple (Acer, ~0.23×). Multiplying Pinus by an arbitrary 0.5 left birch (6.19×), fir (6.88×), and silent maples badly distorted.")
    _bullet(doc, "Crack #5 — Northward-Only Migration & Unchecked Core Clocks: ", "Mountains and the Great Lakes funnel spreading trees East-Northeast or Northwest. Straight-North OLS discarded real migrants like Alnus and Carya, while single default Neotoma age models needed independent LegacyAge 1.0 Bayesian radiocarbon calibration and uncertainty ensembles.")

    # --- 5. Act II: Final Methodology & Stage-by-Stage Improvements ---
    _h(doc, "5. Act II — Final Methodology: Stage-by-Stage Engineering & Ablation Audit")
    _p(
        doc,
        "Rather than changing five things simultaneously and guessing which fix moved which result, we built an automated audit framework (stage_log.py) executing Stages 00 through 08 sequentially—freezing intermediate tagged outputs at every step so every single improvement can be inspected on its own merits.",
    )
    _bullet(doc, "Stage 00–01 (mid_project — Frozen Archive): ", "Backed up all Mid-Eval outputs and built TBD2_MidProject_Baseline_Report.html with transparent Kelvin display and weed-floor warnings.")
    _bullet(doc, "Stage 02 (raw_celsius — Verified Annual °C & PRECT Download): ", f"Restricted climate extraction strictly to annual NetCDFs (*decavg_400BCE.nc), enforced physical Celsius bounds (-10.27 to +5.26 °C), and downloaded TraCE PRECT rainfall (40.7 MB; 2.22–2.49 mm/day, mean 2.403 mm/day). Fixing the seasonal-file glob shifted individual raw lags slightly (Betula +500 yr, Picea +250 yr, Pinus/Quercus -250 yr) and measured the baseline Ebisuzaki false pass rate on raw curves at 65.87% (305/463 pairs).")
    _bullet(doc, "Stage 03 (trsh_only — Filtering Out UPHE Agricultural Herbs): ", "Added --trsh-only preprocessing keeping woody trees and shrubs before applying the 100-grain threshold. Four herb-dominated prairie/edge cores dropped out (72 → 68 sites, 1,686 bins), modern 'Other' pollen plummeted from 31.66% to 10.31%, and the 500 BP no-analogue floor immediately cut in half from 33.14% to 15.56% (-17.58 percentage points). We also added per-taxon SCD attribution, proving UPHE herbs accounted for ~60% of the late-Holocene 'Other' mismatch (0.0119 → 0.0047 at 750 BP).")
    _bullet(doc, "Stage 04 (diff_ebisuzaki — First-Differencing & 1,000 Phase-Randomizations): ", "Replaced raw curve correlation with bin-to-bin first differences (np.diff on regularized chronological grids so interior gaps remain NaN). Now a genus tracks climate only when a warming/cooling jolt aligns with a forest change jolt k bins later. Each site pair was then tested against 1,000 Ebisuzaki (1997) FFT phase-randomized surrogates that scramble timing while preserving identical autocorrelation structure. Result: false-positive pass rate fell sharply from 68.14% to 40.13% (-138 pairs), and Tsuga jumped from a fake 500 yr to 2,500 yr (+2,000 yr), while cross-genus lag differences stayed strongly significant.")
    _bullet(doc, "Stage 05 (rpp — Empirical REVEALS Relative Pollen Productivity): ", "Replaced the uncalibrated 0.5 pine tweak with consensus empirical RPP divisors from Wieczorek & Herzschuh (2020) and Dawson et al. (2016) (Pinus ÷ 14.10, Abies ÷ 6.88, Betula ÷ 6.19, Picea ÷ 2.80, Alnus ÷ 2.70, Fraxinus ÷ 2.42, Fagus ÷ 2.35, Ulmus ÷ 2.24, Quercus ÷ 2.08, Tsuga ÷ 1.60, Larix ÷ 1.24, Carya ÷ 1.00, Populus ÷ 0.67, Acer ÷ 0.23). In modern lakes, over-represented Pinus fell from 21.01% to 4.85% while under-represented maple (Acer) rose nearly 9× from 1.99% to 17.06%, unlocking +54 qualifying site pairs and dropping the 500 BP no-analogue floor further to 8.89%.")
    _bullet(doc, "Stage 06 (legacyage & bin250 — Harmonized Clocks, N=50 Ensemble & 250-yr Check): ", f"Fetched Li et al. (2022) LegacyAge 1.0 radiocarbon chronologies from PANGAEA (Table-S5, 55,821 calibrated depth rows), directly matching 68/85 inside-bbox datasets and {ens['matched_sites']}/{ens['total_sites']} final retained sites (with depth-scaled uncertainty fallback logged transparently for the remaining {ens['total_sites']-ens['matched_sites']} sites). Tighter LegacyAge models closed interior core gaps cleanly, recovering site 312 (bringing the final set to 69 sites / 1,706 bins), lowering 500 BP no-analogue further to {na500_fin:.2f}%, and bringing Ebisuzaki pass rate to {eb_rate:.1f}% ({n_sig_pairs}/523 pairs). Running a 50-draw Monte Carlo chronological ensemble held median lag completely stable at {ens['ensemble_median_lag_yr']:.0f} yr (IQR {ens['ensemble_lag_iqr_yr']}), and halving bins to 250 yr ({m['audit_250']['sites_retained']} sites, {m['audit_250']['binned_rows']:,} bins) preserved the identical fast-to-slow taxonomic order.")
    _bullet(doc, "Stage 07–08 (final_2d & final_reports — 2D Migration Surfaces & Comparison Synthesis): ", "Projected arrival coordinates onto a local equal-area tangent plane (km), applied a 2D planar F-test (p_2d ≤ 0.05) to suppress noisy flat surfaces, fit smooth thin-plate splines (RBFInterpolator) clipped strictly inside each genus's Delaunay convex hull, extracted spatial speeds 1/|∇age| and compass directions, and rendered all final 300-dpi Okabe–Ito figures alongside self-contained HTML and Word/PDF reports.")

    stage_rows = []
    for s in m["manifest"]["stages"]:
        km = s.get("key_metrics", {})
        stage_rows.append({
            "Stage": f"{s['stage']} · {s['name']}",
            "Tag": s.get("tag", ""),
            "Sites / Bins": f"{km.get('n_sites', '—')} / {km.get('n_binned', '—')}",
            "500 BP NA (%)": f"{km['no_analogue_500bp_floor']*100:.1f}%" if km.get("no_analogue_500bp_floor") is not None else "—",
            "Eb. p<0.05": f"{km['ebisuzaki_pass_rate_p05']*100:.1f}%" if km.get("ebisuzaki_pass_rate_p05") is not None else "—",
            "Med. Lag (yr)": f"{km['median_across_genera_lag_yr']:.0f}" if km.get("median_across_genera_lag_yr") is not None else "—",
            "Mig. (m/yr)": f"{km['median_migration_m_per_yr']:.1f}" if km.get("median_migration_m_per_yr") is not None else "—",
        })
    _add_table(doc, pd.DataFrame(stage_rows), "Table 2. Stage 00–08 incremental ablation log documenting how each fix shifted key metrics.")

    # --- 6. Final Results & Visual Inferences ---
    _h(doc, "6. Final Results & Detailed Inferences Across Every Visualization")
    _p(
        doc,
        "Below we walk through every Final figure (Figures 1–5b) plus the four Final interactive HTML visualizations, explaining why each visual encoding was selected and every major ecological pattern visible in the results.",
    )

    # Final Fig 1
    _h(doc, "6.1 Spatial Network & Chronology Coverage (Final Figure 1)", level=2)
    _add_single_fig(
        doc,
        fin_fig / "fig1_spatial_overview.png",
        "Final Figure 1. Study corridor across Eastern North America (69 retained sites, 1,706 bins) showing LegacyAge 1.0 sites (blue, n=57), Neotoma fallback sites (amber, n=12), and TRSH-only drops (red ×, n=4).",
        width_in=5.6,
    )
    _p(doc, "Focusing cleanly on a single geographic basemap with color-coded chronology markers immediately highlights regional sampling balance across the Midwest, Great Lakes, New England, and Southeast, as well as which four marginal cores dropped when agricultural herbs were excluded.", bold_prefix="Why this visualization was chosen: ")
    _p(doc, "Dropping UPHE weeds removed only 4 marginal cores—mostly on western grasslands or the Atlantic margin—while 57 of 69 retained lakes (82.6%) sit on upgraded LegacyAge 1.0 Bayesian clocks evenly distributed alongside 12 Neotoma fallback sites across the Midwest, Great Lakes (n=44 at ≥42° N), and southern states (n=25 below 42° N), spanning 1,706 occupied 500-year bins.", bold_prefix="Detailed Inferences: ")

    # Final Fig 2
    _h(doc, "6.2 Verified Climate, Moisture Dynamics & Turnover Timing (Final Figure 2)", level=2)
    _add_single_fig(
        doc,
        fin_fig / "fig2_climate_turnover_events.png",
        "Final Figure 2. Verified TraCE-21ka annual temperature (°C) and precipitation (mm/day), thermal warming rate (°C/century), and Mid vs. Final median turnover (with IQR ribbon) across abrupt climate events.",
    )
    _p(doc, "Putting temperature (°C), rainfall (mm/day), warming speed, and both the Mid and Final turnover curves on one aligned timeline exposes two vital improvements at a glance: how moisture lagged warmth during early deglaciation, and how REVEALS RPP + LegacyAge sharpened real forest responses.", bold_prefix="Why this visualization was chosen: ")
    _p(doc, f"In the top panel, warming climbs rapidly from -10.27 °C toward -3.3 °C across the Bølling–Allerød, stalls across the Younger Dryas freeze, and stabilizes near +5.0 to +5.26 °C by 6 ka. By contrast, dashed blue rainfall (PRECT) stayed relatively dry (2.22–2.24 mm/day) until after 11.7 ka before rising smoothly to ~2.49 mm/day in mid-Holocene. In the bottom panel, stripping heavy pine pollen distortion shifted median forest turnover from Mid's delayed 0.0407 peak (11.5 ka) directly onto the 12.0 ka Younger Dryas warming snap (0.0545 Hellinger/century, overall median {m['roc_fin'].rate_per_century.median():.4f} vs. Mid 0.0250), while completely erasing Mid Eval's false 500 BP uptick.", bold_prefix="Detailed Inferences: ")

    # Final Fig 3a & 3b
    _h(doc, "6.3 Stationary Genus Lags, Response Polarity (+r/−r) & Mid-vs-Final Shift (RQ1: Figures 3a & 3b)", level=2)
    _add_single_fig(
        doc,
        fin_fig / "fig3a_lags_raincloud.png",
        "Final Figure 3a. Two-panel synthesis of postglacial forest lag dynamics: (A) Response delay (Median ± 95% bootstrap CI) across three ecological speed tiers, paired with (B) 100% horizontal stacked bars showing fossil site response polarity (% cores cold-retreating −r vs. warm-expanding +r, with filled segments denoting Ebisuzaki p < 0.05 significance).",
    )
    _p(doc, "A single distribution or bar obscures whether trees expanded or collapsed during warming. A dual-panel linked visualization immediately resolves this: Panel A tracks response delay (the biological clock across fast pioneer, canopy reorganization, and late climax stages), while Panel B displays the biological reaction (100% horizontal stacked bar of cold-retreating -r vs. warm-expanding +r sites, with verified Ebisuzaki autocorrelation significance). This separates time from direction, making complex continental responses intuitive at a glance.", bold_prefix="Why Figure 3a was chosen: ")
    _p(doc, f"Even after stripping 15,000-year shared trends via first-differencing and testing against 1,000 Ebisuzaki surrogates, {n_sig_pairs} of 523 site pairs ({eb_rate:.1f}%: 103 +r warm-tracking and 147 −r cold-tracking) pass p < 0.05, and differences among genera remain statistically robust (Kruskal–Wallis H = {tests_f['kruskal_H']:.2f}, p = {tests_f['kruskal_p']:.5f}; pairwise Bonferroni Picea vs. Tsuga p = 0.0127, Picea vs. Fagus p = 0.0462). Panel A reveals three distinct ecological speed tiers: pioneer conifer Larix leads with the shortest median lag (750 yr, 80.0% sig), nine canopy reorganization taxa cluster at 1,500 yr, and shade-tolerant climax dominants Fagus and Tsuga trail slowest at 2,500 yr. Crucially, Panel B demonstrates why the 1,500-year cluster is not ecologically uniform: while cold-boreal Picea underwent severe collapse (94.9% negative −r retreat correlations, mean r = -0.637, 78.0% sig) and Fraxinus retreated (68.8% −r), temperate hardwoods expanded aggressively into the newly opened canopy space (Quercus 79.1% +r with 41.8% sig; Acer 67.2% +r with 31.2% sig; Ulmus 63.6% +r). Climax trees Fagus (71.9% +r) and Tsuga (64.7% +r) show lower jump-by-jump significance (15.6%–23.5% sig) because animal dispersal and soil maturation unfold gradually over millennia. Repeating this exact detrended Ebisuzaki check against TraCE precipitation yielded weaker genus differentiation (precip Kruskal p = {tests_f['precip_kruskal_p']:.3f}; {tests_f['precip_ebisuzaki_pass_rate_p05']*100:.1f}% pairs p < 0.05), confirming temperature as the primary continental pacemaker.", bold_prefix="Detailed Inferences from Figure 3a: ")

    _add_single_fig(
        doc,
        fin_fig / "fig3b_mid_vs_final_lags.png",
        "Final Figure 3b. Direct Mid-Evaluation (raw, grey) vs. Final (detrended + RPP + LegacyAge, blue) dumbbell comparison.",
    )
    _p(doc, "A dumbbell chart isolates precisely how methodological rigor altered our original conclusions without forcing readers to cross-reference two separate tables.", bold_prefix="Why Figure 3b was chosen: ")
    _p(doc, "Three decisive shifts stand out. First, Tsuga swung +2,000 years (from an artificial 500 yr at Mid Evals to 2,500 yr alongside Fagus) once trend-matching was removed. Second, Picea shifted +1,000 yr (500 → 1,500 yr), reflecting real stand inertia during rapid warming. Third, Carya (-1,000 yr: 2,500 → 1,500 yr) and Alnus (-500 yr: 2,000 → 1,500 yr) sharpened as RPP corrected pollen bias, while Larix and Populus gained enough clean records to enter and Abies dropped under <5 qualifying sites.", bold_prefix="Detailed Inferences from Figure 3b: ")

    comp_lag = pd.merge(
        m["ls_mid"][["genus", "n_sites", "median_lag_yr"]].rename(columns={"n_sites": "Mid Sites", "median_lag_yr": "Mid Lag (yr)"}),
        m["ls_fin"][["genus", "n_sites", "n_sig_05", "pct_sig_05", "median_lag_yr", "frac_pos_r", "mean_r"]].rename(
            columns={"n_sites": "Fin Sites", "n_sig_05": "Sig (p<0.05)", "pct_sig_05": "Sig (%)", "median_lag_yr": "Final Lag (yr)", "frac_pos_r": "+r (%)", "mean_r": "Mean r"}
        ),
        on="genus", how="outer",
    )
    comp_lag["Delta (yr)"] = comp_lag["Final Lag (yr)"] - comp_lag["Mid Lag (yr)"]
    comp_lag["Sig (%)"] = (comp_lag["Sig (%)"] * 100).round(1)
    comp_lag["+r (%)"] = (comp_lag["+r (%)"] * 100).round(1)
    _add_table(doc, comp_lag.sort_values(["Final Lag (yr)", "Mid Lag (yr)"]), "Table 3. Direct Mid-Evaluation vs. Final detrended/RPP/LegacyAge lag statistics across tree genera.")

    # Final Fig 4
    _h(doc, "6.4 Disentangling Weed Bias from Ice Age No-Analogue Drivers (RQ2: Figure 4)", level=2)
    _add_single_fig(
        doc,
        fin_fig / "fig4_noanalogue_drivers.png",
        "Final Figure 4. Top: Progressive reduction of 500 BP no-analogue floor across Mid TRSH+UPHE (33.1%), TRSH-only (15.6%), and Final TRSH+RPP+LegacyAge (8.0%). Bottom: Per-taxon mean SCD contribution heatmap.",
    )
    _p(doc, "Overplotting all three pipeline stages above a Taxon × Time SCD contribution heatmap simultaneously demonstrates that the 500 BP mismatch was a weed artifact and exposes which exact genera created genuine Ice Age no-analogue forests.", bold_prefix="Why Figure 4 was chosen: ")
    _p(doc, f"1) Collapse of the Fake Holocene Floor (Top): All curves converge near 70%–79% during early deglaciation (Final peak {m['na_fin'].frac_no_analogue.max()*100:.1f}% at 14.5 ka BP), proving Ice Age novelty was real. Across the Holocene, stripping UPHE weeds and adding RPP+LegacyAge collapses 500 BP no-analogue fourfold from {na500_mid:.1f}% (Mid) → {na500_tr:.1f}% (TRSH-only) → {na500_rpp:.1f}% (RPP) → {na500_fin:.1f}% (Final), halving overall mismatch across 15,000 years from {m['na_rows_mid'].no_analogue.mean()*100:.1f}% to {m['na_rows_fin'].no_analogue.mean()*100:.1f}% (SCD threshold {tests_f['no_analogue_threshold_scd']:.4f}).\n2) Ecological Recipe of Alien Forests (Bottom Heatmap): Dark red-orange bands between 14.75 and 11.75 ka reveal that Quercus (mean SCD 0.012–0.026), Picea (0.012–0.023), Betula (0.010–0.022), Fraxinus (0.008–0.016), and Populus co-occurred at mixes unseen in today's separated boreal spruce vs. temperate oak forests. From 8 ka onward, nearly the entire matrix turns pale cream (<0.005), leaving only a faint mid-Holocene Fagus (0.008–0.010) signal while raw UPHE distortion vanishes.\n3) Strict Autocorrelation Reality Check: Final no-analogue fractions still correlate strongly with |climate rate| (Spearman rho = {tests_f['spearman_noanalogue_vs_abs_climate_rate'][0]:.3f}, raw p = {tests_f['spearman_noanalogue_vs_abs_climate_rate'][1]:.2e}) and vegetation turnover (rho = {tests_f['spearman_noanalogue_vs_veg_rate'][0]:.3f}, raw p = {tests_f['spearman_noanalogue_vs_veg_rate'][1]:.2e}). Under 1,000 Ebisuzaki surrogates, vegetation turnover remains significant (p = {tests_f['ebisuzaki_p_veg']:.3f}) while climate speed softens to p = {tests_f['ebisuzaki_p_climate']:.4f}, showing that reorganization turnover—more than temperature rate alone—marks when non-analogue assemblages persist.", bold_prefix="Detailed Inferences from Figure 4: ")

    # Final Fig 5a & 5b
    _h(doc, "6.5 2D Migration Isochrones & the Modern Velocity Deficit (RQ3: Figures 5a & 5b)", level=2)
    _add_single_fig(
        doc,
        fin_fig / "fig5a_migration_isochrones.png",
        "Final Figure 5a. Five statistically validated (2D planar F-test p_2d ≤ 0.05) arrival isochrone maps (ka BP) with convex-hull thin-plate splines and migration azimuth vectors.",
    )
    _p(doc, "Replacing straight-North regressions with 2D contour maps clipped strictly to observed data hulls—and gating panels behind a 2D planar F-test—prevents fitting artificial swirls onto patchy non-migrating trees while capturing true diagonal movement around mountain barriers and lakes.", bold_prefix="Why Figure 5a was chosen: ")
    _p(doc, "Each of the five significant 2D migrants tells a distinct geographic story:\n• Larix (124.0 m/yr, azimuth 1° N, r² = 0.774, p_2d = 0.0026): Classic straight-North frontier tracking across the Upper Midwest as glacial ice melted.\n• Tsuga (116.9 m/yr, azimuth 344° NNW, p_2d = 3.4e-5) & Fagus (169.6 m/yr, azimuth 344° NNW, p_2d = 9.1e-4): Nearly parallel NNW waves expanding from Mid-Atlantic/Appalachian refugia (12–10 ka dark blue) into Michigan, Ontario, and Maine (6–4 ka green).\n• Alnus (264.6 m/yr, azimuth 308° WNW, r² = 0.708, p_2d = 3.8e-7): Completely missed by Mid-Eval 1D North lines (p = 0.119), Alnus turns out to have a tight WNW diagonal wave from New England across the St. Lawrence/Great Lakes into northern Minnesota.\n• Carya (277.0 m/yr, azimuth 65° ENE, r² = 0.344, p_2d = 0.0042): Likewise rejected by Final 1D North regression (p = 0.197), hickory clearly pushed East-Northeast from interior Mississippi/Ohio valley refugia toward the Atlantic coast—matching heavy nut dispersal along warm valleys.\n• Non-significant Genera: Seven genera showed patchy, multi-refugia, or already-present patterns (p_2d > 0.05; Quercus p_2d = 0.095, Pinus p_2d = 0.064) and were deliberately masked out rather than plotted with overfit contours.", bold_prefix="Detailed Inferences from Figure 5a: ")

    _add_single_fig(
        doc,
        fin_fig / "fig5b_velocity_deficit.png",
        "Final Figure 5b. Log-scale migration deficit comparing Mid 1D OLS (grey) and Final 2D spatial speeds (green: medians and full surface range whiskers) against past climate velocity (range 28–343 m/yr, p95 = 332 m/yr) and modern warming velocity (range 1,242–2,071 m/yr, central 1,574 m/yr).",
    )
    _p(doc, "Comparing grey Mid 1D markers directly beside green Final 2D markers on a logarithmic scale shows whether accounting for sideways 2D routes closes the modern warming gap.", bold_prefix="Why Figure 5b was chosen: ")
    _p(doc, f"It does not close the gap. Every Final 2D genus (ranging from Tsuga 116.9 m/yr up to Carya 277.0 m/yr; median {mig2d_med:.1f} m/yr) remains slower than past abrupt p95 climate velocity ({vel_f['past_p95_climate_velocity_m_per_yr']:.1f} m/yr) and sits roughly one full order of magnitude behind modern climate-zone velocity ({vel_f['modern_climate_velocity_m_per_yr']:.1f} m/yr under 1.9 °C/century divided by the {vel_f['spatial_gradient_c_per_km']:.5f} °C/km spatial gradient—a {deficit_fin:.1f}× deficit, virtually identical to Mid Eval's {deficit_mid:.1f}× deficit despite major methodological upgrades).", bold_prefix="Detailed Inferences from Figure 5b: ")

    comp_mig = pd.merge(
        m["mig_mid"][["genus", "n_sites", "rate_m_per_yr"]].rename(columns={"n_sites": "Mid n", "rate_m_per_yr": "Mid 1D (m/yr)"}),
        m["mig_fin"][["genus", "n_sites", "rate_m_per_yr", "p_2d", "rate_2d_median_m_per_yr", "rate_2d_iqr_low", "rate_2d_iqr_high", "mean_azimuth_deg"]].rename(
            columns={"n_sites": "Fin n", "rate_m_per_yr": "Final 1D", "p_2d": "2D p", "rate_2d_median_m_per_yr": "2D Med", "rate_2d_iqr_low": "IQR Low", "rate_2d_iqr_high": "IQR High", "mean_azimuth_deg": "Azimuth (°)"}
        ),
        on="genus", how="outer",
    )
    comp_mig = comp_mig[comp_mig[["Mid 1D (m/yr)", "Final 1D", "2D Med"]].notna().any(axis=1)].sort_values("2D Med", ascending=False)
    _add_table(doc, comp_mig, "Table 4. Statistically significant migration rates: Mid 1D vs. Final 1D and Final 2D spatial speeds with azimuths.")

    # Interactive HTML Views Summary
    _h(doc, "6.6 Interactive HTML Visual Views (Mid Baseline vs. Final Dashboard)", level=2)
    _p(
        doc,
        "Alongside all 17 static figures embedded above (5 original Mid, 5 modernized Mid baseline, and 7 Final publication PNGs), our offline HTML dashboards host 8 interactive Plotly charts across 11 browser tabs so reviewers can hover over individual lakes, bins, and deltas directly:",
    )
    _bullet(doc, "TBD2_MidProject_Baseline_Report.html (4 Plotly Charts): ", "(1) TraCE Temperature Curve interactively displaying Kelvin-to-Celsius hover inspection; (2) Mid Raw Lags bar chart with asymmetric 95% confidence bars; (3) No-Analogue vs. |Climate Rate| bar-by-bar overlay highlighting the 33.1% weed floor; and (4) Log-scale 1D Migration bar chart against 332 and 1,572 m/yr thresholds.")
    _bullet(doc, "TBD2_Final_Report.html (4 Plotly Charts): ", "(1) Mid Raw vs. Final Detrended Genus Lags comparison overlay for direct delta inspection; (2) Three-Stage No-Analogue Ablation Trajectory chart (Mid vs. TRSH-only vs. Final); (3) Verified Climate & Precipitation Dual-Axis Curve (°C and mm/day PRECT); and (4) Final 2D Spatial Migration comparison against past p95 (332.1 m/yr) and modern climate velocity (1,573.8 m/yr) alongside filterable interactive tables across all seven tabs.")

    # --- 7. Discussion ---
    _h(doc, "7. Discussion: Synthesizing the Ecological Story")
    _p(
        doc,
        "Bringing every upgraded test together sharpens the three answers for conservation and paleoecology:",
    )
    _bullet(doc, "1. Taxon-Specific Lag Inertia Is Real (RQ1): ", "Once shared deglacial drift and pine over-representation are removed, fast wind-dispersed colonizers like Larix (750 yr) still outpace slow shade-tolerant canopy dominants like Fagus and Tsuga (2,500 yr). Rather than migrating as intact biomes, forest genera shuffle independently at species-specific tempos controlled by seed size, soil readiness, and cold retreat.")
    _bullet(doc, "2. Most Late-Holocene 'Alien Forests' Were Weeds, While True Ice Age No-Analogue Mixes Tied to Turnover (RQ2): ", "Removing modern farmland UPHE weeds and correcting RPP + LegacyAge lowered 500 BP no-analogue mismatch from an artificial 33.1% down to 8.0%, validating that recent pre-colonial forests resembled modern counterparts. Conversely, deglacial no-analogue mixtures (79.0% at 14.5 ka, built from co-occurring Quercus, Picea, Betula, and Fraxinus) were real ecological recombinations tightly tied to rapid turnover (Ebisuzaki p = 0.033).")
    _bullet(doc, "3. Even Diagonal 2D Expansion Cannot Match Modern Climate Velocity (RQ3): ", "Relaxing straight-North blinders uncovered vigorous east-northeast (Carya, 277.0 m/yr) and west-northwest (Alnus, 264.6 m/yr) postglacial dispersal corridors around topographic barriers. Yet the overall median tree spread of 169.6 m/yr still trails contemporary anthropogenic climate velocity (~1,574 m/yr) by ~9.3×—reinforcing that fragmented modern landscapes cannot rely solely on natural postglacial migration speeds to avoid climatic disequilibrium.")

    # --- 8. Sensitivity Validation, Limitations & Future Outlook ---
    _h(doc, "8. Sensitivity Validation, Limitations & Future Outlook")
    _bullet(doc, "Chronological Ensemble Stability: ", f"Across N = {ens['n_ensemble']} LegacyAge Monte Carlo age realizations, the overall cross-genus median lag remained locked at {ens['ensemble_median_lag_yr']:.0f} yr (IQR {ens['ensemble_lag_iqr_yr']}), showing our core conclusions are insensitive to radiocarbon calibration jitter.")
    _bullet(doc, "250-Year Binning Check: ", f"Halving bin width to 250 yr across {m['audit_250']['sites_retained']} dense lakes ({m['audit_250']['binned_rows']:,} bins) narrowed raw estimates slightly (Picea/Quercus/Pinus 750 yr; Acer 1,750 yr; Fagus/Tsuga 2,000 yr) because finer steps resolve earlier initial shifts, while preserving the identical fast-to-slow rank order.")
    _bullet(doc, "Synthetic Planted-Truth Verification: ", "Testing the entire upgraded pipeline on synthetic lakes with known planted stepped lags (250–2,500 yr), pure random-walk AR(1) nulls, PRECT series, and 2D 200 m/yr diagonal wavefronts recovered planted lags within ±500 yr, held random-walk false positives cleanly at 5.0% (rw_fpr = 0.050) via Ebisuzaki tests, and accurately retrieved synthetic 2D speeds.")
    _bullet(doc, "Remaining Limitations: ", f"(1) {ens['total_sites']-ens['matched_sites']} of {ens['total_sites']} final sites lacked LegacyAge 1.0 matches and rely on Neotoma fallback depth-uncertainty bounds; (2) genus-level grouping blends ecologically distinct species (e.g., white vs. black spruce); (3) coarse TraCE grid cells smooth local topographic microclimates; and (4) 500-year averages conservatively understate century-scale bursts.")
    _bullet(doc, "Future Outlook: ", "Extending this verified pipeline with Sporormiella dung fungal spores (megafaunal grazing collapse), sedimentary charcoal fire records, and downscaled CMIP6 future tree vulnerability projections will connect late-glacial migration constraints directly to forest management planning.")

    # --- 9. References ---
    _h(doc, "9. References")
    refs = [
        "Blois, J. L., Williams, J. W., Fitzpatrick, M. C., Jackson, S. T., & Ferrier, S. (2013). Space can substitute for time in predicting climate-change effects on biodiversity. PNAS, 110(23), 9374–9379.",
        "Dawson, A., Paciorek, C. J., McLachlan, J. S., Goring, S., Williams, J. W., & Jackson, S. T. (2016). Quantifying pollen–vegetation relationships to reconstruct ancient forests using 19th-century forest composition and pollen data. Quaternary Science Reviews, 137, 156–175.",
        "Ebisuzaki, W. (1997). A method to estimate the statistical significance of a correlation when the data are serially correlated. Journal of Climate, 10(9), 2147–2153.",
        "Fordham, D. A., Jackson, S. T., Brown, S. C., Huntley, B., Brook, B. W., Dahl-Jensen, D., et al. (2020). Using paleo-archives to safeguard biodiversity under climate change. Science, 369(6507), eabc5654.",
        "Gill, J. L., Williams, J. W., Jackson, S. T., Lininger, K. B., & Robinson, G. S. (2009). Pleistocene megafaunal collapse, novel plant communities, and enhanced fire regimes in North America. Science, 326(5956), 1100–1103.",
        "Knight, C. A., Baskaran, A., Li, Y., et al. (2020). Community assembly and climate mismatch in late-Quaternary eastern North American pollen assemblages. The American Naturalist, 195(2), 184–200.",
        "Li, C., Cao, X., Tian, F., Dallmeyer, A., & Herzschuh, U. (2022). LegacyAge 1.0: harmonised chronologies for global late-Quaternary pollen records. Earth System Science Data, 14(3), 1331–1343.",
        "Marsicek, J., Shuman, B. N., Bartlein, P. J., Shafer, S. L., & Brewer, S. (2018). Reconciling divergent trends and millennial variations in Holocene temperatures. Nature, 554(7690), 92–96.",
        "Mottl, O., Flantua, S. G., Bhatta, K. P., Felde, V. A., Giesecke, T., Goring, S., et al. (2021). Global acceleration in rates of vegetation change over the past 18,000 years. Science, 372(6544), 860–864.",
        "Nolan, C., Overpeck, J. T., Allen, J. R., Anderson, P. M., Betancourt, J. L., Binney, H. A., et al. (2018). Past and future global transformation of terrestrial ecosystems under climate change. Science, 361(6405), 920–923.",
        "Shuman, B. N., & Marsicek, J. (2016). The structure of Holocene climate change in mid-latitude North America. Quaternary Science Reviews, 141, 38–51.",
        "Sugita, S. (2007). Theory of quantitative reconstruction of vegetation I: pollen from large sites REVEALS regional vegetation composition. The Holocene, 17(2), 229–241.",
        "Wieczorek, M., & Herzschuh, U. (2020). Compilation of relative pollen productivity (RPP) estimates and taxonomically harmonised pollen datasets for the Northern Hemisphere. Earth System Science Data, 12(4), 3515–3545.",
        "Williams, J. W., Shuman, B. N., Webb, T., Bartlein, P. J., & Leduc, P. L. (2004). Late-Quaternary vegetation dynamics in North America: scaling from taxa to biomes. Ecological Monographs, 74(2), 309–334.",
        "Williams, J. W., Grimm, E. C., Blois, J. L., et al. (2018). The Neotoma Paleoecology Database, a multiproxy, international, community-curated data resource. Quaternary Research, 89(1), 156–177.",
        "NCAR TraCE-21ka Simulation (Dataset d651050, DOI 10.5065/CXB5-TV56) & IPCC AR6 Working Group I Technical Summary (~0.19 °C/decade warming rate).",
    ]
    for ref in refs:
        p = doc.add_paragraph(ref, style="List Bullet")
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.line_spacing = 1.05
        for run in p.runs:
            run.font.size = Pt(8.5)

    out_docx = C.ROOT / "TBD2_Final_Project_Report.docx"
    out_pdf = C.ROOT / "TBD2_Final_Project_Report.pdf"
    doc.save(out_docx)
    print(f"[report] wrote {out_docx}")
    _export_pdf(out_docx, out_pdf)
    print(f"[report] wrote {out_pdf}")
    return out_docx, out_pdf
