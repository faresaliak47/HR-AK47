"""
Master theme for TURF Landscape Co. — HR Pro
Brand design system derived from the TURF Landscape Co. logo
(#106454 deep green + neutral grays), modern enterprise look.
"""
import os

# ── Brand identity ────────────────────────────────────────────────
COMPANY_NAME    = "TURF Landscape Co."
COMPANY_TAGLINE = "Create Scenic Views"

_ASSETS_DIR        = os.path.join(os.path.dirname(__file__), "..", "assets")
LOGO_PATH          = os.path.join(_ASSETS_DIR, "turf_logo.jpg")              # white background — use on light surfaces (login)
LOGO_TRANSPARENT   = os.path.join(_ASSETS_DIR, "turf_logo_transparent.png")  # transparent — use on dark surfaces (sidebar)

# ── Single source of truth for every color in the app ────────────
# All UI (sidebar, buttons, cards, tables, forms, tabs, charts, metrics,
# exports) reads colors from this dict — no hardcoded hex anywhere else.
COLORS = {
    # Brand primary — directly from the TURF logo
    "primary":      "#106454",   # brand green
    "primary_dark": "#0B4A3D",   # darker shade for depth/hover
    "primary_light":"#1C8A72",   # lighter shade for gradients/highlights
    "secondary":    "#6B7280",   # neutral gray, from the logo's gray frame
    "accent":       "#B08D57",   # warm bronze accent for variety in charts/KPIs

    "bg":           "#F4F8F6",   # light, faint-green-tinted background
    "surface":      "#FFFFFF",

    "sidebar_bg":   "#0B3A30",   # deep brand-green sidebar (dark variant of primary)
    "sidebar_item": "#0F4A3C",
    "sidebar_hover":"#156B59",

    "success":      "#1FAE7E",
    "warning":      "#E0A23B",
    "danger":       "#E0524C",
    "info":         "#2D8FA0",

    "text":         "#1F2A27",
    "text_muted":   "#6B7280",
    "border":       "#DCE6E2",
    "shadow":       "rgba(16,100,84,0.12)",
}

MONTH_NAMES = [
    'يناير','فبراير','مارس','إبريل','مايو','يونيو',
    'يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر'
]


def inject_global_css():
    """Inject full global CSS — call once from app.py."""
    import streamlit as st
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;500;600;700;800;900&display=swap');

:root {{
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --radius-xl: 20px;
    --space-1: 4px;
    --space-2: 8px;
    --space-3: 12px;
    --space-4: 16px;
    --space-5: 20px;
    --space-6: 24px;
    --shadow-sm: 0 1px 2px rgba(16,40,34,0.05), 0 1px 1px rgba(16,40,34,0.04);
    --shadow-md: 0 4px 16px rgba(16,40,34,0.07);
    --shadow-lg: 0 10px 28px rgba(16,40,34,0.10);
}}

/* Force our Arabic brand font everywhere EXCEPT Streamlit's own native
   Material-icon spans ([data-testid="stIconMaterial"]). Those spans'
   *text content* is literally the icon's ligature name (e.g.
   "keyboard_double_arrow_left") which only renders as an arrow glyph
   under Streamlit's own bundled icon font — forcing Cairo onto them
   like every other element used to make that raw name show up as
   plain giant text instead of an icon (this is exactly what caused
   the literal "double_arrow_left" text some users saw near the top of
   the sidebar). */
*:not([data-testid="stIconMaterial"]), *::before, *::after {{
    font-family: 'Cairo', 'Segoe UI', Arial, sans-serif !important;
    box-sizing: border-box;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}}

html, body, .stApp {{
    direction: rtl !important;
    background: {COLORS['bg']} !important;
    color: {COLORS['text']} !important;
    line-height: 1.6 !important;
    width: 100% !important;
    max-width: 100% !important;
}}

/* Force main content to use all available space */
.main, [data-testid="stAppViewContainer"] > .main {{
    width: 100% !important;
    max-width: 100% !important;
}}

h1, h2, h3, h4, h5, h6 {{
    letter-spacing: -0.3px !important;
    font-weight: 800 !important;
}}
p, span, label, div {{
    letter-spacing: 0 !important;
}}
::selection {{
    background: {COLORS['primary']}33;
}}

