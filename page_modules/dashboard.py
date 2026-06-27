import streamlit as st
import pandas as pd
from datetime import date, timedelta
from database.db import get_db
from database.models import Employee, Attendance, Overtime, Advance
from components.cards import kpi_card, empty_state, stat_pills, section_card
from components.layout import render_topbar
from components.theme import COLORS, MONTH_NAMES
from components.charts import (attendance_trend_chart, department_donut_chart, payroll_bar_chart)
from services.payroll_service import calculate_payroll


def show():
    render_topbar("لوحة التحكم", "📊", "الرئيسية")

    db = get_db()
    try:
        today        = date.today()
        total_emp    = db.query(Employee).count()
        active_emp   = db.query(Employee).filter(Employee.status == 'Active').count()
        inactive_emp = db.query(Employee).filter(Employee.status == 'Inactive').count()
        present_today = db.query(Attendance).filter(
            Attendance.attendance_date == today, Attendance.status == 1
        ).count()
        absent_today = max(active_emp - present_today, 0)

        ot_records  = db.query(Overtime).all()
        total_ot    = sum(r.amount for r in ot_records)
        adv_records = db.query(Advance).all()
        total_adv   = sum(r.amount for r in adv_records)

        try:
            pay_df    = calculate_payroll(today.month, today.year)
            total_net = pay_df['صافي الراتب'].sum() if not pay_df.empty else 0
        except Exception as e:
            print(f"[dashboard] Payroll calculation failed: {e}")
            pay_df    = pd.DataFrame()
            total_net = 0

        # ── KPI Row ──────────────────────────────────────────────────────
        c1, c2, c3, c4, c5 = st.columns(5)
        kpi_card(c1, "👥", "إجمالي الموظفين", total_emp,
                 COLORS['primary'], sub_label=f"{active_emp} نشط · {inactive_emp} غير نشط")
        kpi_card(c2, "✅", "حاضرون اليوم", present_today,
                 COLORS['success'], sub_label=f"من أصل {active_emp} نشط")
        kpi_card(c3, "❌", "غائبون اليوم", absent_today,
                 COLORS['danger'], sub_label="موظف غائب")
        kpi_card(c4, "⏱", "إجمالي الأوفر تايم", f"{total_ot:,.0f}",
                 COLORS['warning'], sub_label="جنيه مصري")
        kpi_card(c5, "🏦", "إجمالي السلف", f"{total_adv:,.0f}",
                 COLORS['accent'], sub_label="جنيه مصري")

        st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

        # ── Charts Row ───────────────────────────────────────────────────
        col_a, col_b = st.columns([3, 2])

        with col_a:
            section_card("منحنى الحضور (30 يوماً)", "📈", COLORS['primary'])
            start_date  = today - timedelta(days=29)
            att_records = db.query(Attendance).filter(
                Attendance.attendance_date >= start_date,
                Attendance.attendance_date <= today,
                Attendance.status == 1
            ).all()
            if att_records:
                att_df    = pd.DataFrame([{'date': r.attendance_date} for r in att_records])
                att_trend = att_df.groupby('date').size().reset_index(name='count')
                att_trend['date'] = pd.to_datetime(att_trend['date'])
                fig = attendance_trend_chart(att_trend)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            else:
                empty_state("لا توجد بيانات حضور بعد", "📅", "أدخل بيانات الحضور من قسم الحضور والغياب")

        with col_b:
            section_card("توزيع الموظفين بالأقسام", "🏢", COLORS['secondary'])
            employees = db.query(Employee).filter(Employee.status == 'Active').all()
            if employees:
                dept_df    = pd.DataFrame([{'القسم': e.department or 'غير محدد'} for e in employees])
                dept_count = dept_df['القسم'].value_counts().reset_index()
                dept_count.columns = ['القسم', 'العدد']
                fig2 = department_donut_chart(dept_count)
                st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
            else:
                empty_state("لا توجد بيانات", "🏢")

        # ── Bottom Row ───────────────────────────────────────────────────
        col_c, col_d = st.columns([3, 2])

        with col_c:
            section_card("أعلى رواتب الشهر الحالي", "💼", COLORS['primary'])
            if not pay_df.empty:
                fig3 = payroll_bar_chart(pay_df)
                st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("احسب مسير الرواتب أولاً لعرض البيانات.")

        with col_d:
            section_card("آخر نشاط", "🕐", COLORS['info'])
            recent_att = db.query(Attendance).filter(
                Attendance.status == 1
            ).order_by(Attendance.attendance_date.desc()).limit(8).all()

            emp_map = {e.id: e for e in db.query(Employee).all()}
            if recent_att:
                for r in recent_att:
                    emp = emp_map.get(r.employee_id)
                    if not emp:
                        continue
                    initials = "".join([w[0] for w in emp.name.split()[:2]])
                    st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;padding:8px 0;
            border-bottom:1px solid {COLORS['border']};">
  <div style="background:{COLORS['primary']}20;border-radius:8px;
              width:34px;height:34px;display:flex;align-items:center;justify-content:center;
              font-size:13px;font-weight:700;color:{COLORS['primary']};flex-shrink:0;">{initials}</div>
  <div style="flex:1;min-width:0;">
    <div style="font-size:12.5px;font-weight:600;color:{COLORS['text']};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{emp.name}</div>
    <div style="font-size:10.5px;color:{COLORS['text_muted']};">{r.attendance_date} · حضور ✅</div>
  </div>
</div>
""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
<div style="text-align:center;padding:30px;color:{COLORS['text_muted']};font-size:13px;">
  لا توجد سجلات حضور بعد
</div>
""", unsafe_allow_html=True)

        # ── Summary Stats Bar ─────────────────────────────────────────────
        att_this_month = db.query(Attendance).filter(
            Attendance.attendance_date >= date(today.year, today.month, 1),
            Attendance.attendance_date <= today,
            Attendance.status == 1
        ).count()

        stat_pills([
            ("👥", "إجمالي الموظفين",  str(total_emp),          COLORS['primary']),
            ("✅", "حضور هذا الشهر",   str(att_this_month),     COLORS['success']),
            ("⏱", "ساعات أوفر تايم",  f"{sum(r.hours for r in ot_records):.0f}", COLORS['warning']),
            ("💰", "إجمالي السلف",      f"{total_adv:,.0f} ج.م", COLORS['accent']),
            ("💼", "صافي رواتب الشهر", f"{total_net:,.0f} ج.م", COLORS['secondary']),
        ])

    except Exception as e:
        st.error(f"خطأ في تحميل لوحة التحكم: {e}")
    finally:
        db.close()
