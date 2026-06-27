import streamlit as st
import pandas as pd
from datetime import date
from database.db import get_db
from database.models import Employee, Overtime
from components.cards import section_card, empty_state, success_toast, danger_toast, stat_pills, warning_toast, info_banner
from components.layout import render_topbar
from components.theme import COLORS
from services.rates import calc_hourly_rate as _calc_hourly_rate


def show():
    render_topbar("الأوفر تايم", "⏱", "الأوفر تايم")
    tab1, tab2, tab3 = st.tabs(["➕ إضافة أوفر تايم", "📋 إدارة السجلات", "✏️ تعديل / حذف"])
    with tab1: _add_overtime()
    with tab2: _list_overtime()
    with tab3: _edit_delete_overtime()


# ─────────────────────────────────────────────────────────────────
# TAB 1 — إضافة سجل
# ─────────────────────────────────────────────────────────────────
def _add_overtime():
    section_card("إضافة سجل أوفر تايم", "➕", COLORS['warning'])
    db = get_db()
    try:
        employees = db.query(Employee).filter(Employee.status == 'Active').order_by(Employee.name).all()
        if not employees:
            empty_state("لا يوجد موظفون نشطون", "👥")
            return
        emp_map = {f"{e.code} — {e.name}": e for e in employees}
    finally:
        db.close()

    # اختيار الموظف خارج الـ form لعرض البيانات الحسابية فوراً
    selected_key = st.selectbox("👤 الموظف", list(emp_map.keys()), key="add_ot_emp")
    emp = emp_map[selected_key]

    hourly_rate = _calc_hourly_rate(emp)

    # عرض معدل الساعة قبل الإدخال
    info_banner(
        f"<b>معدل الساعة المحسوب:</b> {hourly_rate:,.4f} ج.م &nbsp;·&nbsp; "
        f"راتب: {emp.salary:,.2f} ج.م — يومي: {emp.daily_rate:,.2f} ج.م",
        "💡", COLORS['info']
    )

    with st.form("add_overtime_form", clear_on_submit=True):
        st.markdown(
            f"<div style='font-size:12.5px;font-weight:700;color:{COLORS['text_muted']};"
            f"text-transform:uppercase;letter-spacing:.3px;margin-bottom:10px;'>بيانات الأوفر تايم</div>",
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns(2)
        ot_date = col1.date_input("📅 التاريخ", value=date.today())
        hours   = col2.number_input("⏱ الساعات", min_value=0.0, max_value=24.0, step=0.5, value=2.0)
        notes   = st.text_input("📝 ملاحظات", placeholder="اختياري")

        st.markdown(f"<div class='section-sep'></div>", unsafe_allow_html=True)

        # عرض الحساب قبل الحفظ (read-only)
        amount = round(hours * hourly_rate, 2)
        rc1, rc2 = st.columns(2)
        rc1.metric("💵 معدل الساعة (ج.م)", f"{hourly_rate:,.4f}")
        rc2.metric("💰 المبلغ المحسوب (ج.م)", f"{amount:,.2f}")

        submitted = st.form_submit_button("💾 حفظ", type="primary", use_container_width=True)
        if submitted:
            if hours <= 0:
                st.error("⚠️ الساعات يجب أن تكون أكبر من صفر.")
                return
            if hourly_rate <= 0:
                st.error("⚠️ لا يمكن حساب معدل الساعة — يرجى تحديث بيانات الموظف (الراتب أو اليومية).")
                return
            db2 = get_db()
            try:
                db2.add(Overtime(
                    employee_id=emp.id,
                    date=ot_date,
                    hours=hours,
                    rate_per_hour=hourly_rate,
                    amount=amount,
                    notes=notes,
                ))
                db2.commit()
                success_toast(f"✅ تم حفظ الأوفر تايم بنجاح. المبلغ: {amount:,.2f} ج.م")
                st.rerun()
            except Exception as e:
                db2.rollback()
                danger_toast(f"خطأ: {e}")
            finally:
                db2.close()


# ─────────────────────────────────────────────────────────────────
# TAB 2 — عرض السجلات
# ─────────────────────────────────────────────────────────────────
def _list_overtime():
    section_card("سجلات الأوفر تايم", "📋", COLORS['primary'])
    col1, col2 = st.columns(2)
    start = col1.date_input("من تاريخ", value=date.today().replace(day=1))
    end   = col2.date_input("إلى تاريخ", value=date.today())

    if start > end:
        st.error("تاريخ البداية يجب أن يكون قبل تاريخ النهاية.")
        return

    db = get_db()
    try:
        records = (
            db.query(Overtime)
            .filter(Overtime.date >= start, Overtime.date <= end)
            .order_by(Overtime.date.desc())
            .all()
        )
        if not records:
            empty_state("لا توجد سجلات أوفر تايم في هذه الفترة", "⏱")
            return

        employees = {e.id: e for e in db.query(Employee).all()}
        data = [{
            'الرقم':        r.id,
            'الموظف':      employees[r.employee_id].name if r.employee_id in employees else '—',
            'القسم':       employees[r.employee_id].department if r.employee_id in employees else '—',
            'التاريخ':     str(r.date),
            'الساعات':     r.hours,
            'معدل الساعة': r.rate_per_hour,
            'قيمة الأوفر': r.amount,
            'ملاحظات':     r.notes or '',
        } for r in records]
    finally:
        db.close()

    df = pd.DataFrame(data)

    stat_pills([
        ("📋", "عدد السجلات",   str(len(df)),                           COLORS['primary']),
        ("⏱",  "إجمالي الساعات", f"{df['الساعات'].sum():.1f} ساعة",    COLORS['warning']),
        ("💰", "إجمالي المبلغ",  f"{df['قيمة الأوفر'].sum():,.0f} ج.م", COLORS['success']),
    ])

    search = st.text_input("🔍 بحث في السجلات", placeholder="ابحث بالاسم أو القسم أو التاريخ...")
    display_df = df.drop(columns=["الرقم"])
    if search:
        mask = display_df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
        display_df = display_df[mask]

    st.markdown("<div style='margin-top:6px;'></div>", unsafe_allow_html=True)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    if len(df) > 0:
        st.markdown(f"<div class='section-sep'></div>", unsafe_allow_html=True)
        dept_sum = df.groupby('القسم')['قيمة الأوفر'].sum().reset_index()
        st.bar_chart(dept_sum.set_index('القسم'))


# ─────────────────────────────────────────────────────────────────
# TAB 3 — تعديل / حذف
# ─────────────────────────────────────────────────────────────────
def _edit_delete_overtime():
    section_card("تعديل / حذف سجل أوفر تايم", "✏️", COLORS['danger'])

    db_r = get_db()
    try:
        records   = db_r.query(Overtime).order_by(Overtime.date.desc()).limit(100).all()
        employees = {e.id: e for e in db_r.query(Employee).all()}
        emp_list  = db_r.query(Employee).filter(Employee.status == 'Active').all()
        if not records:
            empty_state("لا توجد سجلات", "⏱")
            return
        options = {
            f"{employees[r.employee_id].name if r.employee_id in employees else '—'} — {r.date} — {r.hours} ساعة": r.id
            for r in records
        }
        rec_map = {
            r.id: {
                'emp_id': r.employee_id,
                'date':   r.date,
                'hours':  float(r.hours),
                'rate':   float(r.rate_per_hour),
                'amount': float(r.amount),
                'notes':  r.notes or '',
            }
            for r in records
        }
        emp_options = {f"{e.code} — {e.name}": e for e in emp_list}
    finally:
        db_r.close()

    selected = st.selectbox("اختر سجلاً", list(options.keys()), key="edit_ot_select")
    rec_id = options[selected]
    rv     = rec_map[rec_id]

    # اختيار الموظف خارج الـ form لحساب المعدل فوراً
    emp_names   = list(emp_options.keys())
    current_emp = next((k for k, v in emp_options.items() if v.id == rv['emp_id']), emp_names[0] if emp_names else "")
    sel_emp_key = st.selectbox("الموظف", emp_names,
                               index=emp_names.index(current_emp) if current_emp in emp_names else 0,
                               key="edit_ot_emp")
    sel_emp     = emp_options[sel_emp_key]
    hourly_rate = _calc_hourly_rate(sel_emp)

    info_banner(
        f"<b>معدل الساعة المحسوب:</b> {hourly_rate:,.4f} ج.م &nbsp;·&nbsp; "
        f"راتب: {sel_emp.salary:,.2f} ج.م — يومي: {sel_emp.daily_rate:,.2f} ج.م",
        "💡", COLORS['info']
    )

    with st.form("edit_ot_form"):
        st.markdown(
            f"<div style='font-size:12.5px;font-weight:700;color:{COLORS['text_muted']};"
            f"text-transform:uppercase;letter-spacing:.3px;margin-bottom:10px;'>بيانات السجل</div>",
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns(2)
        ot_date = col1.date_input("التاريخ", value=rv['date'])
        hours   = col2.number_input("الساعات", value=rv['hours'], min_value=0.0, step=0.5)
        notes   = st.text_input("ملاحظات", value=rv['notes'])

        st.markdown(f"<div class='section-sep'></div>", unsafe_allow_html=True)

        amount = round(hours * hourly_rate, 2)
        rc1, rc2 = st.columns(2)
        rc1.metric("💵 معدل الساعة (ج.م)", f"{hourly_rate:,.4f}")
        rc2.metric("💰 المبلغ المحسوب (ج.م)", f"{amount:,.2f}")

        confirm_del = st.checkbox("⚠️ تأكيد الحذف")
        cs, cd = st.columns(2)
        save   = cs.form_submit_button("💾 تحديث",  type="primary",   use_container_width=True)
        delete = cd.form_submit_button("🗑️ حذف",   type="secondary", use_container_width=True)

        if save:
            if hours <= 0:
                st.error("⚠️ الساعات يجب أن تكون أكبر من صفر.")
            elif hourly_rate <= 0:
                st.error("⚠️ لا يمكن حساب معدل الساعة — يرجى تحديث بيانات الموظف.")
            else:
                db_w = get_db()
                try:
                    obj = db_w.query(Overtime).filter(Overtime.id == rec_id).first()
                    if obj:
                        obj.employee_id   = sel_emp.id
                        obj.date          = ot_date
                        obj.hours         = hours
                        obj.rate_per_hour = hourly_rate
                        obj.amount        = amount
                        obj.notes         = notes
                        db_w.commit()
                        success_toast("✅ تم تحديث السجل بنجاح.")
                        st.rerun()
                except Exception as e:
                    db_w.rollback()
                    danger_toast(f"خطأ: {e}")
                finally:
                    db_w.close()

        if delete:
            if not confirm_del:
                warning_toast("⚠️ يرجى تأكيد الحذف أولاً.")
            else:
                db_d = get_db()
                try:
                    obj = db_d.query(Overtime).filter(Overtime.id == rec_id).first()
                    if obj:
                        db_d.delete(obj)
                        db_d.commit()
                        success_toast("✅ تم حذف السجل بنجاح.")
                        st.rerun()
                except Exception as e:
                    db_d.rollback()
                    danger_toast(f"خطأ في الحذف: {e}")
                finally:
                    db_d.close()