/* ═══ HIDE STREAMLIT CHROME ═══ */
#MainMenu, footer, .stDeployButton {{visibility: hidden;}}
header[data-testid="stHeader"] {{background: transparent !important; min-height: 0; display:none;}}
[data-testid="stToolbar"] {{display:none;}}
[data-testid="stDecoration"] {{display:none;}}

/* ═══ HIDE double-arrow collapse button (all known selectors,
   across Streamlit versions — the internal testid for this button
   has been renamed more than once: collapsedControl → stSidebarCollapsedControl
   → stSidebarCollapseButton. The wildcard catches any future rename. ═══ */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid*="SidebarCollapse"],
[data-testid*="ollapsedControl"],
button[data-testid="baseButton-headerNoPadding"],
button[aria-label="Close sidebar"],
button[aria-label="Open sidebar"],
.st-emotion-cache-1cypcdb,
button[kind="header"] {{
    display: none !important;
}}

/* ═══ SIDEBAR ═══ */
section[data-testid="stSidebar"] {{
    background: {COLORS['sidebar_bg']} !important;
    border-left: none !important;
    border-right: none !important;
    padding: 0 !important;
    width: 265px !important;
    min-width: 265px !important;
    max-width: 265px !important;
    box-shadow: 4px 0 24px rgba(0,0,0,0.3) !important;
    transition: width 0.3s ease, min-width 0.3s ease !important;
}}
section[data-testid="stSidebar"] > div:first-child {{
    padding: 0 !important;
}}
section[data-testid="stSidebar"] * {{
    color: #d7e9e3 !important;
}}

/* ── Nav list ── */
section[data-testid="stSidebar"] .stRadio > div {{
    gap: 2px !important;
    flex-direction: column;
}}
/* Hide the radio group label ("القائمة") */
section[data-testid="stSidebar"] .stRadio > label {{
    display: none !important;
}}
section[data-testid="stSidebar"] .stRadio label {{
    display: flex !important;
    align-items: center !important;
    padding: 11px 16px !important;
    margin: 2px 8px !important;
    border-radius: 10px !important;
    cursor: pointer !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    color: #a9c9bf !important;
    transition: background 0.2s ease, color 0.2s ease, box-shadow 0.2s ease !important;
    background: transparent !important;
    gap: 10px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}
section[data-testid="stSidebar"] .stRadio label:hover {{
    background: rgba(28,138,114,0.35) !important;
    color: #fff !important;
}}
section[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {{
    font-size: 13.5px !important;
    color: inherit !important;
    margin: 0 !important;
}}
/* Hide radio circle bullets entirely */
section[data-testid="stSidebar"] .stRadio input[type="radio"] {{
    display: none !important;
}}
section[data-testid="stSidebar"] .stRadio div[data-testid="stRadioGroup"] > label > div:first-child {{
    display: none !important;
}}
section[data-testid="stSidebar"] .stRadio div[data-baseweb="radio"] {{
    display: none !important;
}}
/* Highlight the currently selected nav item (modern browsers) */
section[data-testid="stSidebar"] .stRadio label:has(input:checked) {{
    background: linear-gradient(135deg, {COLORS['primary_light']}, {COLORS['primary']}) !important;
    color: #fff !important;
    box-shadow: 0 3px 10px rgba(0,0,0,0.25) !important;
}}

/* ═══ RESPONSIVE — hide sidebar on narrow screens ═══ */
@media (max-width: 768px) {{
    section[data-testid="stSidebar"] {{
        width: 0 !important;
        min-width: 0 !important;
        overflow: hidden !important;
    }}
    .main .block-container,
    [data-testid="stMainBlockContainer"] {{
        padding: 1rem 0.9rem 1.75rem !important;
        max-width: 100% !important;
        width: 100% !important;
    }}

    /* Topbar / page-header: stack title and the date/avatar cluster so
       neither gets squeezed on narrow screens */
    [data-testid="stMarkdownContainer"] div[style*="justify-content:space-between"] {{
        flex-wrap: wrap !important;
        row-gap: 10px !important;
    }}

    /* ── Stack columns vertically on mobile (Dashboard KPI cards,
       Attendance/Overtime entry inputs & buttons) ──────────────── */
    [data-testid="stHorizontalBlock"] {{
        flex-direction: column !important;
    }}
    [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }}

    /* Full-width inputs and stacked, full-width buttons on mobile */
    .stTextInput, .stNumberInput, .stTextArea, .stSelectbox,
    .stDateInput, .stMultiSelect, .stButton, [data-testid="stForm"] {{
        width: 100% !important;
    }}
    .stButton > button {{
        width: 100% !important;
    }}
    .kpi-hover {{
        margin: 7px 0 !important;
    }}
    [data-testid="stForm"] {{
        padding: 20px 18px 16px !important;
    }}

    /* ── Tables / Reports / Matrix: keep the desktop table layout
       intact and only allow horizontal scrolling on mobile — do
       NOT shrink or restructure the table itself. ───────────────── */
    .stDataFrame {{
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
        max-width: 100% !important;
    }}
    .stDataFrame > div {{
        overflow-x: auto !important;
    }}
    .stDataFrame table {{
        width: max-content !important;
        min-width: 100% !important;
    }}

    /* This grid (bulk-overtime employee selection) is a real row-aligned
       table built from st.columns, not a stacked input form — keep its
       desktop row layout and just allow horizontal scroll on mobile. */
    .st-key-bulk_ot_emp_table {{
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
    }}
    .st-key-bulk_ot_emp_table [data-testid="stHorizontalBlock"] {{
        flex-direction: row !important;
        min-width: 560px !important;
    }}
    .st-key-bulk_ot_emp_table [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
        width: auto !important;
        min-width: unset !important;
        flex: initial !important;
    }}
}}

