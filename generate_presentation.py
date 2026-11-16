"""generate_presentation.py - Build 25-minute academic defense presentation.

Generates TBD2_Final_Project_Presentation.pptx (22 slides, 16:9 widescreen)
with embedded 300-dpi publication figures, student-friendly English slide copy,
and complete conversational speaker notes with timing checkpoints.
"""
from pathlib import Path
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

ROOT = Path(__file__).resolve().parent
FIG_DIR = ROOT / "data" / "outputs" / "figures_standalone"
PPTX_OUT = ROOT / "TBD2_Final_Project_Presentation.pptx"

# Color Palette (Okabe-Ito + Light Academic)
BG_CANVAS = RGBColor(0xF8, 0xFA, 0xFC)       # Crisp soft off-white
CARD_BG = RGBColor(0xFF, 0xFF, 0xFF)         # Pure white card
CARD_BORDER = RGBColor(0xCB, 0xD5, 0xE1)     # Slate border
CARD_MUTED_BG = RGBColor(0xF1, 0xF5, 0xF9)   # Muted card fill

COLOR_INK = RGBColor(0x0F, 0x17, 0x2A)        # Deep slate primary text
COLOR_SLATE = RGBColor(0x47, 0x55, 0x69)      # Slate secondary text
COLOR_MUTED = RGBColor(0x64, 0x74, 0x8B)      # Lighter slate text
COLOR_BLUE = RGBColor(0x00, 0x72, 0xB2)       # Okabe-Ito Blue
COLOR_VERMILION = RGBColor(0xD5, 0x5E, 0x00)  # Okabe-Ito Vermilion
COLOR_GREEN = RGBColor(0x00, 0x9E, 0x73)      # Okabe-Ito Green
COLOR_ORANGE = RGBColor(0xE6, 0x9F, 0x00)     # Okabe-Ito Orange
COLOR_SKY = RGBColor(0x56, 0xB4, 0xE9)        # Okabe-Ito Sky Blue
COLOR_LINE = RGBColor(0xE2, 0xE8, 0xF0)       # Divider line


def create_base_deck():
    prs = pptx.Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    return prs


def add_slide_header(slide, category_tag, title_text, subtitle_text=None):
    """Draws consistent academic header with category tag, title, and divider."""
    # Background fill
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = BG_CANVAS
    bg.line.fill.background()

    # Category Badge Pill
    pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.42), Inches(3.2), Inches(0.32))
    pill.fill.solid()
    pill.fill.fore_color.rgb = RGBColor(0xE0, 0xF2, 0xFE)
    pill.line.color.rgb = RGBColor(0xBA, 0xE6, 0xFD)
    pill.line.width = Pt(0.75)
    tf = pill.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = category_tag.upper()
    p.alignment = PP_ALIGN.CENTER
    p.font.size = Pt(8.5)
    p.font.bold = True
    p.font.color.rgb = RGBColor(0x03, 0x69, 0xA1)
    p.font.name = "Segoe UI"

    # Slide Title
    tx_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.78), Inches(11.7), Inches(0.65))
    tf2 = tx_box.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_top = tf2.margin_right = tf2.margin_bottom = 0
    p2 = tf2.paragraphs[0]
    p2.text = title_text
    p2.font.size = Pt(21)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_INK
    p2.font.name = "Segoe UI"

    if subtitle_text:
        p_sub = tf2.add_paragraph()
        p_sub.text = subtitle_text
        p_sub.font.size = Pt(11)
        p_sub.font.color.rgb = COLOR_SLATE
        p_sub.font.name = "Segoe UI"
        p_sub.space_before = Pt(2)

    # Subtle Header Accent Line
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.48), Inches(11.733), Inches(0.02))
    line.fill.solid()
    line.fill.fore_color.rgb = COLOR_LINE
    line.line.fill.background()


def add_card(slide, left, top, width, height, title, bullet_list, bg_color=CARD_BG, border_color=CARD_BORDER, title_color=COLOR_BLUE):
    """Draws a neat card with title and bullet points in clean simple English."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    card.line.color.rgb = border_color
    card.line.width = Pt(1)

    tx_box = slide.shapes.add_textbox(Inches(left + 0.22), Inches(top + 0.18), Inches(width - 0.44), Inches(height - 0.36))
    tf = tx_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    if title:
        p_title = tf.paragraphs[0]
        p_title.text = title
        p_title.font.size = Pt(12.5)
        p_title.font.bold = True
        p_title.font.color.rgb = title_color
        p_title.font.name = "Segoe UI"
        p_title.space_after = Pt(6)
        first_bullet = True
    else:
        first_bullet = False

    for item in bullet_list:
        p = tf.add_paragraph() if (title or not first_bullet) else tf.paragraphs[0]
        first_bullet = False
        p.text = f"•  {item}"
        p.font.size = Pt(10.5)
        p.font.color.rgb = COLOR_INK
        p.font.name = "Segoe UI"
        p.space_after = Pt(4)


def add_kpi_card(slide, left, top, width, height, main_stat, label, subtitle=None, accent_color=COLOR_BLUE):
    """Draws a clean metric stat card."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    card.fill.solid()
    card.fill.fore_color.rgb = CARD_BG
    card.line.color.rgb = CARD_BORDER
    card.line.width = Pt(1)

    tx_box = slide.shapes.add_textbox(Inches(left + 0.15), Inches(top + 0.15), Inches(width - 0.3), Inches(height - 0.3))
    tf = tx_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p_stat = tf.paragraphs[0]
    p_stat.text = main_stat
    p_stat.font.size = Pt(24)
    p_stat.font.bold = True
    p_stat.font.color.rgb = accent_color
    p_stat.font.name = "Segoe UI"

    p_lbl = tf.add_paragraph()
    p_lbl.text = label
    p_lbl.font.size = Pt(11)
    p_lbl.font.bold = True
    p_lbl.font.color.rgb = COLOR_INK
    p_lbl.font.name = "Segoe UI"
    p_lbl.space_before = Pt(2)

    if subtitle:
        p_sub = tf.add_paragraph()
        p_sub.text = subtitle
        p_sub.font.size = Pt(9.5)
        p_sub.font.color.rgb = COLOR_SLATE
        p_sub.font.name = "Segoe UI"
        p_sub.space_before = Pt(3)


def add_figure_slide_content(slide, fig_filename, fig_left, fig_top, fig_w, fig_h,
                             card_left, card_top, card_w, card_h,
                             card_title, bullet_points, caption_text=None, kpis=None):
    """Embeds publication figure beside an explanatory card and optional KPI metrics."""
    fig_path = FIG_DIR / fig_filename
    if fig_path.exists():
        slide.shapes.add_picture(str(fig_path), Inches(fig_left), Inches(fig_top), width=Inches(fig_w), height=Inches(fig_h))
        if caption_text:
            cap_box = slide.shapes.add_textbox(Inches(fig_left), Inches(fig_top + fig_h + 0.08), Inches(fig_w), Inches(0.4))
            tf_cap = cap_box.text_frame
            tf_cap.word_wrap = True
            p = tf_cap.paragraphs[0]
            p.text = caption_text
            p.font.size = Pt(8.5)
            p.font.color.rgb = COLOR_MUTED
            p.font.name = "Segoe UI"

    add_card(slide, card_left, card_top, card_w, card_h, card_title, bullet_points)

    if kpis:
        k_top = card_top + card_h + 0.18
        k_w = (card_w - (0.15 * (len(kpis) - 1))) / len(kpis)
        for idx, (stat, lbl, sub, col) in enumerate(kpis):
            add_kpi_card(slide, card_left + (idx * (k_w + 0.15)), k_top, k_w, 1.45, stat, lbl, sub, col)


def set_notes(slide, slide_num, target_time, running_time, talk_script, transition, potential_qa=None):
    """Sets student-friendly conversational speaker notes on the slide."""
    notes = slide.notes_slide.notes_text_frame
    text_parts = [
        f"=== SLIDE {slide_num} OF 22 ===",
        f"⏱️ PACING: [Target Slide Time: {target_time} | Running Total: {running_time} / 25:00]",
        "",
        "🗣️ CONVERSATIONAL SPOKEN SCRIPT (Student-Friendly English):",
        talk_script,
        "",
        f"➡️ TRANSITION TO NEXT SLIDE:\n{transition}"
    ]
    if potential_qa:
        text_parts.extend([
            "",
            f"💡 ANTICIPATED QUESTION & PLAIN-ENGLISH ANSWER:\n{potential_qa}"
        ])
    notes.text = "\n".join(text_parts)


# ==============================================================================
# SLIDE BUILDERS (22 SLIDES)
# ==============================================================================

