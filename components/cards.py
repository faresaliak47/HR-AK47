"""Reusable card components for Odoo Mini HR Pro v2."""
import streamlit as st
from components.theme import COLORS


def kpi_card(col, icon: str, label: str, value, color: str,
             sub_label: str = "", trend: str = None):
    """Clean, modern KPI card: white surface, colored icon chip and top
    accent bar, bold neutral value. Keeps the same call signature so every
    existing caller (dashboard, payroll) works unchanged."""
    trend_html = ""
    if trend:
        trend_html = (
            f'<span style="background:{color}14;color:{color};border-radius:20px;'
            f'padding:3px 10px;font-size:11px;font-weight:700;">{trend}</span>'
        )

    sub_html = (
        f'<p style="margin:6px 0 0;font-size:12px;color:{COLORS["text_muted"]};font-weight:500;">{sub_label}</p>'
        if sub_label else ""
    )

    col.markdown(f"""
<div class="fade-in-up kpi-hover" style="
    background: {COLORS['surface']};
    border-radius: 16px;
    padding: 20px 22px;
    margin: 0;
    border: 1px solid {COLORS['border']};
    box-shadow: var(--shadow-sm, 0 1px 3px rgba(16,40,34,0.06));
    position: relative;
    overflow: hidden;
    cursor: default;
    transition: transform 0.25s cubic-bezier(.4,0,.2,1), box-shadow 0.25s, border-color 0.25s;
">
  <div style="position:absolute;top:0;left:0;right:0;height:3px;background:{color};"></div>
  <div style="display:flex;justify-content:space-between;align-items:flex-start;">
    <div style="
        background:{color}14;color:{color};
        border-radius:11px;width:40px;height:40px;
        display:flex;align-items:center;justify-content:center;
        font-size:18px;flex-shrink:0;
    ">{icon}</div>
    {trend_html}
  </div>
  <p style="color:{COLORS['text_muted']};font-size:12px;font-weight:600;margin:16px 0 6px;letter-spacing:.2px;">{label}</p>
  <p style="color:{COLORS['text']};font-size:28px;font-weight:800;margin:0;line-height:1.15;letter-spacing:-0.5px;font-variant-numeric:tabular-nums;">{value}</p>
  {sub_html}
</div>
""", unsafe_allow_html=True)


def section_card(title: str, icon: str = "", color: str = None):
    """White section card header with colored right border."""
    c = color or COLORS['primary']
    st.markdown(f"""
<div style="
    background:{COLORS['surface']};
    border-radius:12px;
    padding:16px 20px;
    margin-bottom:14px;
    border-right:4px solid {c};
    box-shadow:0 2px 14px {COLORS['shadow']};
    display:flex;align-items:center;gap:12px;
    border-left:1px solid {COLORS['border']};
    border-top:1px solid {COLORS['border']};
    border-bottom:1px solid {COLORS['border']};
">
  <div style="background:{c}15;border-radius:10px;padding:8px;font-size:18px;line-height:1;display:flex;">{icon}</div>
  <span style="font-size:16px;font-weight:700;color:{COLORS['text']};">{title}</span>
</div>
""", unsafe_allow_html=True)


def info_banner(message: str, icon: str = "ℹ️", color: str = None):
    """Styled info banner."""
    c = color or COLORS['info']
    st.markdown(f"""
<div style="
    background:{c}12;
    border:1px solid {c}44;
    border-radius:10px;
    padding:12px 18px;
    margin:8px 0;
    display:flex;align-items:flex-start;gap:10px;
    direction:rtl;
">
  <span style="font-size:18px;flex-shrink:0;">{icon}</span>
  <span style="font-size:13px;color:{COLORS['text']};line-height:1.7;">{message}</span>
</div>
""", unsafe_allow_html=True)


def status_badge(status: str) -> str:
    """Return HTML badge string for employee status."""
    cfg = {
        'Active':    (COLORS['success'], 'نشط'),
        'Inactive':  (COLORS['text_muted'], 'غير نشط'),
        'Suspended': (COLORS['danger'], 'موقوف'),
    }
    color, label = cfg.get(status, (COLORS['text_muted'], status))
    return (f'<span style="background:{color}20;color:{color};'
            f'border-radius:20px;padding:3px 12px;font-size:11px;'
            f'font-weight:700;white-space:nowrap;border:1px solid {color}44;">{label}</span>')