/* ═══ MAIN CONTENT ═══ */
.main .block-container {{
    padding: 1.5rem 2rem 2.5rem !important;
    max-width: 100% !important;
    width: 100% !important;
    background: {COLORS['bg']};
}}
/* Streamlit newer versions use stMainBlockContainer */
[data-testid="stMainBlockContainer"] {{
    max-width: 100% !important;
    width: 100% !important;
    padding: 1.5rem 2rem 2.5rem !important;
}}
/* Vertical rhythm — enough breathing room between stacked sections */
[data-testid="stVerticalBlock"] > div {{
    margin-bottom: 10px;
}}
/* Column padding — balanced gutters between cards */
[data-testid="column"] {{ padding: 0 8px !important; }}
/* Horizontal blocks — comfortable gap between columns */
[data-testid="stHorizontalBlock"] {{
    gap: 16px;
    align-items: stretch !important;
}}

/* ═══ BUTTONS ═══ */
.stButton > button {{
    border-radius: 9px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 9px 22px !important;
    transition: all 0.2s ease !important;
    border: none !important;
    letter-spacing: 0 !important;
}}
.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['primary_light']} 100%) !important;
    color: #fff !important;
    box-shadow: 0 4px 15px {COLORS['shadow']} !important;
}}
.stButton > button[kind="primary"]:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 26px {COLORS['shadow']} !important;
    opacity: 0.95 !important;
}}
.stButton > button[kind="primary"]:active {{
    transform: translateY(0) !important;
    box-shadow: 0 3px 10px {COLORS['shadow']} !important;
}}
.stButton > button[kind="secondary"] {{
    background: #fff !important;
    color: {COLORS['primary']} !important;
    border: 1.5px solid {COLORS['border']} !important;
}}
.stButton > button[kind="secondary"]:hover {{
    background: {COLORS['primary']}0d !important;
    border-color: {COLORS['primary']} !important;
    transform: translateY(-1px) !important;
}}
.stButton > button:focus-visible {{
    outline: 2px solid {COLORS['primary']}66 !important;
    outline-offset: 1px !important;
}}
.stButton > button:disabled {{
    opacity: 0.5 !important;
    transform: none !important;
    box-shadow: none !important;
    cursor: not-allowed !important;
}}

/* ═══ INPUTS ═══ */
.stTextInput input, .stNumberInput input, .stTextArea textarea,
.stSelectbox select, [data-baseweb="input"] input {{
    border-radius: 9px !important;
    border: 1.5px solid {COLORS['border']} !important;
    padding: 10px 14px !important;
    background: #fff !important;
    color: {COLORS['text']} !important;
    -webkit-text-fill-color: {COLORS['text']} !important;
    font-size: 14px !important;
    min-height: 42px !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}}
