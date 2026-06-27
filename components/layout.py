"""Layout helpers — sidebar, topbar, wrappers."""
import streamlit as st
import base64
from datetime import date
from components.theme import COLORS, COMPANY_NAME, COMPANY_TAGLINE, LOGO_TRANSPARENT

NAV_ITEMS = [
    ("📊", "لوحة التحكم",           "dashboard"),
    ("👥", "الموظفون",               "employees"),
    ("📅", "الحضور والغياب",        "attendance"),
    ("⏱",  "الأوفر تايم",           "overtime"),
    ("⏱⏱", "أوفر تايم جماعي",      "bulk_overtime"),
    ("💰", "السلف",                  "advances"),
    ("💼", "مسير الرواتب",          "payroll"),
    ("📈", "التقارير",               "reports"),
    ("💵", "المصروفات والخزينة",    "expenses"),
]

NAV_LABELS = [f"{icon} {label}" for icon, label, _ in NAV_ITEMS]


def _logo_data_uri(path: str) -> str:
    """Read a logo file from disk and return it as a base64 data URI."""
    try:
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        ext = "png" if path.lower().endswith("png") else "jpeg"
        return f"data:image/{ext};base64,{encoded}"
    except Exception as e:
        print(f"[layout] Could not load logo from {path!r}: {e}")
        return ""


def render_sidebar(extra_items: list = None) -> str:
    """Render the sidebar and return the selected page label."""
    extra_items = extra_items or []
    all_items  = NAV_ITEMS + extra_items
    all_labels = [f"{icon} {label}" for icon, label, _ in all_items]

    with st.sidebar:
        # ── Logo / Brand ──────────────────────────────
        logo_uri = _logo_data_uri(LOGO_TRANSPARENT)
        logo_html = (
            f'<img src="{logo_uri}" style="width:46px;height:46px;object-fit:contain;flex-shrink:0;" />'
            if logo_uri else '<div style="font-size:22px;">🌳</div>'
        )
        st.markdown(f"""
<div style="
    padding: 22px 18px 16px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 6px;
    background: linear-gradient(180deg, rgba(28,138,114,0.25) 0%, transparent 100%);
">
  <div style="display:flex;align-items:center;gap:12px;">
    {logo_html}
    <div>
      <div style="font-size:15px;font-weight:800;color:#fff;line-height:1.2;letter-spacing:-0.3px;">{COMPANY_NAME}</div>
      <div style="font-size:10px;color:#9bcdbf;margin-top:2px;font-weight:500;">{COMPANY_TAGLINE}</div>
    </div>
  </div>
  <div style="margin-top:12px;background:rgba(28,138,114,0.3);border-radius:6px;padding:5px 10px;display:inline-block;">
    <span style="font-size:10px;color:#cdeae0;font-weight:600;">HR Pro · v 3.0.0 Enterprise</span>
  </div>
</div>
""", unsafe_allow_html=True)

        st.markdown("""
<p style="font-size:9.5px;font-weight:700;color:#5c8d80;
          letter-spacing:1.8px;text-transform:uppercase;
          padding:12px 20px 4px;margin:0;">
  القائمة الرئيسية
</p>""", unsafe_allow_html=True)

        selected = st.radio(
            "القائمة الرئيسية",
            all_labels,
            label_visibility="collapsed",
        )

        st.markdown("""
<div style="height:1px;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.08),transparent);margin:10px 16px 4px;"></div>
""", unsafe_allow_html=True)

        # ── User profile bottom ───────────────────────
        full_name = st.session_state.get('full_name', 'مستخدم')
        username  = st.session_state.get('username', '')
        initials  = full_name[0] if full_name else 'م'

        st.markdown(f"""
<div style="
    padding:14px 16px 8px;
    border-top:1px solid rgba(255,255,255,0.08);
    margin-top:12px;
">
  <div style="display:flex;align-items:center;gap:10px;">
    <div style="
        background:linear-gradient(135deg,{COLORS['primary']},{COLORS['primary_light']});
        border-radius:10px;
        width:36px;height:36px;
        display:flex;align-items:center;justify-content:center;
        font-size:16px;color:#fff;font-weight:700;flex-shrink:0;
        box-shadow:0 3px 10px rgba(16,100,84,0.4);
    ">{initials}</div>
    <div style="flex:1;min-width:0;">
      <div style="font-size:13px;font-weight:700;color:#e3f3ee;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{full_name}</div>
      <div style="font-size:10px;color:#5c8d80;">{username}</div>
    </div>
    <div style="width:8px;height:8px;background:{COLORS['success']};border-radius:50%;box-shadow:0 0 6px {COLORS['success']}88;"></div>
  </div>
</div>
""", unsafe_allow_html=True)

    return selected


def render_topbar(page_title: str, page_icon: str = "", breadcrumb: str = ""):
    """Render a top bar with page title, breadcrumb, and current date."""
    today = date.today()
    day_names   = ['الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']
    month_names = ['يناير','فبراير','مارس','إبريل','مايو','يونيو',
                   'يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر']
    date_str = f"{day_names[today.weekday()]}، {today.day} {month_names[today.month-1]} {today.year}"

    breadcrumb_html = ""
    if breadcrumb:
        breadcrumb_html = f"""
<div style="font-size:11px;color:{COLORS['text_muted']};margin-bottom:4px;display:flex;align-items:center;gap:6px;">
  <span>الرئيسية</span>
  <span style="opacity:0.4;">›</span>
  <span style="color:{COLORS['primary']};font-weight:600;">{breadcrumb}</span>
</div>"""

    full_name = st.session_state.get('full_name', 'مستخدم')
    initials  = full_name[0] if full_name else 'م'

    st.markdown(f"""
<div class="fade-in" style="
    background:{COLORS['surface']};
    border-radius:14px;
    padding:14px 22px;
    margin-bottom:16px;
    display:flex;
    justify-content:space-between;
    align-items:center;
    box-shadow:0 2px 14px {COLORS['shadow']};
    border:1px solid {COLORS['border']};
">
  <div>
    {breadcrumb_html}
    <div style="display:flex;align-items:center;gap:10px;">
      <div style="
          background:linear-gradient(135deg,{COLORS['primary']},{COLORS['primary_light']});
          border-radius:10px;width:38px;height:38px;
          display:flex;align-items:center;justify-content:center;
          font-size:18px;flex-shrink:0;
          box-shadow:0 3px 10px {COLORS['shadow']};
      ">{page_icon}</div>
      <span style="font-size:19px;font-weight:800;color:{COLORS['text']};letter-spacing:-0.3px;">{page_title}</span>
    </div>
  </div>
  <div style="display:flex;align-items:center;gap:12px;">
    <div style="
        background:{COLORS['primary']}0d;
        border:1px solid {COLORS['primary']}22;
        border-radius:20px;padding:7px 16px;
        font-size:12px;color:{COLORS['primary']};font-weight:600;
        display:flex;align-items:center;gap:6px;
    ">
      <span style="font-size:14px;">📅</span>
      <span>{date_str}</span>
    </div>
    <div style="
        background:linear-gradient(135deg,{COLORS['primary']},{COLORS['primary_light']});
        border-radius:10px;width:36px;height:36px;
        display:flex;align-items:center;justify-content:center;
        font-size:16px;color:#fff;font-weight:700;
        box-shadow:0 3px 10px {COLORS['shadow']};
    ">{initials}</div>
  </div>
</div>
""", unsafe_allow_html=True)