def build_slide_01_title(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = RGBColor(0x0F, 0x17, 0x2A) # Sleek Dark Slate Cover
    bg.line.fill.background()

    # Category Pill
    pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(1.2), Inches(4.5), Inches(0.38))
    pill.fill.solid()
    pill.fill.fore_color.rgb = RGBColor(0x1E, 0x29, 0x3B)
    pill.line.color.rgb = RGBColor(0x38, 0xBD, 0xF8)
    pill.line.width = Pt(1)
    p = pill.text_frame.paragraphs[0]
    p.text = "ACADEMIC FINAL DEFENSE  ·  COURSE ES1.101"
    p.alignment = PP_ALIGN.CENTER
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = RGBColor(0x38, 0xBD, 0xF8)

    # Main Title
    tb = slide.shapes.add_textbox(Inches(1.2), Inches(1.85), Inches(11.0), Inches(2.2))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "How Trees Responded to 15,000 Years\nof Climate Warming"
    p.font.size = Pt(36)
    p.font.bold = True
    p.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    p_sub = tf.add_paragraph()
    p_sub.text = "Quantifying Ecological Lags, Novel Forests & 2D Migration Deficits in Eastern North America"
    p_sub.font.size = Pt(17)
    p_sub.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)
    p_sub.space_before = Pt(10)

    # Team & Presentation Info Box
    info_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(4.4), Inches(10.9), Inches(1.8))
    info_box.fill.solid()
    info_box.fill.fore_color.rgb = RGBColor(0x1E, 0x29, 0x3B)
    info_box.line.color.rgb = RGBColor(0x33, 0x41, 0x55)
    info_box.line.width = Pt(1)

    tb2 = slide.shapes.add_textbox(Inches(1.5), Inches(4.6), Inches(10.3), Inches(1.4))
    tf2 = tb2.text_frame
    p1 = tf2.paragraphs[0]
    p1.text = "Team TBD2 (Project 25): Vivek R  ·  Nandan Rajesh Kamat  ·  Shaurya Gupta"
    p1.font.size = Pt(14)
    p1.font.bold = True
    p1.font.color.rgb = RGBColor(0xF1, 0xF5, 0xF9)

    p2 = tf2.add_paragraph()
    p2.text = "Data Sources: Neotoma Paleoecology Database (Fossil & Modern Pollen) + TraCE-21ka Paleoclimate Simulations"
    p2.font.size = Pt(11)
    p2.font.color.rgb = RGBColor(0x38, 0xBD, 0xF8)
    p2.space_before = Pt(6)

    p3 = tf2.add_paragraph()
    p3.text = "Methodological Framework: LegacyAge 1.0 Bayesian Age Models · REVEALS Pollen Productivity · Ebisuzaki Phase Tests · 2D Planar Surfaces"
    p3.font.size = Pt(10)
    p3.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)
    p3.space_before = Pt(4)

    set_notes(slide, 1, "1 min 00s", "01:00",
        "Hello everyone, and welcome to our final project presentation! Today, we are taking you on a journey through the last 15,000 years of Earth's history.\n\n"
        "Our central question is simple but urgent: When the climate warms up rapidly, can forest trees keep up? "
        "By looking at fossil pollen preserved in lake mud across eastern North America since the last Ice Age, combined with cutting-edge computer climate simulations, "
        "we calculated exact numbers for how long different trees lagged behind rising temperatures, what caused weird extinct forest mixtures, and how fast trees actually moved across the map.",
        "To understand why this matters right now, let's look at the big ecological picture on slide 2.",
        "Q: Why did you pick eastern North America?\nA: Because eastern North America has the densest, highest-quality network of radiocarbon-dated lake sediment cores in the world, with continuous records from the ice age right up to the modern era.")