.stTextInput input::placeholder, .stTextArea textarea::placeholder {{
    color: {COLORS['text_muted']} !important;
    opacity: 0.7 !important;
}}
.stTextInput input:hover, .stNumberInput input:hover, .stTextArea textarea:hover {{
    border-color: {COLORS['primary']}66 !important;
}}
.stTextInput input:focus, .stNumberInput input:focus,
.stTextArea textarea:focus {{
    border-color: {COLORS['primary']} !important;
    box-shadow: 0 0 0 3px {COLORS['primary']}1f !important;
    outline: none !important;
}}
.stTextInput label, .stNumberInput label, .stTextArea label,
.stSelectbox label, .stDateInput label, .stMultiSelect label {{
    font-weight: 600 !important;
    font-size: 13px !important;
    color: {COLORS['text']} !important;
    margin-bottom: 7px !important;
}}
/* Helper / caption text under inputs */
.stTextInput [data-testid="stWidgetLabelHelp"],
[data-testid="stCaptionContainer"] {{
    color: {COLORS['text_muted']} !important;
}}
/* Consistent breathing room above every labelled widget */
.stTextInput, .stNumberInput, .stTextArea, .stSelectbox,
.stDateInput, .stMultiSelect, .stCheckbox {{
    margin-bottom: 6px !important;
}}

/* ═══ SELECT / DROPDOWN — STRUCTURE-AGNOSTIC VISIBILITY FIX ═══
   The previous version of this fix guessed at BaseWeb's internal DOM
   (specific nesting depth, class names containing "singleValue" etc.).
   That's fragile: in a production build those class names are usually
   minified/hashed with no readable substring left, and the exact
   nesting can differ by Streamlit version — which is exactly why
   the selected employee name could end up not just unreadable, but
   completely blank, with no text visible in the box at all.

   This version makes no assumption about internal structure:
   - [data-baseweb="select"] itself (the one attribute Streamlit always
     sets, regardless of version) gets ALL the visual chrome — border,
     background, sizing. This is the only element styled with an
     opaque background.
   - Literally everything nested inside it — input, span, div,
     whatever tag/class BaseWeb happens to use — is forced to a
     transparent background and the correct, visible text color. That
     guarantees no inner wrapper can ever paint an opaque layer over
     the real text, and no text node can end up invisible because we
     missed its specific class name.                                  */

[data-baseweb="select"] {{
    border-radius: 9px !important;
    border: 1.5px solid {COLORS['border']} !important;
    background: #ffffff !important;
    min-height: 42px !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}}
[data-baseweb="select"]:hover {{
    border-color: {COLORS['primary']}66 !important;
}}
[data-baseweb="select"]:focus-within {{
    border-color: {COLORS['primary']} !important;
    box-shadow: 0 0 0 3px {COLORS['primary']}1f !important;
}}

/* Every descendant: no opaque backgrounds, no invisible text, no
   dimmed opacity — whatever tag/class it turns out to be. */
[data-baseweb="select"] * {{
    background: transparent !important;
    color: {COLORS['text']} !important;
    -webkit-text-fill-color: {COLORS['text']} !important;
    opacity: 1 !important;
    border: none !important;
}}

/* Placeholder text (no employee chosen yet) gets the muted color —
   applied after the wildcard above so it wins for this specific case. */
[data-baseweb="select"] div[class*="placeholder"] {{
    color: {COLORS['text_muted']} !important;
    -webkit-text-fill-color: {COLORS['text_muted']} !important;
}}

/* The real type-to-search <input> still needs a working caret and
   needs its OWN raw text (the in-progress search query) to never
   visually double up with the selected-value text next to it — paint
   its glyphs via text-shadow instead of color, since text-shadow
   can't be hijacked by `-webkit-text-fill-color` games on any browser. */
[data-baseweb="select"] input {{
    color: transparent !important;
    -webkit-text-fill-color: transparent !important;
    text-shadow: 0 0 0 {COLORS['text']} !important;
    caret-color: {COLORS['text']} !important;
}}

/* ── Multi-select tags (selected employee chips) ── */
[data-baseweb="tag"] {{
    background: {COLORS['primary']}18 !important;
    border: 1px solid {COLORS['primary']}44 !important;
    border-radius: 6px !important;
}}
[data-baseweb="tag"] span,
[data-baseweb="tag"] [data-baseweb="tag-text"] {{
    color: {COLORS['primary_dark']} !important;
    font-weight: 600 !important;
    font-size: 13px !important;
}}
[data-baseweb="tag"] button,
[data-baseweb="tag"] [data-baseweb="icon"] {{
    color: {COLORS['primary']} !important;
}}
[data-baseweb="tag"]:hover {{
    background: {COLORS['primary']}28 !important;
}}