def employee_card(col, code: str, name: str, job_title: str,
                  department: str, status: str, salary: float):
    """Professional employee profile card with hover effect."""
    initials = "".join([w[0] for w in name.split()[:2]]) if name else "؟"
    avatar_colors = {
        'Active':    (COLORS['primary'], '#fff'),
        'Inactive':  (COLORS['text_muted'], '#fff'),
        'Suspended': (COLORS['danger'], '#fff'),
    }
    av_bg, av_fg = avatar_colors.get(status, (COLORS['primary'], '#fff'))
    badge = status_badge(status)

    col.markdown(f"""
<div class="fade-in-up emp-card" style="
    background:{COLORS['surface']};
    border-radius:16px;
    padding:20px;
    margin:6px 0;
    border:1px solid {COLORS['border']};
    box-shadow:0 2px 14px {COLORS['shadow']};
    transition:transform 0.2s cubic-bezier(.4,0,.2,1),box-shadow 0.2s,border-color 0.2s;
    cursor:default;
">
  <div style="display:flex;align-items:center;gap:14px;margin-bottom:14px;">
    <div style="
        background:linear-gradient(135deg,{av_bg},{av_bg}cc);
        color:{av_fg};border-radius:14px;
        width:52px;height:52px;
        display:flex;align-items:center;justify-content:center;
        font-size:19px;font-weight:800;flex-shrink:0;
        box-shadow:0 4px 12px {av_bg}44;
    ">{initials}</div>
    <div style="flex:1;min-width:0;">
      <div style="font-size:15px;font-weight:700;color:{COLORS['text']};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{name}</div>
      <div style="font-size:12px;color:{COLORS['text_muted']};margin-top:2px;">{job_title or '—'}</div>
    </div>
    {badge}
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
    <div style="background:{COLORS['bg']};border-radius:8px;padding:8px 10px;">
      <div style="font-size:10px;color:{COLORS['text_muted']};font-weight:600;margin-bottom:2px;">القسم</div>
      <div style="font-size:13px;font-weight:700;color:{COLORS['primary']};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{department or '—'}</div>
    </div>
    <div style="background:{COLORS['bg']};border-radius:8px;padding:8px 10px;">
      <div style="font-size:10px;color:{COLORS['text_muted']};font-weight:600;margin-bottom:2px;">الراتب</div>
      <div style="font-size:13px;font-weight:700;color:{COLORS['success']};">{salary:,.0f} ج.م</div>
    </div>
  </div>
  <div style="margin-top:10px;padding-top:10px;border-top:1px solid {COLORS['border']};font-size:11px;color:{COLORS['text_muted']};display:flex;align-items:center;gap:6px;">
    <span style="background:{COLORS['primary']}12;border-radius:4px;padding:2px 8px;font-weight:600;color:{COLORS['primary']};">#{code}</span>
  </div>
</div>
""", unsafe_allow_html=True)


