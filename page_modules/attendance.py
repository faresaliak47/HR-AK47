import streamlit as st
import pandas as pd
from datetime import date
from database.db import get_db
from database.models import Employee, Attendance
from services.attendance_service import (
    process_attendance, get_attendance_matrix,
    parse_smart_attendance_text, process_smart_attendance,
)
from components.cards import (section_card, empty_state, info_banner,
                               success_toast, danger_toast, stat_pills)
from components.layout import render_topbar
from components.theme import COLORS, MONTH_NAMES


def show():
    render_topbar("الحضور والغياب", "📅", "الحضور والغياب")
    tab1, tab2, tab3, tab4 = st.tabs([
        "🧠 إدخال ذكي",
        "📝 إدخال عادي",
        "🗂️ مصفوفة الحضور",
        "📋 سجلات الحضور",
    ])
    with tab1: _smart_attendance()
    with tab2: _input_attendance()
    with tab3: _attendance_matrix()
    with tab4: _attendance_records()


# ── Smart Attendance Tab ──────────────────────────────────────────

def _smart_attendance():
    section_card("الإدخال الذكي للحضور", "🧠", COLORS['primary'])

    info_banner(
        "أدخل النص الحر مباشرة — كل سطر موظف.<br>"
        "<b>بدون رقم:</b> عدد العمال = 1 تلقائياً<br>"
        "<b>بدون تاريخ:</b> يُستخدم تاريخ اليوم تلقائياً<br>"
        "<b>مثال:</b> <code>6 عمال سامح</code> → سامح، 6 عمال | <code>خالد طارق</code> → خالد طارق، 1 عامل",
        "💡", COLORS['primary']
    )

    # ── Sample placeholder ────────────────────────────────────────
    sample = """20/06/2025
خالد طارق
أسامة علي
6 عمال سامح
7 عمال مختار
2 عمال أشرف"""

    text = st.text_area(
        "📋 الصق النص هنا:",
        placeholder=sample,
        height=220,
        help="السطر الأول تاريخ اختياري (DD/MM/YYYY)، ثم الأسماء",
        key="smart_att_input",
    )

    # ── Live Preview ──────────────────────────────────────────────
    if text.strip():
        att_date, entries, errors = parse_smart_attendance_text(text)

        if errors:
            st.error(" | ".join(errors))
        else:
            # Date display
            st.markdown(
                f"<div style='background:{COLORS['info']}18;border:1px solid {COLORS['info']}33;"
                f"border-radius:8px;padding:8px 16px;margin:8px 0;font-size:13px;"
                f"color:{COLORS['info']};font-weight:600;'>📅 التاريخ المُحدَّد: {att_date.strftime('%d/%m/%Y')}</div>",
                unsafe_allow_html=True,
            )

            # Parsed entries table preview
            total_workers = sum(e['workers_count'] for e in entries)
            st.markdown(
                f"<div style='background:{COLORS['success']}12;border:1px solid {COLORS['success']}30;"
                f"border-radius:8px;padding:8px 16px;margin:4px 0 10px;font-size:13px;"
                f"color:{COLORS['success']};font-weight:700;'>"
                f"✅ تم تحليل {len(entries)} سطر — إجمالي العمال: {total_workers}</div>",
                unsafe_allow_html=True,
            )

            preview_df = pd.DataFrame([
                {
                    "الاسم المُستخرَج": e['name'],
                    "عدد العمال":       e['workers_count'],
                }
                for e in entries
            ])
            st.dataframe(preview_df, use_container_width=True, hide_index=True, height=min(300, 40 + len(entries) * 36))

            # ── Save Button ───────────────────────────────────────
            st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
            col_save, _ = st.columns([1, 3])
            if col_save.button("💾 حفظ الحضور", type="primary", use_container_width=True, key="smart_save_btn"):
                with st.spinner("جاري الحفظ..."):
                    result = process_smart_attendance(text)

                if result['success']:
                    success_toast(
                        f"✅ تم حفظ حضور يوم {result['date'].strftime('%d/%m/%Y')} بنجاح!"
                    )

                    stat_pills([
                        ("✅", "تم الحفظ",       str(result['saved']),          COLORS['success']),
                        ("🔁", "مكرر (تجاهل)",  str(result['duplicates']),     COLORS['warning']),
                        ("⚠️", "غير متطابق",    str(len(result['unmatched'])), COLORS['danger']),
                    ])

                    if result['matched']:
                        with st.expander(f"✅ الموظفون المطابقون ({len(result['matched'])})", expanded=False):
                            cols = st.columns(3)
                            for i, entry in enumerate(result['matched']):
                                worker_badge = (
                                    f" <span style='background:{COLORS['primary']}22;border-radius:4px;"
                                    f"padding:1px 6px;font-size:11px;'>{entry['workers_count']} عمال</span>"
                                    if entry['workers_count'] > 1 else ""
                                )
                                cols[i % 3].markdown(
                                    f"<div style='background:{COLORS['success']}12;border:1px solid {COLORS['success']}30;"
                                    f"border-radius:8px;padding:8px 12px;margin:3px 0;"
                                    f"font-size:13px;color:{COLORS['success']};font-weight:600;'>"
                                    f"✓ {entry['name']}{worker_badge}</div>",
                                    unsafe_allow_html=True,
                                )

                    if result['unmatched']:
                        with st.expander(f"⚠️ أسماء غير متطابقة ({len(result['unmatched'])})", expanded=True):
                            info_banner(
                                "هذه الأسماء لم يتم العثور عليها في قاعدة بيانات الموظفين النشطين.",
                                "⚠️", COLORS['warning']
                            )
                            cols = st.columns(3)
                            for i, entry in enumerate(result['unmatched']):
                                cols[i % 3].markdown(
                                    f"<div style='background:{COLORS['warning']}12;border:1px solid {COLORS['warning']}30;"
                                    f"border-radius:8px;padding:8px 12px;margin:3px 0;"
                                    f"font-size:13px;color:{COLORS['warning']};font-weight:600;'>"
                                    f"⚠ {entry['name']} ({entry['workers_count']})</div>",
                                    unsafe_allow_html=True,
                                )
                else:
                    for err in result['errors']:
                        danger_toast(err)
    else:
        # Show format guide when empty
        st.markdown(
            f"""
<div style="background:{COLORS['surface']};border:1px solid {COLORS['border']};
border-radius:14px;padding:22px 24px;margin-top:10px;box-shadow:0 2px 14px {COLORS['shadow']};">
  <p style="font-size:13px;font-weight:700;color:{COLORS['text_muted']};margin-bottom:14px;
            text-transform:uppercase;letter-spacing:.3px;">
    📖 تنسيقات مقبولة
  </p>
  <table style="width:100%;border-collapse:collapse;font-size:13px;">
    <tr style="border-bottom:2px solid {COLORS['primary']}22;">
      <td style="padding:8px 12px;color:{COLORS['text_muted']};font-weight:700;font-size:11.5px;text-transform:uppercase;">النص</td>
      <td style="padding:8px 12px;color:{COLORS['text_muted']};font-weight:700;font-size:11.5px;text-transform:uppercase;">الاسم</td>
      <td style="padding:8px 12px;color:{COLORS['text_muted']};font-weight:700;font-size:11.5px;text-transform:uppercase;">عدد العمال</td>
    </tr>
    <tr style="border-bottom:1px solid {COLORS['border']};">
      <td style="padding:9px 12px;font-family:monospace;color:{COLORS['primary']};">خالد طارق</td>
      <td style="padding:9px 12px;color:{COLORS['text']};">خالد طارق</td>
      <td style="padding:9px 12px;color:{COLORS['success']};font-weight:700;">1</td>
    </tr>
    <tr style="border-bottom:1px solid {COLORS['border']};">
      <td style="padding:9px 12px;font-family:monospace;color:{COLORS['primary']};">6 عمال سامح</td>
      <td style="padding:9px 12px;color:{COLORS['text']};">سامح</td>
      <td style="padding:9px 12px;color:{COLORS['success']};font-weight:700;">6</td>
    </tr>
    <tr style="border-bottom:1px solid {COLORS['border']};">
      <td style="padding:9px 12px;font-family:monospace;color:{COLORS['primary']};">7 عمال مختار</td>
      <td style="padding:9px 12px;color:{COLORS['text']};">مختار</td>
      <td style="padding:9px 12px;color:{COLORS['success']};font-weight:700;">7</td>
    </tr>
    <tr>
      <td style="padding:9px 12px;font-family:monospace;color:{COLORS['primary']};">2 أشرف</td>
      <td style="padding:9px 12px;color:{COLORS['text']};">أشرف</td>
      <td style="padding:9px 12px;color:{COLORS['success']};font-weight:700;">2</td>
    </tr>
  </table>
</div>
""",
            unsafe_allow_html=True,
        )