/* ── Dropdown popover menu ── */
[data-baseweb="popover"],
[data-baseweb="menu"],
[data-baseweb="menu"] ul,
ul[data-baseweb="menu"] {{
    background: #ffffff !important;
    border: 1px solid {COLORS['border']} !important;
    border-radius: 10px !important;
    box-shadow: 0 8px 28px {COLORS['shadow']} !important;
    padding: 4px !important;
}}

/* ── Every option row inside the popover ── */
[data-baseweb="menu"] li,
[data-baseweb="menu"] [role="option"],
[role="listbox"] [role="option"],
[role="option"] {{
    color: {COLORS['text']} !important;
    background: #ffffff !important;
    border-radius: 7px !important;
    padding: 9px 14px !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    transition: background 0.15s, color 0.15s !important;
}}

/* ── Option hover ── */
[data-baseweb="menu"] li:hover,
[data-baseweb="menu"] [role="option"]:hover,
[role="listbox"] [role="option"]:hover,
[role="option"]:hover {{
    background: {COLORS['primary']}12 !important;
    color: {COLORS['primary_dark']} !important;
}}

/* ── Option focused (keyboard navigation) ── */
[data-baseweb="menu"] li:focus,
[data-baseweb="menu"] [role="option"]:focus,
[role="option"]:focus,
[data-baseweb="menu"] li[data-highlighted],
[role="option"][data-highlighted] {{
    background: {COLORS['primary']}18 !important;
    color: {COLORS['primary_dark']} !important;
    outline: none !important;
}}

/* ── Currently selected option (the checkmarked one) ── */
[aria-selected="true"][role="option"],
[data-baseweb="menu"] li[aria-selected="true"],
[role="listbox"] [aria-selected="true"] {{
    background: {COLORS['primary']}16 !important;
    color: {COLORS['primary']} !important;
    font-weight: 700 !important;
}}
[aria-selected="true"][role="option"]:hover,
[data-baseweb="menu"] li[aria-selected="true"]:hover {{
    background: {COLORS['primary']}24 !important;
    color: {COLORS['primary_dark']} !important;
}}

/* ── Any text node inside an option (Arabic names) ── */
[role="option"] span,
[role="option"] p,
[role="option"] div,
[data-baseweb="menu"] li span,
[data-baseweb="menu"] li div,
[data-baseweb="menu"] li p {{
    color: inherit !important;
}}

/* ── Dropdown chevron / indicator icons ── */
[data-baseweb="select"] [data-baseweb="icon"],
[data-baseweb="select"] svg {{
    color: {COLORS['text_muted']} !important;
    fill:  {COLORS['text_muted']} !important;
}}

/* ── Date input calendar picker ── */
.stDateInput input {{
    border-radius: 8px !important;
    border: 1.5px solid {COLORS['border']} !important;
    background: #ffffff !important;
    color: {COLORS['text']} !important;
}}

/* ── Dark-mode guard: force white background + dark text on all
   select controls so system dark-mode can't flip them ── */
@media (prefers-color-scheme: dark) {{
    [data-baseweb="select"] > div,
    [data-baseweb="select"] > div > div,
    [data-baseweb="select"] > div > div > div {{
        background: #ffffff !important;
        color: {COLORS['text']} !important;
    }}
    [data-baseweb="popover"],
    [data-baseweb="menu"],
    [data-baseweb="menu"] ul {{
        background: #ffffff !important;
    }}
    [data-baseweb="menu"] li,
    [role="option"] {{
        background: #ffffff !important;
        color: {COLORS['text']} !important;
    }}
    [data-baseweb="tag"] span,
    [data-baseweb="tag"] [data-baseweb="tag-text"] {{
        color: {COLORS['primary_dark']} !important;
    }}
}}

/* Checkbox / radio accent */
/* Checkbox / radio accent */
input[type="checkbox"], input[type="radio"] {{
    accent-color: {COLORS['primary']} !important;
}}
[data-testid="stCheckbox"] label p {{
    font-size: 14px !important;
}}