def empty_state(message: str = "لا توجد بيانات", icon: str = "📭",
                hint: str = "أضف بيانات جديدة للبدء"):
    """Professional empty state placeholder."""
    st.markdown(f"""
<div class="fade-in" style="
    text-align:center;
    padding:64px 20px;
    background:{COLORS['surface']};
    border-radius:18px;
    border:2px dashed {COLORS['border']};
    margin:20px 0;
">
  <div style="font-size:60px;margin-bottom:16px;opacity:0.3;">{icon}</div>
  <div style="font-size:18px;font-weight:700;color:{COLORS['text']};margin-bottom:8px;">{message}</div>
  <div style="font-size:13px;color:{COLORS['text_muted']};">{hint}</div>
</div>
""", unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "", icon: str = ""):
    """Top-of-page header with gradient accent."""
    st.markdown(f"""
<div class="fade-in" style="
    background:linear-gradient(135deg,{COLORS['primary']} 0%,{COLORS['primary_light']} 100%);
    border-radius:16px;
    padding:22px 28px;
    margin-bottom:24px;
    color:#fff;
    box-shadow:0 6px 24px {COLORS['shadow']};
    position:relative;
    overflow:hidden;
">
  <div style="position:absolute;top:-30px;right:-30px;width:150px;height:150px;border-radius:50%;background:rgba(255,255,255,0.05);"></div>
  <div style="display:flex;align-items:center;gap:14px;position:relative;">
    <span style="font-size:34px;">{icon}</span>
    <div>
      <div style="font-size:22px;font-weight:800;line-height:1.2;letter-spacing:-0.3px;">{title}</div>
      {'<div style="font-size:13px;opacity:0.8;margin-top:5px;">'+subtitle+'</div>' if subtitle else ''}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


def success_toast(message: str):
    st.markdown(f"""
<div class="fade-in-up" style="
    background:{COLORS['success']}12;
    border:1px solid {COLORS['success']}55;
    border-radius:10px;padding:12px 18px;
    display:flex;align-items:center;gap:10px;
    margin:8px 0;
">
  <span style="font-size:18px;">✅</span>
  <span style="font-size:14px;font-weight:600;color:{COLORS['success']};">{message}</span>
</div>
""", unsafe_allow_html=True)


def danger_toast(message: str):
    st.markdown(f"""
<div class="fade-in-up" style="
    background:{COLORS['danger']}12;
    border:1px solid {COLORS['danger']}55;
    border-radius:10px;padding:12px 18px;
    display:flex;align-items:center;gap:10px;
    margin:8px 0;
">
  <span style="font-size:18px;">❌</span>
  <span style="font-size:14px;font-weight:600;color:{COLORS['danger']};">{message}</span>
</div>
""", unsafe_allow_html=True)


def warning_toast(message: str):
    st.markdown(f"""
<div class="fade-in-up" style="
    background:{COLORS['warning']}12;
    border:1px solid {COLORS['warning']}55;
    border-radius:10px;padding:12px 18px;
    display:flex;align-items:center;gap:10px;
    margin:8px 0;
">
  <span style="font-size:18px;">⚠️</span>
  <span style="font-size:14px;font-weight:600;color:{COLORS['warning']};">{message}</span>
</div>
""", unsafe_allow_html=True)


def stat_pills(stats: list):
    """
    Render a horizontal row of stat pills.
    stats: list of (icon, label, value, color) tuples
    """
    pills_html = ""
    for icon, label, value, color in stats:
        pills_html += f"""
<div style="background:{COLORS['surface']};border:1px solid {COLORS['border']};border-radius:12px;
            padding:10px 18px;display:flex;align-items:center;gap:10px;
            box-shadow:0 1px 3px rgba(16,40,34,0.05);flex:1 1 auto;min-width:150px;">
  <div style="background:{color}14;color:{color};border-radius:9px;width:32px;height:32px;
              display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0;">{icon}</div>
  <div style="min-width:0;">
    <div style="font-size:10.5px;color:{COLORS['text_muted']};font-weight:600;white-space:nowrap;">{label}</div>
    <div style="font-size:14.5px;font-weight:800;color:{color};white-space:nowrap;">{value}</div>
  </div>
</div>"""

    st.markdown(f"""
<div style="display:flex;gap:10px;flex-wrap:wrap;margin:14px 0;">
  {pills_html}
</div>
""", unsafe_allow_html=True)


def confirm_delete_section(item_name: str = "هذا العنصر") -> bool:
    """Render a styled confirmation checkbox before delete."""
    confirmed = st.checkbox(f"⚠️ تأكيد حذف: {item_name}")
    return confirmed


def data_card(title: str, content_html: str, icon: str = "", color: str = None):
    """Generic white data card with title."""
    c = color or COLORS['primary']
    st.markdown(f"""
<div class="fade-in" style="
    background:{COLORS['surface']};
    border-radius:14px;
    padding:20px;
    margin-bottom:16px;
    border:1px solid {COLORS['border']};
    box-shadow:0 2px 14px {COLORS['shadow']};
">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;padding-bottom:12px;border-bottom:1px solid {COLORS['border']};">
    <span style="font-size:18px;">{icon}</span>
    <span style="font-size:15px;font-weight:700;color:{COLORS['text']};">{title}</span>
  </div>
  {content_html}
</div>
""", unsafe_allow_html=True)