# ── Classic Attendance Tab (unchanged) ───────────────────────────

def _input_attendance():
    section_card("إدخال الحضور اليومي", "📝", COLORS['primary'])
    info_banner(
        "السطر الأول: التاريخ بصيغة DD/MM/YYYY<br>باقي الأسطر: أسماء الموظفين (سطر لكل موظف)<br>يمكن إضافة بادئات مثل «م» أو «أ» قبل الاسم",
        "📋", COLORS['primary']
    )

    sample = f"""{date.today().strftime('%d/%m/%Y')}
م محمد عبدالجواد
م محمد التوني
شريف ابو العزم
شحاته رزق
عادل عربي"""

    text = st.text_area(
        "📋 أدخل بيانات الحضور:",
        placeholder=sample,
        height=200,
        help="السطر الأول تاريخ، ثم الأسماء"
    )

    st.markdown("<div style='margin-top:4px;'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 4])
    with col1:
        submitted = st.button("💾 حفظ الحضور", type="primary", use_container_width=True)

    if submitted:
        if not text.strip():
            st.error("الرجاء إدخال بيانات الحضور.")
            return
        with st.spinner("جاري معالجة بيانات الحضور..."):
            try:
                result = process_attendance(text)
            except Exception as e:
                danger_toast(f"خطأ في المعالجة: {e}")
                return

        if result['success']:
            success_toast(f"تم حفظ حضور يوم {result['date']} بنجاح!")

            stat_pills([
                ("✅", "تم الحفظ",       str(result['saved']),         COLORS['success']),
                ("🔁", "مكرر (تجاهل)",  str(result['duplicates']),    COLORS['warning']),
                ("⚠️", "غير متطابق",    str(len(result['unmatched'])), COLORS['danger']),
            ])

            if result['matched']:
                with st.expander(f"✅ الموظفون المطابقون ({len(result['matched'])})", expanded=False):
                    cols = st.columns(3)
                    for i, name in enumerate(result['matched']):
                        cols[i % 3].markdown(f"""
<div style="background:{COLORS['success']}12;border:1px solid {COLORS['success']}30;
            border-radius:8px;padding:8px 12px;margin:3px 0;
            font-size:13px;color:{COLORS['success']};font-weight:600;">
  ✓ {name}
</div>""", unsafe_allow_html=True)

            if result['unmatched']:
                with st.expander(f"⚠️ أسماء غير متطابقة ({len(result['unmatched'])})", expanded=True):
                    info_banner("هذه الأسماء لم يتم العثور عليها في قاعدة بيانات الموظفين النشطين.", "⚠️", COLORS['warning'])
                    cols = st.columns(3)
                    for i, name in enumerate(result['unmatched']):
                        cols[i % 3].markdown(f"""
<div style="background:{COLORS['warning']}12;border:1px solid {COLORS['warning']}30;
            border-radius:8px;padding:8px 12px;margin:3px 0;
            font-size:13px;color:{COLORS['warning']};font-weight:600;">
  ⚠ {name}
</div>""", unsafe_allow_html=True)
        else:
            for err in result['errors']:
                danger_toast(err)


def _attendance_matrix():
    section_card("مصفوفة الحضور الشهرية", "🗂️", COLORS['secondary'])

    col1, col2, col3 = st.columns(3)
    month = col1.selectbox(
        "الشهر", list(range(1, 13)),
        index=date.today().month - 1,
        format_func=lambda m: MONTH_NAMES[m - 1]
    )
    year = col2.number_input("السنة", min_value=2020, max_value=2030, value=date.today().year)

    db = get_db()
    try:
        depts = ['الكل'] + sorted([d[0] for d in db.query(Employee.department).distinct() if d[0]])
    finally:
        db.close()

    dept = col3.selectbox("القسم", depts)
    dept_filter = None if dept == 'الكل' else dept

    st.markdown("<div style='margin-top:6px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 عرض المصفوفة", type="primary"):
        with st.spinner("جاري تحميل المصفوفة..."):
            try:
                matrix = get_attendance_matrix(int(month), int(year), dept_filter)
            except Exception as e:
                danger_toast(f"خطأ في تحميل المصفوفة: {e}")
                return

        if matrix.empty:
            empty_state("لا توجد بيانات حضور لهذه الفترة", "📅",
                        "أدخل بيانات الحضور من تبويب «إدخال الحضور»")
            return

        day_cols      = [c for c in matrix.columns if c.isdigit()]
        # Days-present count (1 per day a row has any value > 0), independent
        # of headcount. Using the headcount sum here would push the
        # percentage past 100% whenever a day has more than 1 person.
        days_present   = (matrix[day_cols] > 0).sum().sum() if day_cols else 0
        total_headcount = matrix['إجمالي الحضور'].sum()
        total_possible = len(matrix) * len(day_cols)
        pct = (days_present / total_possible * 100) if total_possible else 0

        stat_pills([
            ("👥", "عدد الموظفين",       str(len(matrix)),     COLORS['primary']),
            ("📅", "أيام الشهر",         str(len(day_cols)),   COLORS['info']),
            ("📊", "نسبة الحضور الكلية", f"{pct:.1f}%",        COLORS['success'] if pct >= 80 else COLORS['warning']),
            ("✅", "إجمالي أيام الحضور", str(int(days_present)), COLORS['success']),
            ("🧮", "إجمالي عدد الأفراد", str(int(total_headcount)), COLORS['secondary']),
        ])

        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
        st.dataframe(matrix, use_container_width=True, hide_index=True, height=400)
        success_toast(f"مصفوفة {MONTH_NAMES[int(month)-1]} {int(year)} — {len(matrix)} موظف")


def _attendance_records():
    section_card("سجلات الحضور", "📋", COLORS['info'])

    col1, col2 = st.columns(2)
    start = col1.date_input("من تاريخ", value=date.today().replace(day=1))
    end   = col2.date_input("إلى تاريخ", value=date.today())

    if start > end:
        st.error("تاريخ البداية يجب أن يكون قبل تاريخ النهاية.")
        return

    st.markdown("<div style='margin-top:6px;'></div>", unsafe_allow_html=True)
    if st.button("🔍 بحث", type="primary"):
        db = get_db()
        try:
            records = db.query(Attendance).filter(
                Attendance.attendance_date >= start,
                Attendance.attendance_date <= end
            ).order_by(Attendance.attendance_date.desc()).all()

            if not records:
                empty_state("لا توجد سجلات في هذه الفترة", "📅")
                return

            employees = {e.id: e for e in db.query(Employee).all()}
            data = [{
                'اسم الموظف': employees[r.employee_id].name if r.employee_id in employees else 'غير معروف',
                'القسم':      employees[r.employee_id].department if r.employee_id in employees else '—',
                'التاريخ':    str(r.attendance_date),
                'الحالة':     '✅ حاضر' if r.status == 1 else '❌ غائب',
                'عدد الأفراد': r.workers_count if r.workers_count is not None else 1,
            } for r in records]

            df      = pd.DataFrame(data)
            present = df[df['الحالة'].str.contains('حاضر')].shape[0]

            stat_pills([
                ("✅", "حاضر",    str(present),           COLORS['success']),
                ("❌", "غائب",    str(len(df) - present), COLORS['danger']),
                ("📋", "الإجمالي", str(len(df)),           COLORS['primary']),
            ])

            st.dataframe(df, use_container_width=True, hide_index=True)
        except Exception as e:
            danger_toast(f"خطأ في تحميل السجلات: {e}")
        finally:
            db.close()