/* ═══ TABS ═══ */
.stTabs [data-baseweb="tab-list"] {{
    background: {COLORS['surface']} !important;
    border-radius: 12px !important;
    padding: 5px !important;
    gap: 3px !important;
    border-bottom: none !important;
    box-shadow: 0 2px 12px {COLORS['shadow']} !important;
    margin-bottom: 14px !important;
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 9px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 9px 20px !important;
    color: {COLORS['text_muted']} !important;
    border: none !important;
    transition: all 0.2s !important;
}}
.stTabs [data-baseweb="tab"]:hover {{
    background: {COLORS['primary']}0d !important;
    color: {COLORS['primary']} !important;
}}
.stTabs [aria-selected="true"] {{
    background: linear-gradient(135deg, {COLORS['primary']}, {COLORS['primary_light']}) !important;
    color: #fff !important;
    box-shadow: 0 4px 12px {COLORS['shadow']} !important;
}}
.stTabs [aria-selected="true"]:hover {{
    color: #fff !important;
}}
.stTabs [data-baseweb="tab-panel"] {{
    padding: 0 !important;
}}

/* ═══ DATAFRAME ═══ */
.stDataFrame {{
    border-radius: var(--radius-lg) !important;
    overflow: hidden !important;
    box-shadow: var(--shadow-md) !important;
    border: 1px solid {COLORS['border']} !important;
}}
.stDataFrame table {{
    font-size: 13.5px !important;
    font-variant-numeric: tabular-nums;
}}
.stDataFrame thead tr th {{
    background: {COLORS['primary']}0d !important;
    font-weight: 700 !important;
    color: {COLORS['primary']} !important;
    font-size: 12.5px !important;
    letter-spacing: 0.2px !important;
    padding-top: 12px !important;
    padding-bottom: 12px !important;
    border-bottom: 2px solid {COLORS['primary']}22 !important;
    position: sticky !important;
    top: 0 !important;
    z-index: 2 !important;
}}
.stDataFrame tbody tr td {{
    padding-top: 9px !important;
    padding-bottom: 9px !important;
    border-bottom: 1px solid {COLORS['border']}99 !important;
}}
.stDataFrame tbody tr:last-child td {{
    border-bottom: none !important;
}}
.stDataFrame tbody tr:nth-child(even) {{
    background: {COLORS['bg']} !important;
}}
.stDataFrame tbody tr:hover {{
    background: {COLORS['primary']}12 !important;
}}
/* Card wrapper feel: a touch of breathing room above every table */
.stDataFrame {{
    margin-top: 6px;
}}

/* ═══ METRICS ═══ */
[data-testid="metric-container"] {{
    background: {COLORS['surface']} !important;
    border-radius: var(--radius-lg) !important;
    padding: 16px 18px !important;
    border: 1px solid {COLORS['border']} !important;
    box-shadow: var(--shadow-sm) !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease !important;
}}
[data-testid="metric-container"]:hover {{
    transform: translateY(-2px) !important;
    box-shadow: var(--shadow-md) !important;
    border-color: {COLORS['primary']}33 !important;
}}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {{
    font-size: 12.5px !important;
    color: {COLORS['text_muted']} !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.3px !important;
}}
[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    font-size: 25px !important;
    font-weight: 800 !important;
    color: {COLORS['primary']} !important;
    font-variant-numeric: tabular-nums;
    margin-top: 4px !important;
}}
[data-testid="stMetricDelta"] svg {{
    display: inline !important;
}}

/* ═══ ALERTS ═══ */
.stAlert {{
    border-radius: 10px !important;
    border: none !important;
    font-size: 14px !important;
}}

/* ═══ FORMS ═══ */
[data-testid="stForm"] {{
    background: {COLORS['surface']} !important;
    border-radius: var(--radius-xl) !important;
    padding: 28px 28px 22px !important;
    border: 1px solid {COLORS['border']} !important;
    border-top: 3px solid {COLORS['primary']} !important;
    box-shadow: var(--shadow-md) !important;
}}
/* Breathing room between fields inside a form — clearer vertical rhythm
   than the page-level default so multi-field forms read as distinct rows */