def build_slide_02_context(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_header(slide, "1. Context & Motivation", "The Big Picture: Why Study Ancient Forest Changes?",
                     "Looking back 15,000 years provides our only real-world test of how long-lived trees handle rapid warming.")

    cards = [
        ("The Deglacial Natural Experiment", [
            "15,000 to 500 years ago, Earth warmed naturally as massive ice sheets melted over North America.",
            "This gives us a real historical laboratory to see what happens to forests over thousands of years.",
            "Trees cannot pack up and walk overnight; they can only move generation by generation through seed dispersal."
        ], COLOR_BLUE),
        ("The Unanswered Scientific Gap", [
            "Older studies noticed that forests lagged behind climate, but lacked precise numbers.",
            "Key missing answers: Did all trees lag by the same amount of time? Did they move as a single unit?",
            "How fast could trees physically disperse across mountains and lakes compared to shifting climate zones?"
        ], COLOR_VERMILION),
        ("The Urgent Modern Stakes", [
            "Today, human-caused warming is happening 10 times faster than anything trees experienced naturally.",
            "If past trees struggled to keep up with gentle natural warming, our modern forests face a severe tracking crisis.",
            "Understanding past limits tells us which trees are at risk of extinction and where we need conservation action."
        ], COLOR_GREEN)
    ]

    for idx, (title, bullets, col) in enumerate(cards):
        add_card(slide, 0.8 + idx * 3.98, 1.7, 3.75, 5.2, title, bullets, title_color=col)

    set_notes(slide, 2, "1 min 15s", "02:15",
        "Why do we care about trees that lived thousands of years ago? Because trees live for centuries! You can't just put an entire forest in a greenhouse and see how it reacts to 100 years of global warming.\n\n"
        "Fortunately, nature already ran this experiment for us. 15,000 years ago, North America was covered in a giant glacier. As the ice melted, temperatures rose, and trees had to migrate northward out of their southern refuges.\n\n"
        "By digging into ancient lake sediments and counting fossil pollen grains, we can see exactly how fast each tree species moved. But as we'll see, modern climate change is moving at lightning speed compared to anything ancient trees ever survived.",
        "To break down this massive problem into concrete science, we formulated three clear research questions on slide 3.",
        "Q: Isn't modern warming different from deglacial warming?\nA: Yes! Modern warming is much faster (projected at ~1.9°C per century vs ~0.15°C per century in the past). That is precisely why measuring the maximum speed of past trees gives us the biological speed limit.")


def build_slide_03_questions(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_header(slide, "1. Context & Motivation", "Three Central Questions We Set Out to Answer",
                     "Breaking down postglacial forest reorganization into three measurable, quantitative dimensions.")

    rqs = [
        ("RQ1: The Response Clock", "How long did different tree genera lag behind temperature changes?", [
            "When climate suddenly warmed or cooled, did trees respond right away, or did they take centuries?",
            "Did fast pioneers (like tamarack) react differently from slow climax trees (like beech)?",
            "Did warming cause species to expand their range, or did it trigger cold-adapted trees to collapse?"
        ], COLOR_BLUE, "Lag Times & Direction"),
        ("RQ2: Novel Ecosystems", "What caused strange 'no-analogue' forests with no modern match?", [
            "During the ice age, trees formed strange combinations that do not exist anywhere on Earth today.",
            "For example, cold spruce grew right alongside warm ash and elm trees.",
            "Was this novelty driven by sudden climate jolts, and which specific trees created the weird mixtures?"
        ], COLOR_VERMILION, "Novel Forest Drivers"),
        ("RQ3: The Speed Deficit", "Could tree migration speeds keep up with moving climate zones?", [
            "How fast did tree populations actually spread across the 2D landscape (in meters per year)?",
            "Did trees migrate straight north, or did they take diagonal detours around lakes and mountains?",
            "How does their real biological speed compare to modern global warming velocities?"
        ], COLOR_GREEN, "2D Velocity vs Climate")
    ]

    for idx, (rq_num, rq_title, bullets, col, badge) in enumerate(rqs):
        top_pos = 1.7 + idx * 1.75
        add_card(slide, 0.8, top_pos, 11.733, 1.55, f"{rq_num}:  {rq_title}", bullets, title_color=col)

    set_notes(slide, 3, "1 min 15s", "03:30",
        "Here are our three core research questions, which structure this entire project:\n\n"
        "First, Research Question 1: How many centuries did trees lag behind temperature? Did all trees march to the same beat, or did pioneers react quickly while canopy giants lagged by thousands of years?\n\n"
        "Second, Research Question 2: In ancient records, we see 'no-analogue' forests—meaning tree combinations with no modern match on Earth. What caused these weird mixtures, and which tree species drove them?\n\n"
        "Third, Research Question 3: What was the physical speed limit of tree migration across real 2D landscapes? When we measure their speed across real hills and valleys, could they ever outrun modern climate change?",
        "To answer these questions rigorously, we need real fossil evidence. Let's look at our fossil core network on slide 4.",
        "Q: What does 'no-analogue' mean in simple terms?\nA: Imagine walking into a forest and seeing polar spruce trees growing next to southern walnut trees. That's a 'no-analogue' forest—a unique mixture that doesn't exist anywhere in nature today.")


def build_slide_04_data_network(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_header(slide, "2. Data & Study Corridor", "Where Did the Data Come From? 69 Lake Sediment Cores",
                     "Synthesizing 15,000 years of fossil pollen across Eastern North America from the Neotoma Database.")

    bullets = [
        "69 High-Quality Sediment Cores: Retained across 25°–50°N and 95°–65°W, providing 1,706 continuous 500-year time bins.",
        "Strict Quality Filtering: Every site required at least 150 identified pollen grains per sample and continuous coverage with no massive gaps.",
        "Li et al. (2022) LegacyAge 1.0: 57 sites had direct calibrated Bayesian radiocarbon chronologies; 12 sites used depth-uncertainty fallback.",
        "Modern Surface Calibration: 611 modern surface pollen samples across eastern North America serve as our baseline benchmark."
    ]

    kpis = [
        ("69", "Fossil Cores", "Continuous records", COLOR_BLUE),
        ("1,706", "500-Yr Bins", "15 ka to 500 BP", COLOR_VERMILION),
        ("611", "Modern Sites", "Reference dataset", COLOR_GREEN)
    ]

    add_figure_slide_content(slide, "fig1_study_sites.png", 0.8, 1.65, 5.8, 5.1,
                             6.85, 1.65, 5.68, 3.45,
                             "A Rigorous Geographic Study Corridor", bullets,
                             "Figure 1: Core locations across Eastern North America (Blue: LegacyAge 1.0; Amber: Neotoma; Red x: Excluded).",
                             kpis)

    set_notes(slide, 4, "1 min 15s", "04:45",
        "Let's look at where our raw data comes from. On the map on the left (Figure 1), you can see our study corridor across eastern North America, stretching from the Gulf Coast up to southern Canada.\n\n"
        "Every single blue and yellow dot is a real lake where scientists drilled deep sediment cores into the mud. Why lake mud? Because every spring, flowering trees release pollen into the air. Pollen falls into lakes, sinks to the bottom, and gets sealed in layers of mud year after year, preserving a permanent diary of what trees were growing.\n\n"
        "We collected 69 continuous lake cores, divided them into 1,706 500-year time windows, and calibrated them against 611 modern pollen samples. Notice the blue dots: 57 of our sites use 'LegacyAge 1.0'—a state-of-the-art Bayesian radiocarbon dating system published by Li and colleagues in 2022, which fixes messy core chronologies.",
        "Now that we know where the trees were, we need an independent thermometer to see what the temperature was doing. Let's look at that on slide 5.",
        "Q: Why use 500-year bins instead of exact years?\nA: Because sediment accumulation in lake mud varies slightly from year to year. 500-year windows give a clean, robust, and harmonized signal across all 69 lakes without over-interpreting noise.")


def build_slide_05_climate_trace(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_header(slide, "2. Data & Study Corridor", "Independent Climate History: The TraCE-21ka Simulation",
                     "Using an independent supercomputer paleoclimate model avoids circular reasoning.")

    cards = [
        ("Why Independence Matters (No Circular Logic!)", [
            "Common trap in paleontology: Some researchers use fossil pollen to estimate temperature, and then use that temperature to explain pollen!",
            "That is completely circular reasoning! You cannot test if trees lag climate using a thermometer made out of trees.",
            "Solution: We used TraCE-21ka—a physics-based supercomputer simulation from NCAR (National Center for Atmospheric Research)."
        ], COLOR_BLUE),
        ("What TraCE-21ka Provides Across Every Site", [
            "Surface Temperature (°C): Decadal mean annual temperature tracked through every 500-year bin from 15,000 BP to modern times.",
            "Annual Precipitation (mm/day): Rain and snowfall simulation (PRECT) to check moisture controls alongside temperature.",
            "Thermal Spatial Gradient: 0.00121 °C per kilometer across eastern North America (temperature drops ~1.2°C for every 1,000 km north)."
        ], COLOR_VERMILION),
        ("Key Abrupt Climate Events Tracked", [
            "Bølling-Allerød Warm Period (14.7–12.9 ka BP): Sudden, massive warming melting northern ice.",
            "Younger Dryas Cold Snap (12.9–11.7 ka BP): Sharp, brutal freeze plunging the region back into near-glacial cold.",
            "8.2 ka Cooling Pulse: A rapid freshwater drainage into the North Atlantic that chilled temperatures for several centuries."
        ], COLOR_GREEN)
    ]

    for idx, (title, bullets, col) in enumerate(cards):
        add_card(slide, 0.8 + idx * 3.98, 1.7, 3.75, 5.2, title, bullets, title_color=col)

    set_notes(slide, 5, "1 min 15s", "06:00",
        "On slide 5, let's talk about our climate data. This is where many older studies made a serious mistake.\n\n"
        "In paleoclimatology, people often look at pollen in mud and guess: 'Well, there was lots of spruce, so it must have been cold!' But if you use that estimated temperature to test if spruce was lagging behind climate, you are chasing your own tail—that's circular reasoning!\n\n"
        "To avoid circular logic, we used TraCE-21ka. This is an independent, physics-based simulation run by supercomputers at NCAR. It simulates solar orbit changes, greenhouse gases, and ice sheet dynamics from basic physics—completely independent of fossil pollen.\n\n"
        "TraCE gives us true surface temperatures in degrees Celsius and rainfall in millimeters per day. It also lets us calculate the geographic temperature gradient: about 1.2 degrees Celsius per thousand kilometers.",
        "Now, fossil pollen data can be tricky to interpret if you don't clean it properly. On slide 6, we explain three critical upgrades we made to clean the data.",
        "Q: Is TraCE-21ka accurate at regional scales?\nA: Yes! TraCE-21ka has been extensively validated against independent ice cores, cave stalagmites, and ocean sediment records worldwide.")


def build_slide_06_methods_cleaning(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_header(slide, "2. Data & Study Corridor", "Cleaning the Fossil Signal: 3 Crucial Methodological Upgrades",
                     "Fixing pollen overproduction, post-settlement agricultural weeds, and radiocarbon errors.")

    cards = [
        ("1. Fixing Pollen 'Megaphones' (RPP)", [
            "The Problem: Different trees produce wildly different amounts of pollen.",
            "Pine and birch are 'megaphones'—they dump millions of tiny airborne pollen grains that blow hundreds of miles away.",
            "Maple and larch are 'whisperers'—they produce heavy, insect-carried pollen that barely leaves the tree.",
            "Our Fix: We applied empirical REVEALS Relative Pollen Productivity (RPP) multipliers (Wieczorek & Herzschuh 2020) to convert pollen grains into true tree abundances on the ground."
        ], COLOR_BLUE),
        ("2. Removing Farm Weeds (TRSH-Only)", [
            "The Problem: When European settlers cleared forests in the 1700s and 1800s, agricultural weeds (ragweed, grasses) exploded.",
            "If you include these weeds in your analysis, late-Holocene forests falsely look 'weird' or 'no-analogue' simply because of modern farms.",
            "Our Fix: We isolated strictly arboreal woody trees and shrubs (TRSH-only), dropping human weed artifacts and revealing true pre-colonial forest floors."
        ], COLOR_VERMILION),
        ("3. Harmonized Bayesian Clocks", [
            "The Problem: Older carbon-14 dates suffered from core gaps, marine carbon offsets, and calibration jumps.",
            "Our Fix: We harmonized all 69 cores to Li et al. (2022) LegacyAge 1.0 Bayesian chronologies, standardizing calendar ages across all lakes."
        ], COLOR_GREEN)
    ]

    for idx, (title, bullets, col) in enumerate(cards):
        add_card(slide, 0.8 + idx * 3.98, 1.7, 3.75, 5.2, title, bullets, title_color=col)

    set_notes(slide, 6, "1 min 15s", "07:15",
        "Slide 6 covers three critical upgrades we implemented to clean our raw data.\n\n"
        "First, pollen isn't equal! Think of pine trees like people with megaphones: a single pine tree produces billions of tiny, winged pollen grains that fly hundreds of miles. Maple trees, on the other hand, produce very little pollen because bees carry it. If you just count raw pollen grains, you think North America was 80% pine when it wasn't! We used mathematical multipliers called Relative Pollen Productivity to fix this distortion.\n\n"
        "Second, we filtered out agricultural farm weeds. When European settlers arrived in the 1700s and cleared the woods for farms, ragweed and grass exploded. If you leave ragweed in, the pre-industrial forest looks 'abnormal' when it was actually just a farm weed invasion. Removing weeds gave us an honest look at pure tree forests.\n\n"
        "Third, we used modern Bayesian radiocarbon chronologies from LegacyAge 1.0, giving us synchronized, accurate dates across all 69 lakes.",
        "Now let's examine our statistical toolset on slide 7—how we proved these lag results weren't just statistical flukes.",
        "Q: How big is the difference between pine and maple pollen productivity?\nA: Pine produces about 10 to 15 times more pollen than maple! That's why RPP calibration is essential for accurate tree counts.")


def build_slide_07_methods_stats(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_header(slide, "2. Data & Study Corridor", "Our Statistical Toolkit: Proving Results Aren't Flukes",
                     "Trend removal, 1,000 surrogate shuffles, and 2D spatial surface modeling.")

    cards = [
        ("Removing the 15,000-Yr Trend", [
            "The Classic Trap: Both temperature and oak trees increased from 15,000 years ago to the present.",
            "If two curves both go up over time, standard statistics will claim they are 99% correlated, even if one is just ice melting and the other is random noise!",
            "Our Solution: We took first differences (bin-to-bin changes: ΔTree vs ΔTemp). This removes the background trend and asks: 'When temperature suddenly jumped this century, did the tree jump too?'"
        ], COLOR_BLUE),
        ("The 1,000-Surrogate Ebisuzaki Test", [
            "Even after detrending, environmental time series have 'memory' (autocorrelation). Standard p-values underestimate error.",
            "Our Solution: We generated 1,000 fake climate surrogates using the Ebisuzaki phase-randomization algorithm.",
            "These fake series have the exact same wiggliness and power spectrum as real climate, but shuffled in time.",
            "If a tree genus beats 950 out of 1,000 fake climates, we know the response is real, not accidental."
        ], COLOR_VERMILION),
        ("True 2D Spatial Velocity Surfaces", [
            "Older studies forced trees to migrate strictly due North (0°) in a 1D straight line.",
            "Our Solution: We fitted 2D planar arrival surfaces Age(x, y) in equal-area Albers coordinates.",
            "Local speed is 1 / |∇Age| along the actual physical front, revealing real detour routes around the Great Lakes and Appalachians."
        ], COLOR_GREEN)
    ]

    for idx, (title, bullets, col) in enumerate(cards):
        add_card(slide, 0.8 + idx * 3.98, 1.7, 3.75, 5.2, title, bullets, title_color=col)

    set_notes(slide, 7, "1 min 15s", "08:30",
        "Slide 7 introduces our statistical safety kit. In data science, there's a famous trap called 'spurious correlation.'\n\n"
        "Over the last 15,000 years, global temperature went up, and oak trees increased. If you just run a simple correlation between them, you get a 99% match! But that's like saying ice cream sales cause sunburns—they both just happen during summer! To fix this, we took first-differences: we subtracted bin from bin. We only looked at sudden changes: when temperature bumped up, did the tree bump up?\n\n"
        "Next, we ran the 'Ebisuzaki phase-randomization test.' For every single tree species, we generated 1,000 fake climate histories that had the exact same wiggles and bumps as real climate, but shuffled. A correlation was only accepted as statistically significant if it beat 95% of those 1,000 surrogate tests.\n\n"
        "Finally, we ditched 1D North-only lines and modeled migration on a real 2D map.",
        "Now, let's dive into our results! On slide 8, we look at the climate rollercoaster that triggered this forest upheaval.",
        "Q: What is phase-randomization in simple terms?\nA: It keeps all the frequency waves of the climate curve identical, but scrambles the timing of when peaks occur. That creates realistic fake climates to test our data against.")


def build_slide_08_results_climate(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_header(slide, "3. Results: Climate & Turnover", "15,000 Years of Climate Warming & Forest Turnover",
                     "Tracking temperature, precipitation, warming rates, and plant community upheaval across abrupt events.")

    bullets = [
        "TraCE-21ka Temperature Trajectory: Regional annual temperature rose from -1.1°C at 15 ka BP to +8.5°C during the mid-Holocene (~6 ka BP).",
        "Annual Precipitation: Rose from 2.0 mm/day during dry glacial conditions to a wet Holocene peak of 3.2 mm/day at ~10 ka BP.",
        "Peak Warming Rate: Hit +0.43°C per century during the Bølling-Allerød deglaciation (14.5 ka BP).",
        "Hellinger Community Turnover: Forest turnover peaked right alongside the fastest climate rates, proving that abrupt temperature spikes directly triggered massive vegetation reshuffling."
    ]

    kpis = [
        ("+9.6 °C", "Total Warming", "Glacial to Holocene", COLOR_VERMILION),
        ("0.43 °C/c", "Peak Warming Rate", "At 14.5 ka BP", COLOR_ORANGE),
        ("0.24", "Max Turnover Rate", "Hellinger dist/c", COLOR_BLUE)
    ]

    add_figure_slide_content(slide, "fig2_climate_and_turnover.png", 0.8, 1.65, 5.8, 5.1,
                             6.85, 1.65, 5.68, 3.45,
                             "Coincidence of Climate Shifts & Forest Upheaval", bullets,
                             "Figure 2: TraCE-21ka temperature (°C), precipitation (mm/day), warming rate, and vegetation turnover across abrupt events.",
                             kpis)

    set_notes(slide, 8, "1 min 15s", "09:45",
        "Now let's examine Figure 2 on slide 8. This is our timeline of environmental upheaval over the last 15,000 years.\n\n"
        "Look at the top two panels: the orange line is temperature, and the blue dashed line is rainfall. 15,000 years ago, eastern North America was freezing cold—averaging about minus 1 degree Celsius. Over the deglaciation, it warmed by almost 10 degrees Celsius, reaching about 8.5 degrees in the mid-Holocene.\n\n"
        "Notice the yellow and blue vertical bars. The yellow band is the 'Bølling-Allerød'—a massive warming jump where temperatures rose at 0.43 degrees Celsius per century. Right after it is the 'Younger Dryas' blue band—a brutal cold snap where climate suddenly slammed into reverse!\n\n"
        "Now look at the bottom panel: that dark blue curve is vegetation turnover—meaning how rapidly the forest community was changing. Notice how the turnover peaks line up with the sudden climate jumps! When climate shifted fast, forests were thrown into chaos.",
        "So, when the climate warmed, how long did it take for trees to actually respond? That brings us to Research Question 1 on slide 9.",
        "Q: Why did precipitation rise along with temperature?\nA: Because warmer air holds more moisture, and melting ice sheets shifted jet streams, bringing moist Atlantic air into the interior.")


def build_slide_09_rq1_lags(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_header(slide, "3. Results: RQ1 (Response Lags)", "RQ1: Different Trees Run on Very Different Clocks",
                     "Forests do not move as a single synchronized unit; tree genera lag by 750 to 2,500 years across three speed tiers.")

    bullets = [
        "Statistically Significant Differentiation: Kruskal-Wallis test strongly confirms genus lag differences (H = 34.6, p = 0.0003).",
        "Fast Pioneer Tier (<1,000 yr): Larch (Larix) responded fastest, with a median lag of 750 years [0–2,500 yr CI].",
        "Canopy Reorganization Tier (1,000–2,000 yr): Oak (Quercus), Birch (Betula), Ash (Fraxinus), Elm (Ulmus), Pine (Pinus), and Maple (Acer) all clustered at a median lag of 1,500 years.",
        "Slow Climax Seeders (>2,000 yr): Hemlock (Tsuga) and Beech (Fagus) lagged behind climate by 2,500 years [2,000–3,000 yr CI]."
    ]

    kpis = [
        ("750 yr", "Larix (Larch)", "Fastest Pioneer", COLOR_GREEN),
        ("1,500 yr", "Quercus / Acer", "Canopy Hardwoods", COLOR_BLUE),
        ("2,500 yr", "Fagus / Tsuga", "Slow Climax Seeders", COLOR_VERMILION)
    ]

    add_figure_slide_content(slide, "fig3_genus_lags_raincloud.png", 0.8, 1.65, 5.8, 5.1,
                             6.85, 1.65, 5.68, 3.45,
                             "Three Distinct Ecological Lag Tiers", bullets,
                             "Figure 3 (Panel A): Timeline lollipop plot showing median response lag (years ± 95% CI) behind temperature.",
                             kpis)

    set_notes(slide, 9, "1 min 15s", "11:00",
        "Now we arrive at our first major discovery on slide 9, answering Research Question 1: How long did trees lag behind temperature?\n\n"
        "Look at Panel A of Figure 3. Each row is a different tree genus. The dot represents the median lag time in years, and the horizontal black bar shows the 95% confidence interval.\n\n"
        "The first big takeaway: trees do NOT respond as a synchronized biome! A forest does not move as a single team. Instead, trees separate into three distinct speed tiers:\n\n"
        "Tier 1 at the top: Fast pioneers like Larch (Larix) reacted in 750 years. They produce light, wind-blown seeds that quickly colonized exposed glacial till.\n\n"
        "Tier 2 in the middle: Major canopy trees—Oak, Birch, Ash, Elm, Pine, and Maple—all clustered around a 1,500-year lag. That's 15 centuries to reorganize after a temperature jump!\n\n"
        "Tier 3 at the bottom: Slow climax giants like Beech (Fagus) and Hemlock (Tsuga) lagged by 2,500 years. Their seeds are heavy nuts and cones that take generations to crawl across the map.",
        "But did these lags mean trees were expanding into new land, or dying off? On slide 10, we examine the direction of this reaction.",
        "Q: Why did beech take 2,500 years while larch only took 750 years?\nA: Larch matures in 10-15 years and has tiny winged seeds that blow for miles. Beech produces heavy beechnuts that drop right under the parent tree and take 40 years to produce seed.")


def build_slide_10_rq1_polarity(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_header(slide, "3. Results: RQ1 (Response Lags)", "RQ1: Winners vs. Losers During Deglacial Warming",
                     "Separating cold-tracking boreal retreat from warm-tracking temperate hardwood expansion.")

    bullets = [
        "Response Polarity Breakdown: Examining whether correlation with temperature was negative (cold-tracking retreat) or positive (warm-tracking expansion).",
        "Boreal Conifer Collapse: Spruce (Picea) was 94.9% cold-tracking (negative correlation), with 78% of lakes passing the strict 1,000-surrogate Ebisuzaki test. As temperatures warmed, spruce suffered massive dieback and retreat.",
        "Temperate Hardwood Expansion: Oak (Quercus) was 79.1% warm-tracking (positive correlation), and Maple (Acer) was 67.2% warm-tracking. Warming allowed them to surge into newly deglaciated territory.",
        "The Non-Equilibrium Paradox: Even warm-adapted trees expanding enthusiastically still lagged climate by 1,500 years due to seed dispersal limits."
    ]

    kpis = [
        ("95% Cold", "Picea (Spruce)", "Retreated as it warmed", COLOR_BLUE),
        ("79% Warm", "Quercus (Oak)", "Expanded northward", COLOR_VERMILION),
        ("67% Warm", "Acer (Maple)", "Followed behind Oak", COLOR_ORANGE)
    ]

    add_figure_slide_content(slide, "fig3_genus_lags_raincloud.png", 0.8, 1.65, 5.8, 5.1,
                             6.85, 1.65, 5.68, 3.45,
                             "Biological Direction: Retreat vs. Expansion", bullets,
                             "Figure 3 (Panel B): 100% stacked horizontal bar chart showing % fossil sites cold-retreating (-r) vs warm-expanding (+r).",
                             kpis)

    set_notes(slide, 10, "1 min 15s", "12:15",
        "On slide 10, we look at Panel B of Figure 3, which answers a crucial biological question: When trees lagged, which ones were expanding, and which ones were collapsing?\n\n"
        "In this graph, blue bars show negative correlations—meaning the tree died back as temperatures rose. Orange and red bars show positive correlations—meaning the tree expanded as temperatures rose.\n\n"
        "Look at Spruce (Picea) near the top: 95% of sites are solid blue! 78% of those sites passed our strict 1,000-surrogate Ebisuzaki test. That means when the ice melted, spruce didn't just move—it suffered a massive, catastrophic regional collapse across the lower Midwest.\n\n"
        "Now look at Oak (Quercus) and Maple (Acer): nearly 80% of oak sites are orange and red! Oak was a massive winner during postglacial warming, surging northward into newly thawed land.\n\n"
        "Here is the key paradox: Even though Oak loved the warmth, it still took 1,500 years to reach full abundance. That proves trees live in a chronic state of disequilibrium behind climate.",
        "When cold spruce was dying back while warm oak was moving in, what kinds of forests did they create? That brings us to Research Question 2 on slide 11.",
        "Q: Why did spruce collapse so violently?\nA: As summer temperatures rose above its physiological heat tolerance, spruce suffered drought stress, bark beetle outbreaks, and forest fires, opening the canopy for hardwoods.")


def build_slide_11_rq2_noanalogue(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_header(slide, "3. Results: RQ2 (No-Analogue Forests)", "RQ2: When Weird 'No-Analogue' Forests Appeared",
                     "Novel ecosystems peaked at 38.2% during peak warming and collapsed to 0.0% before European contact.")

    bullets = [
        "Measuring Community Novelty: Squared Chord Distance (SCD) compares fossil pollen samples against 611 modern surface samples. Samples exceeding the modern 5th-percentile threshold (0.138 SCD) are flagged as 'no-analogue'.",
        "Peak Deglacial Novelty: 38.2% of all binned forest samples had no modern match at 14.5 ka BP, coinciding exactly with the Bølling-Allerød warming pulse.",
        "Zero Pre-Colonial Floor: Under TRSH-only woody filtering, no-analogue frequency fell smoothly to exactly 0.0% by 500 BP (pre-settlement late Holocene).",
        "Significantly Correlated with Turnover: Novelty strongly correlates with community turnover rate (Spearman rho = 0.743, Ebisuzaki p = 0.021)."
    ]

    kpis = [
        ("38.2 %", "Peak Novelty", "At 14.5 ka BP", COLOR_VERMILION),
        ("0.0 %", "Pre-Colonial Floor", "At 500 BP (TRSH-only)", COLOR_GREEN),
        ("p = 0.021", "Ebisuzaki Test", "Significant vs turnover", COLOR_BLUE)
    ]

    add_figure_slide_content(slide, "fig4_noanalogue_drivers.png", 0.8, 1.65, 5.8, 5.1,
                             6.85, 1.65, 5.68, 3.45,
                             "Rise and Fall of Novel Deglacial Ecosystems", bullets,
                             "Figure 4 (Top Panel): No-analogue forest prevalence (%) through time alongside absolute climate warming rate.",
                             kpis)

    set_notes(slide, 11, "1 min 15s", "13:30",
        "Now let's examine Research Question 2 on slide 11: What caused 'no-analogue' forests?\n\n"
        "To identify a 'no-analogue' forest, we used a standard ecological metric called Squared Chord Distance. We compared every ancient fossil sample against 611 modern forests across North America. If an ancient pollen sample was more different from any modern forest than 95% of modern forests are from each other, it gets flagged as 'no-analogue'—an extinct community mixture.\n\n"
        "Look at the top panel of Figure 4: 14,500 years ago, no-analogue forests peaked at a staggering 38.2%! More than one out of every three forests in eastern North America was completely unique compared to today.\n\n"
        "Notice when that peak happened: right at the Bølling-Allerød warming spike. But look at where the curve goes as climate stabilized: by 500 years ago, under our clean woody filtering, novel forests dropped to exactly 0.0%!",
        "So what tree species were responsible for making these ancient forests so weird? Let's look at the taxonomic drivers on slide 12.",
        "Q: Why did older papers find high no-analogue percentages right up to the modern era?\nA: Because older papers included agricultural weeds like ragweed! Once we filtered out post-settlement farm weeds, the natural pre-colonial forest proved to be 100% normal.")


def build_slide_12_rq2_drivers(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_header(slide, "3. Results: RQ2 (No-Analogue Forests)", "RQ2: Who Caused the Novel Forests? Spruce & Ash",
                     "Additive Squared Chord Distance (SCD) identifies the specific trees driving community dissimilarity.")

    bullets = [
        "Additive SCD Decomposition: Squared Chord Distance can be broken down taxon-by-taxon to calculate the exact percentage of dissimilarity contributed by each tree.",
        "The Primary Culprit: Spruce (Picea) contributed an enormous mean SCD of 0.161 during early deglaciation, explaining nearly half of the entire novelty signal.",
        "The Secondary Culprit: Black Ash (Fraxinus) contributed 0.057, followed by Birch (Betula) at 0.038.",
        "The Biological Mechanism: During deglaciation, high solar insolation created hot summers with freezing winters. Cold-adapted Spruce and temperate Ash grew side-by-side in unique combinations that vanished once modern climates settled."
    ]

    kpis = [
        ("0.161", "Picea SCD", "Dominant driver (48%)", COLOR_BLUE),
        ("0.057", "Fraxinus SCD", "Secondary driver (17%)", COLOR_VERMILION),
        ("0.038", "Betula SCD", "Tertiary driver (11%)", COLOR_GREEN)
    ]

    add_figure_slide_content(slide, "fig4_noanalogue_drivers.png", 0.8, 1.65, 5.8, 5.1,
                             6.85, 1.65, 5.68, 3.45,
                             "Taxonomic Breakdown of Ancient Novelty", bullets,
                             "Figure 4 (Bottom Panel): Heatmap of taxon-specific Squared Chord Distance (SCD) contributions across 15 ka to 500 BP.",
                             kpis)

    set_notes(slide, 12, "1 min 15s", "14:45",
        "Slide 12 breaks down the mathematical anatomy of these weird forests. Which trees were actually responsible?\n\n"
        "Look at the bottom panel of Figure 4. This heatmap shows the additive contribution of each tree genus to the total dissimilarity score over time. Dark purple and blue show high novelty contributions.\n\n"
        "Look at the top row: Spruce (Picea)! Spruce is by far the biggest driver, contributing an average of 0.161 to the Squared Chord Distance. Right below it is Black Ash (Fraxinus), contributing 0.057.\n\n"
        "Why would Spruce and Ash create a weird forest? Because today, Spruce lives in the cold boreal north of Canada, while Black Ash lives in temperate wetlands. But 14,000 years ago, Earth's orbit created super-high summer sunshine with bitterly cold winters. Cold-tolerant Spruce and wetland Ash grew right next to each other! Once modern seasonality stabilized, that mixture dissolved.",
        "Now, let's turn to Research Question 3: How fast did trees actually migrate across the map? Let's look at slide 13.",
        "Q: Can no-analogue forests happen again in the future?\nA: Yes! As modern climate warming creates novel temperature and rainfall combinations, we expect future forests to scramble into new mixtures that don't exist today.")


def build_slide_13_rq3_isochrones(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_header(slide, "3. Results: RQ3 (2D Migration)", "RQ3: Mapping 15,000 Years of Tree Travel in 2D",
                     "Replacing straight-line 1D assumptions with equal-area planar arrival surfaces and directional vectors.")

    bullets = [
        "Rigorous 2D Planar F-Test: Evaluated all 12 genera on a 2D grid Age(x, y); strictly required p <= 0.05 to avoid hallucinating waves on non-migrating trees.",
        "5 Coherent Migrants Passed: Hickory (Carya), Alder (Alnus), Beech (Fagus), Tamarack (Larix), and Hemlock (Tsuga) showed true landscape-scale migration fronts.",
        "Clipped to Observed Ground: Isochrone contours are clipped strictly to the convex hull of lakes where the tree was actually found.",
        "Directional Azimuth Vectors: Black arrows show local migration direction, revealing major detours around physical barriers."
    ]

    kpis = [
        ("5 Genera", "Statistically Validated", "p_2d <= 0.05", COLOR_GREEN),
        ("7 Genera", "Non-Significant", "Diffuse / multi-refugia", COLOR_SLATE),
        ("Convex Hull", "Strict Masking", "Zero map extrapolation", COLOR_BLUE)
    ]

    add_figure_slide_content(slide, "fig5_migration_isochrones.png", 0.8, 1.65, 5.8, 5.1,
                             6.85, 1.65, 5.68, 3.45,
                             "Real 2D Postglacial Arrival Fronts", bullets,
                             "Figure 5: Postglacial 2D arrival age isochrones (ka BP contours) and local migration azimuth vectors for validated genera.",
                             kpis)

    set_notes(slide, 13, "1 min 15s", "16:00",
        "Now we arrive at Research Question 3 on slide 13: How fast did trees physically move across the map?\n\n"
        "Look at Figure 5. These five maps show the true 2D arrival fronts for the five tree genera that passed our strict statistical test. The colors show arrival ages: dark blue represents early arrival 12,000 years ago, and green and yellow represent arrival 6,000 to 4,000 years ago. The black arrows show the exact compass direction of migration.\n\n"
        "Notice something critical: older studies assumed all trees moved in a straight line due North. But real trees don't have compasses! They have to detour around the Appalachian Mountains, navigate river valleys, and skirt the Great Lakes.\n\n"
        "Out of 12 genera, only 5 showed coherent traveling fronts. The other 7—including Oak and Pine—were already present in multiple diffuse pockets across the landscape.",
        "Let's look at the exact corridors and compass directions these 5 trees followed on slide 14.",
        "Q: Why did 7 genera fail the 2D migration test?\nA: Because trees like Pine and Oak survived the ice age in many small micro-refugia scattered across the south and east, so they expanded locally rather than marching in a single wave.")


def build_slide_14_rq3_corridors(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_header(slide, "3. Results: RQ3 (2D Migration)", "RQ3: The Real Dispersal Corridors Trees Followed",
                     "Tree migration was shaped by river valleys, mountain ridges, and lake basins.")

    headers = ["Genus", "Common Name", "Median Speed", "Full Range", "Compass Heading", "Key Travel Corridor"]
    rows = [
        ["Carya", "Hickory", "277 m/yr", "217–296 m/yr", "65.0° (ENE)", "Mississippi/Ohio valleys toward Atlantic coast"],
        ["Alnus", "Alder", "265 m/yr", "254–278 m/yr", "308.2° (WNW)", "New England across Great Lakes to Minnesota"],
        ["Fagus", "Beech", "170 m/yr", "157–185 m/yr", "344.4° (NNW)", "Southern Appalachians north into New England"],
        ["Larix", "Tamarack", "124 m/yr", "115–129 m/yr", "1.2° (Due North)", "Tracked retreating ice across Upper Midwest"],
        ["Tsuga", "Hemlock", "117 m/yr", "112–120 m/yr", "344.3° (NNW)", "Appalachian mountain spine into Great Lakes"]
    ]

    add_card(slide, 0.8, 1.65, 11.733, 2.1, "Topographic Routing Highlights", [
        "Hickory (Carya) was our fastest migrant at 277 m/yr, spreading East-North-East along warm, fertile river valleys.",
        "Alder (Alnus) moved in a tight diagonal West-North-West corridor (308°), colonizing wet lake margins around the Great Lakes.",
        "Beech and Hemlock moved in parallel North-North-West tracks (344°), clinging to moist Appalachian slopes.",
        "Tamarack (Larix) was the only tree that marched due North (1°), staying glued to the melting edge of the Laurentide ice sheet."
    ], title_color=COLOR_BLUE)

    add_table(slide, 0.8, 4.0, 11.733, 2.8, headers, rows, [Inches(1.5), Inches(1.5), Inches(1.4), Inches(1.5), Inches(1.8), Inches(4.033)])

    set_notes(slide, 14, "1 min 15s", "17:15",
        "Slide 14 provides the exact numbers and geographic details of these five migration corridors.\n\n"
        "Look at the table: Hickory (Carya) was our speed champion at 277 meters per year. But look at its compass heading: 65 degrees East-North-East! It didn't move north; it spread sideways out of the Mississippi and Ohio River valleys toward the Atlantic coast along rich riverbanks.\n\n"
        "Alder (Alnus) was second fastest at 265 meters per year, moving West-North-West at 308 degrees across the St. Lawrence river and the Great Lakes.\n\n"
        "Beech and Hemlock moved at 170 and 117 meters per year along nearly identical North-North-West tracks (344 degrees), climbing along the moist spine of the Appalachian Mountains.\n\n"
        "Finally, Tamarack (Larix) moved at 124 meters per year, and was the only tree that actually headed straight North (1.2 degrees), tracking the edge of the melting ice sheet.",
        "Now, how do these speeds compare to climate change? That brings us to our most important slide: Figure 6 on slide 15.",
        "Q: Why was hickory the fastest migrant?\nA: Hickory produces nutritious nuts carried and cached by squirrels and blue jays, who frequently bury nuts hundreds of meters ahead of the forest front.")


def build_slide_15_rq3_deficit(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_header(slide, "3. Results: RQ3 (2D Migration)", "RQ3: The Massive Speed Deficit vs. Modern Warming",
                     "Real trees hit a biological ceiling below 300 m/yr—falling nearly an order of magnitude behind modern climate.")

    bullets = [
        "A Hard Biological Ceiling: Even our fastest tree, Hickory (Carya), maxed out at 296 m/yr (median 277 m/yr), and slow conifers moved at 117 m/yr.",
        "Slower Than Past Deglaciation: Every single tree genus migrated slower than the past abrupt deglacial climate velocity (p95 = 332 m/yr, blue dashed line).",
        "The 9.3x Contemporary Climate Deficit: Modern anthropogenic warming is moving climate zones at ~1,574 m/yr (orange dashed line, based on 1.9°C/century warming).",
        "The Takeaway: Real tree migration falls roughly an order of magnitude short of contemporary climate velocity, creating an unprecedented tracking deficit."
    ]

    kpis = [
        ("170 m/yr", "Median Tree Speed", "Biological limit", COLOR_GREEN),
        ("332 m/yr", "Past Climate Speed", "p95 deglacial rate", COLOR_BLUE),
        ("1,574 m/yr", "Modern Climate Speed", "1.9 °C / century", COLOR_VERMILION),
        ("9.3 ×", "Velocity Deficit", "Modern gap", COLOR_VERMILION)
    ]

    add_figure_slide_content(slide, "fig6_velocity_deficit.png", 0.8, 1.65, 5.8, 5.1,
                             6.85, 1.65, 5.68, 3.45,
                             "Comparing Tree Speeds to Climate Velocities", bullets,
                             "Figure 6: Log-scale migration velocity deficit showing validated 2D migration medians and full spatial surface ranges vs. climate.",
                             kpis)

    set_notes(slide, 15, "1 min 15s", "18:30",
        "Slide 15 shows Figure 6, which is the defining punchline of our entire study. Please look closely at this chart.\n\n"
        "The horizontal axis is speed in meters per year on a logarithmic scale. The green dots and whiskers show the actual 2D speeds of our trees, from 117 meters per year for hemlock up to 277 meters per year for hickory.\n\n"
        "Now look at the blue dashed vertical line at 332 meters per year. That is the 95th-percentile speed of past natural climate change. Notice that NOT A SINGLE TREE crossed the blue line! Every tree genus was strictly slower than past rapid warming.\n\n"
        "Now look all the way to the right at the dashed orange line: 1,574 meters per year! That is the speed modern climate zones are shifting north under 1.9 degrees Celsius of global warming per century.\n\n"
        "Look at the giant gap between the green dots and the orange line! Modern warming is moving 9.3 times faster than median tree migration. Trees simply cannot walk that fast.",
        "To make sure our results were completely bulletproof, we performed several sensitivity stress-tests on slide 16.",
        "Q: How is modern climate velocity calculated?\nA: By dividing the projected warming rate (1.9°C per century) by the geographic temperature gradient (0.00121°C per km), which equals ~1,574 meters per year.")


def build_slide_16_sensitivity(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_header(slide, "4. Sensitivity & Robustness", "Stress-Testing Our Results: Age Uncertainty & Bin Tests",
                     "Rigorous validation proves our findings are robust and not sensitive to analytical choices.")

    cards = [
        ("LegacyAge N=50 Monte Carlo", [
            "We drew 50 random realizations of radiocarbon calibration curves across all 69 lake cores.",
            "Result: The cross-genus median response lag remained locked at exactly 1,500 years across all 50 iterations.",
            "Proves our lag ordering is completely insensitive to radiocarbon dating jitter."
        ], COLOR_BLUE),
        ("Halving Bin Size: 250-Year Check", [
            "We doubled temporal resolution, running our entire pipeline on 250-year bins (66 cores, 3,365 bins).",
            "Result: Taxonomic ordering was identical—Larch remained fastest, Canopy hardwoods in the middle, and Beech/Hemlock slowest.",
            "Proves 500-year binning did not blur or distort the true biological ranking."
        ], COLOR_VERMILION),
        ("1,000 Ebisuzaki Surrogate Test", [
            "Testing correlations against 1,000 synthetic climate series.",
            "Result: 78.4% of Picea lag pairs and 67.2% of Quercus lag pairs beat 95% of randomized surrogates.",
            "Proves our temperature correlations reflect real physical responses, not statistical flukes."
        ], COLOR_GREEN)
    ]

    for idx, (title, bullets, col) in enumerate(cards):
        add_card(slide, 0.8 + idx * 3.98, 1.7, 3.75, 5.2, title, bullets, title_color=col)

    set_notes(slide, 16, "1 min 15s", "19:45",
        "On slide 16, we ask a tough question that every good scientist must ask: 'Could our results just be an artifact of how we set up the code?'\n\n"
        "We ran three extensive sensitivity audits to prove our results are rock solid:\n\n"
        "First, we ran a 50-member Monte Carlo simulation resampling carbon-14 dating uncertainty. Across all 50 runs, the median tree lag stayed locked at 1,500 years.\n\n"
        "Second, we doubled our time resolution by cutting the bin size in half—from 500 years down to 250 years. That gave us over 3,300 time bins, and the exact same fast-to-slow taxonomic hierarchy was reproduced.\n\n"
        "Third, our 1,000-surrogate Ebisuzaki test proved that over 78% of spruce retreat signals and 67% of oak expansion signals beat 95% of randomized climate surrogates.",
        "Now, let's step back and look at the biology. Why do trees lag behind climate by 15 centuries? Let's explore that on slide 17.",
        "Q: Why did you test 250-year bins if 500-year was your main choice?\nA: To ensure that bin width didn't hide sub-millennial lag dynamics. Both bin widths gave identical biological conclusions.")


def build_slide_17_ecology(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_header(slide, "4. Ecological Synthesis", "Why Do Trees Lag? Three Biological Bottlenecks",
                     "Understanding the physical and ecological mechanisms that prevent instantaneous forest tracking.")

    cards = [
        ("1. Generation Time & Seed Weight", [
            "Delayed Sexual Maturity: Unlike annual weeds, forest trees take 15 to 40 years just to produce their first viable seed.",
            "Mast Seeding Cycles: Heavy nuts (oaks, beech) only produce major seed crops once every 3 to 7 years.",
            "Seed Dispersal Limits: Most heavy nuts fall within 30 meters of the mother tree unless carried by animals."
        ], COLOR_BLUE),
        ("2. Slow Soil Maturation (Pedogenesis)", [
            "Glacial Till is Raw Rock: When glaciers retreat, they leave behind bare gravel and crushed rock with zero organic matter.",
            "It takes centuries of weathering, moss growth, and nitrogen-fixing pioneers (like Alder) to build rich topsoil.",
            "Climax hardwoods (like Beech and Maple) cannot survive until soil biology and fungi fully mature."
        ], COLOR_VERMILION),
        ("3. Canopy Inertia & Competition", [
            "Old Trees Don't Leave Easily: A mature forest canopy shades out incoming seedlings and buffers ground microclimates.",
            "Even if the regional climate is now ideal for oak, existing pine and birch canopies block oak seedlings for centuries.",
            "New trees can only break through when old trees die from fire, disease, or windstorms."
        ], COLOR_GREEN)
    ]

    for idx, (title, bullets, col) in enumerate(cards):
        add_card(slide, 0.8 + idx * 3.98, 1.7, 3.75, 5.2, title, bullets, title_color=col)

    set_notes(slide, 17, "1 min 15s", "21:00",
        "Slide 17 explores the biology behind the numbers: Why do trees lag behind climate by 1,500 to 2,500 years? There are three major bottlenecks:\n\n"
        "Bottleneck 1: Generation time and seed weight. Annual plants produce seeds in a few months. But a beech tree takes 40 years before it produces a single nut! Furthermore, beech nuts are heavy; they roll 20 or 30 feet from the trunk. Moving a forest 500 miles takes thousands of generations.\n\n"
        "Bottleneck 2: Soil building. When a glacier melts, it leaves behind barren gravel and crushed stone. You cannot plant a sugar maple in bare crushed rock! It takes centuries of weathering, lichen growth, and nitrogen-fixing shrubs like alder to build living topsoil.\n\n"
        "Bottleneck 3: Canopy competition. An established forest has enormous inertia. Even when the climate becomes too warm for spruce, mature spruce trees keep shading the ground, preventing oak seedlings from getting sunlight until the old canopy dies off.",
        "Knowing these three bottlenecks, what does this mean for today's climate crisis? Let's look at slide 18.",
        "Q: Does animal dispersal help speed up migration?\nA: Yes, birds like blue jays and rodents like squirrels help disperse nuts, but even with animal caching, maximum dispersal rarely exceeds 200 to 300 meters per year.")


def build_slide_18_conservation(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_header(slide, "5. Implications & Limitations", "What This Means for Today's Climate Crisis",
                     "Translating paleoecological discoveries into actionable modern conservation policy.")

    cards = [
        ("1. Natural Migration Will Fail", [
            "Modern warming velocity (1,574 m/yr) is nearly 10x faster than historical tree dispersal speeds (117–277 m/yr).",
            "Left alone, long-lived trees simply cannot walk fast enough to stay within their suitable temperature zones.",
            "Expect widespread trailing-edge dieback and forest decline along southern species boundaries."
        ], COLOR_VERMILION),
        ("2. Landscape Fragmentation Blocks Corridors", [
            "In the postglacial era, trees migrated across contiguous, uninterrupted wild landscapes.",
            "Today, eastern North America is severely fragmented by mega-highways, cities, industrial farms, and suburbs.",
            "The natural East-North-East river corridor that Hickory used is now blocked by human infrastructure."
        ], COLOR_ORANGE),
        ("3. The Necessity of Assisted Migration", [
            "Foresters and conservation managers cannot rely on passive seed dispersal.",
            "We must actively implement Assisted Migration (physically planting southern tree seeds and seedlings hundreds of kilometers north).",
            "Priority must be given to slow-dispersing, heavy-seeded climax species like Beech, Maple, and Hemlock."
        ], COLOR_GREEN)
    ]

    for idx, (title, bullets, col) in enumerate(cards):
        add_card(slide, 0.8 + idx * 3.98, 1.7, 3.75, 5.2, title, bullets, title_color=col)

    set_notes(slide, 18, "1 min 00s", "22:00",
        "Slide 18 connects our 15,000-year study directly to modern conservation.\n\n"
        "First: Natural migration alone will fail. If ancient trees couldn't even keep up with gentle natural warming, expecting modern forests to keep up with warming that is 10 times faster is ecologically impossible.\n\n"
        "Second: Modern fragmentation. 10,000 years ago, a hickory nut carried by a blue jay could land anywhere in unbroken wilderness. Today, it lands on Interstate 80, a cornfield, or a parking lot! Human development has severed natural migration corridors.\n\n"
        "Third: The need for 'Assisted Migration.' If we want temperate hardwoods to survive the 21st century, foresters and conservationists must actively collect seeds from southern populations and plant them in northern forests.",
        "Before concluding, every rigorous scientific study must acknowledge its limitations. Let's look at slide 19.",
        "Q: What is assisted migration in practice?\nA: It means foresters planting tree seedlings 100 to 300 kilometers north of their current natural range so that mature trees are already established when warming arrives.")


def build_slide_19_limitations(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_header(slide, "5. Implications & Limitations", "Honest Scientific Limitations: What We Still Don't Know",
                     "Transparency about analytical boundaries and future research opportunities.")

    cards = [
        ("1. 500-Year Time Windows", [
            "Sediment mixing and deposition rates required 500-year binning.",
            "While robust for multi-millennial trends, it cannot capture sudden decadal extreme weather events (like 5-year mega-droughts).",
            "Future Solution: High-resolution annual varved lake cores."
        ], COLOR_BLUE),
        ("2. Planar 2D Surface Smoothing", [
            "Our 2D planar arrival surfaces capture dominant regional fronts across equal-area coordinates.",
            "However, planar surfaces smooth out micro-topographic detours, such as trees creeping up narrow canyon microclimates.",
            "Future Solution: Non-linear thin-plate splines and terrain modeling."
        ], COLOR_VERMILION),
        ("3. Genus vs. Species Resolution", [
            "Standard pollen grains can usually only be identified to genus level (e.g., Quercus for all oaks, Pinus for all pines).",
            "Red oak vs. white oak may have responded differently.",
            "Future Solution: Ancient sedimentary environmental DNA (sedaDNA) to unlock exact species-level tracking."
        ], COLOR_GREEN)
    ]

    for idx, (title, bullets, col) in enumerate(cards):
        add_card(slide, 0.8 + idx * 3.98, 1.7, 3.75, 5.2, title, bullets, title_color=col)

    set_notes(slide, 19, "1 min 00s", "23:00",
        "Slide 19 highlights three honest limitations in our study:\n\n"
        "First, our 500-year binning. While 500-year windows give a clean signal across thousands of years, they cannot resolve 10-year heat waves or 5-year mega-droughts. Future studies using annual varved lake mud can give finer sub-century resolution.\n\n"
        "Second, planar 2D surfaces. Our planar arrival models capture the broad regional direction of travel, but they smooth out local terrain details like deep river gorges where microclimates allow trees to linger.\n\n"
        "Third, genus versus species. Under a microscope, an oak pollen grain is just 'Quercus'—we cannot easily tell a northern red oak from a southern live oak. Upcoming sedimentary ancient DNA technology will soon allow scientists to identify exact species.",
        "Now, let's wrap up with our three major takeaways on slide 20.",
        "Q: How will ancient environmental DNA improve this in the future?\nA: Ancient eDNA directly detects plant genetic fragments in the mud, allowing us to identify exact species and genetic varieties rather than just general genera.")


def build_slide_20_conclusion(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_header(slide, "5. Conclusions & Takeaways", "Final Wrap-Up: Three Big Discoveries from 15,000 Years",
                     "Synthesizing 69 lake cores, TraCE-21ka climate, and 2D spatial modeling into three core principles.")

    takeaways = [
        ("Takeaway 1: Forests Are Not Synchronized Units (RQ1)", [
            "Trees do not move together as coherent biomes; each genus runs on its own biological clock.",
            "Fast pioneers (Larix) react in 750 years; canopy hardwoods (Oak, Maple) lag by 1,500 years; climax seeders (Beech, Hemlock) lag by 2,500 years.",
            "Warming triggered severe collapse in cold spruce (95% -r) alongside aggressive northward expansion in oak (79% +r)."
        ], COLOR_BLUE),
        ("Takeaway 2: Novel Ecosystems Peak During Rapid Shifts (RQ2)", [
            "Weird 'no-analogue' forests reached 38.2% at 14.5 ka BP during peak Bølling-Allerød warming.",
            "Driven by unique co-occurrences of cold Spruce and temperate wetland Ash under high seasonal contrast.",
            "Novel forests collapsed smoothly to a 0.0% pre-colonial baseline once modern climate stabilized."
        ], COLOR_VERMILION),
        ("Takeaway 3: A Massive 9.3x Modern Tracking Deficit (RQ3)", [
            "True 2D migration routes were bounded by a hard biological ceiling: 117 to 277 m/yr across observed terrain.",
            "Real postglacial trees never outran past climate velocity (332 m/yr), and trail modern warming (1,574 m/yr) by roughly an order of magnitude.",
            "Passive natural dispersal will not save modern forests—active assisted migration is essential."
        ], COLOR_GREEN)
    ]

    for idx, (title, bullets, col) in enumerate(takeaways):
        top_pos = 1.7 + idx * 1.75
        add_card(slide, 0.8, top_pos, 11.733, 1.55, title, bullets, title_color=col)

    set_notes(slide, 20, "1 min 00s", "24:00",
        "To conclude our presentation, here are the three big discoveries to remember:\n\n"
        "Discovery 1: Forests are not synchronized teams. Every tree species has its own personal speedometer, lagging behind climate by 750 to 2,500 years. As climate warmed, spruce collapsed while oak surged north.\n\n"
        "Discovery 2: Rapid warming creates weird, novel ecosystems. Extinct forest mixtures peaked at 38% during the fastest deglacial warming spike, driven by unique mixtures of spruce and black ash.\n\n"
        "Discovery 3: Trees face an unprecedented modern speed deficit. Real trees hit a physical speed limit between 117 and 277 meters per year. Modern global warming is moving climate zones at 1,574 meters per year—more than 9 times faster! Trees cannot walk that fast on their own.\n\n"
        "Thank you so much for your time and attention! We would be delighted to open the floor to any questions.",
        "We also have two technical backup slides prepared if the committee wishes to discuss 1D vs 2D mathematical differences or statistical parameters.",
        "Q: What is the single most important message of your project for a general audience?\nA: Climate change moves in decades, but forests move in centuries. We cannot expect trees to naturally migrate out of harm's way without active human assistance.")


def build_slide_21_backup_math(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_header(slide, "Backup Slide (Q&A)", "Why Older 1D Methods Overestimated Tree Speeds",
                     "Technical breakdown: 1D regression slope inversion artifacts vs. true 2D vector gradients.")

    cards = [
        ("The Math Glitch in Older 1D Models", [
            "In older studies, migration speed was modeled as: Arrival Age = beta_0 + beta_1 * Latitude.",
            "Speed was calculated by inverting the slope: Speed = 1 / beta_1.",
            "Because core counts were modest, the standard error on beta_1 was large.",
            "When the lower confidence bound (beta_1 - t * SE) approached zero, taking 1 / slope exploded asymptotically toward infinity!",
            "This falsely produced speeds of 500 to 600+ m/yr that crossed the past climate line (332 m/yr)."
        ], COLOR_VERMILION),
        ("The Straight-North Blindspot", [
            "1D regression forced an assumption that trees only traveled due North (0° azimuth).",
            "If a tree took 2,000 years to migrate 500 km East along a river valley around a mountain range, a 1D model saw near-zero Northward distance.",
            "This caused 1D models to misinterpret sideways dispersal as instantaneous, distorting physical speed estimates."
        ], COLOR_ORANGE),
        ("Why 2D Equal-Area Modeling is Physically Honest", [
            "We fitted planar arrival surfaces Age(x, y) in Albers equal-area coordinates (km).",
            "Speed is calculated as the true gradient: Speed = 1 / sqrt(beta_x^2 + beta_y^2).",
            "Calculates speed along the actual physical front (e.g. Hickory at 65° ENE; Alder at 308° WNW).",
            "Across the observed landscape (convex hulls), speeds hit a physical biological ceiling: 117 to 277 m/yr (max 296 m/yr), strictly below past climate velocity (332 m/yr)."
        ], COLOR_BLUE)
    ]

    for idx, (title, bullets, col) in enumerate(cards):
        add_card(slide, 0.8 + idx * 3.98, 1.7, 3.75, 5.2, title, bullets, title_color=col)

    set_notes(slide, 21, "Backup", "Buffer",
        "BACKUP SLIDE 1 (Q&A): Use this slide if someone asks: 'Why did some older literature papers claim trees moved at 500 or 600 meters per year, while you found only 277 meters per year?'\n\n"
        "Explain the math glitch in older 1D models: They ran a simple linear regression: Arrival Age = Slope * Latitude, and then flipped the slope upside down: Speed = 1 / Slope.\n\n"
        "Because data was noisy, the lower bound of their slope touched almost zero. And what is 1 divided by a number close to zero? Infinity! That math artifact blew up their confidence intervals past 600 meters per year.\n\n"
        "Furthermore, 1D models assumed trees only traveled due North. In reality, hickory traveled East-North-East, and alder traveled Northwest. Our 2D equal-area surface measures speed along the actual ground front, giving an honest biological ceiling under 300 m/yr.",
        "Transition back to Q&A or to Slide 22 for statistical parameters.")


def build_slide_22_backup_params(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_header(slide, "Backup Slide (Q&A)", "Master Statistical & Methodological Parameter Reference",
                     "Complete reference table of analytical thresholds, calibration parameters, and test criteria.")

    headers = ["Parameter / Step", "Scientific Value Used", "Methodological Rationale & Reference"]
    rows = [
        ["Study Corridor", "25°–50°N, 95°–65°W", "Eastern North American temperate-boreal transition zone"],
        ["Sediment Cores", "69 continuous lakes (1,706 bins)", "Min 150 grains/sample, min 4 continuous 500-yr bins"],
        ["Age-Model System", "LegacyAge 1.0 (Li et al. 2022)", "Calibrated Bayesian radiocarbon chronologies (PANGAEA Table-S5)"],
        ["Age Uncertainty", "N = 50 Monte Carlo draws", "Resampled depth-age bounds; cross-genus median lag locked at 1,500 yr"],
        ["Pollen Productivity", "REVEALS RPP Multipliers", "Wieczorek & Herzschuh (2020) & Dawson et al. (2016)"],
        ["Taxon Filtering", "TRSH-only (Woody Taxa)", "Isolates arboreal trees & shrubs; drops post-settlement farm weeds"],
        ["No-Analogue Metric", "Squared Chord Distance (SCD)", "Threshold = 0.138 (modern 5th percentile across 611 surface sites)"],
        ["Stationary Lag Test", "First-differencing (Δy_t vs ΔT_t-k)", "Removes 15 ka trend; tests against 1,000 Ebisuzaki surrogates"],
        ["2D Arrival Surface", "Age(x, y) = b0 + bx*x + by*y", "Albers Equal-Area (EPSG:5070); gated by planar F-test (p <= 0.05)"],
        ["Modern Climate Velocity", "1,574 m/yr (range 1,242–2,071)", "1.9°C/century warming / 0.00121°C/km regional spatial gradient"]
    ]

    add_table(slide, 0.8, 1.7, 11.733, 5.2, headers, rows, [Inches(2.5), Inches(3.2), Inches(6.033)])

    set_notes(slide, 22, "Backup", "Buffer",
        "BACKUP SLIDE 2 (Q&A): Use this slide if a professor asks for exact statistical parameters, thresholds, or citations.\n\n"
        "Key points to cite from this master table:\n"
        "1. Pollen calibration: Empirical REVEALS Relative Pollen Productivity from Wieczorek & Herzschuh (2020).\n"
        "2. Chronologies: Li et al. (2022) LegacyAge 1.0 from PANGAEA Table-S5.\n"
        "3. No-analogue threshold: 0.138 Squared Chord Distance based on the 5th percentile of 611 modern surface samples.\n"
        "4. Surrogate testing: 1,000 Ebisuzaki phase-randomized surrogate time series.\n"
        "5. Modern climate velocity: Calculated from 1.9°C/century warming divided by the 0.00121°C/km regional thermal gradient, giving 1,574 meters per year.",
        "Transition back to general Q&A.")


def add_table(slide, left, top, width, height, headers, rows, col_widths=None):
    """Draws a cleanly formatted presentation table."""
    num_rows = len(rows) + 1
    num_cols = len(headers)
    table_shape = slide.shapes.add_table(num_rows, num_cols, Inches(left), Inches(top), Inches(width), Inches(height))
    table = table_shape.table

    if col_widths and len(col_widths) == num_cols:
        for idx, w in enumerate(col_widths):
            table.columns[idx].width = w

    # Header Row
    for col_idx, header_text in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_INK
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        p.text = header_text
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        p.font.name = "Segoe UI"

    # Data Rows
    for row_idx, row_data in enumerate(rows):
        bg_col = CARD_BG if row_idx % 2 == 0 else CARD_MUTED_BG
        for col_idx, cell_value in enumerate(row_data):
            cell = table.cell(row_idx + 1, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg_col
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cell.text_frame.paragraphs[0]
            p.text = str(cell_value)
            p.font.size = Pt(9.5)
            p.font.name = "Segoe UI"
            if col_idx == 0:
                p.font.bold = True
                p.font.color.rgb = COLOR_INK
            elif col_idx == 1:
                p.font.color.rgb = COLOR_SLATE
            else:
                p.font.color.rgb = COLOR_INK


def main():
    print("[ppt] initializing presentation...")
    prs = create_base_deck()

    print("[ppt] building 22 slides...")
    build_slide_01_title(prs)
    build_slide_02_context(prs)
    build_slide_03_questions(prs)
    build_slide_04_data_network(prs)
    build_slide_05_climate_trace(prs)
    build_slide_06_methods_cleaning(prs)
    build_slide_07_methods_stats(prs)
    build_slide_08_results_climate(prs)
    build_slide_09_rq1_lags(prs)
    build_slide_10_rq1_polarity(prs)
    build_slide_11_rq2_noanalogue(prs)
    build_slide_12_rq2_drivers(prs)
    build_slide_13_rq3_isochrones(prs)
    build_slide_14_rq3_corridors(prs)
    build_slide_15_rq3_deficit(prs)
    build_slide_16_sensitivity(prs)
    build_slide_17_ecology(prs)
    build_slide_18_conservation(prs)
    build_slide_19_limitations(prs)
    build_slide_20_conclusion(prs)
    build_slide_21_backup_math(prs)
    build_slide_22_backup_params(prs)

    prs.save(str(PPTX_OUT))
    print(f"[ppt] successfully saved presentation to: {PPTX_OUT}")


if __name__ == "__main__":
    main()