[data-testid="stForm"] [data-testid="stVerticalBlock"] > div {{
    margin-bottom: 14px;
}}
[data-testid="stForm"] [data-testid="stHorizontalBlock"] {{
    gap: 16px;
    margin-bottom: 6px;
}}
/* Extra gap before the submit button row so it doesn't crowd the last field */
[data-testid="stForm"] [data-testid="stFormSubmitButton"] {{
    margin-top: 10px !important;
}}
[data-testid="stForm"] [data-testid="stFormSubmitButton"] > button {{
    padding: 11px 22px !important;
    font-size: 14.5px !important;
}}
/* Calculated read-only metrics inside a form get a soft tinted backdrop
   so they read as "derived values", distinct from editable fields */
[data-testid="stForm"] [data-testid="metric-container"] {{
    background: {COLORS['bg']} !important;
    box-shadow: none !important;
    border: 1px dashed {COLORS['border']} !important;
}}
[data-testid="stForm"] [data-testid="metric-container"]:hover {{
    transform: none !important;
}}

/* ═══ EXPANDER ═══ */
.streamlit-expanderHeader {{
    background: {COLORS['surface']} !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    border: 1px solid {COLORS['border']} !important;
    transition: all 0.2s !important;
}}
.streamlit-expanderHeader:hover {{
    border-color: {COLORS['primary']} !important;
    background: {COLORS['primary']}08 !important;
}}

/* ═══ ANIMATIONS ═══ */
@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(20px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes fadeIn {{
    from {{ opacity: 0; }}
    to   {{ opacity: 1; }}
}}
@keyframes slideInRight {{
    from {{ opacity: 0; transform: translateX(20px); }}
    to   {{ opacity: 1; transform: translateX(0); }}
}}
@keyframes pulse-glow {{
    0%, 100% {{ box-shadow: 0 0 0 0 rgba(16,100,84,0.3); }}
    50%       {{ box-shadow: 0 0 0 8px rgba(16,100,84,0); }}
}}

.fade-in-up  {{ animation: fadeInUp  0.45s ease both; }}
.fade-in     {{ animation: fadeIn    0.3s ease both; }}
.slide-in    {{ animation: slideInRight 0.4s ease both; }}

/* ═══ SCROLLBAR ═══ */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: {COLORS['bg']}; border-radius: 3px; }}
::-webkit-scrollbar-thumb {{
    background: {COLORS['primary']}55;
    border-radius: 3px;
}}
::-webkit-scrollbar-thumb:hover {{ background: {COLORS['primary']}; }}

/* ═══ FILE UPLOADER ═══ */
[data-testid="stFileUploaderDropzone"] {{
    border-radius: 12px !important;
    border: 2px dashed {COLORS['primary']}55 !important;
    background: {COLORS['primary']}05 !important;
    transition: all 0.2s !important;
}}
[data-testid="stFileUploaderDropzone"]:hover {{
    border-color: {COLORS['primary']} !important;
    background: {COLORS['primary']}10 !important;
}}

/* ═══ DATE INPUT ═══ */
.stDateInput input {{
    border-radius: 8px !important;
    border: 1.5px solid {COLORS['border']} !important;
}}

/* ═══ SPINNER ═══ */
.stSpinner > div {{
    border-top-color: {COLORS['primary']} !important;
}}

/* ═══ DOWNLOAD BUTTON ═══ */
[data-testid="stDownloadButton"] > button {{
    background: linear-gradient(135deg, {COLORS['success']}, #20a55a) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}}

/* ═══ PROGRESS BAR ═══ */
.stProgress > div > div > div {{
    background: linear-gradient(90deg, {COLORS['primary']}, {COLORS['primary_light']}) !important;
    border-radius: 4px !important;
}}

/* ═══ SIDEBAR DIVIDER ═══ */
.sidebar-divider {{
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
    margin: 8px 16px;
}}

/* ═══ KPI CARD HOVER ═══ */
.kpi-hover:hover {{
    transform: translateY(-3px) !important;
    box-shadow: var(--shadow-lg) !important;
}}

/* Card hover effect */
.emp-card:hover {{
    transform: translateY(-3px) !important;
    box-shadow: 0 8px 28px {COLORS['shadow']} !important;
    border-color: {COLORS['primary']}44 !important;
}}

/* Section separator */
.section-sep {{
    height: 1px;
    background: {COLORS['border']};
    margin: 20px 0;
}}
</style>
""", unsafe_allow_html=True)
