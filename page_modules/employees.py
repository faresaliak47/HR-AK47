import streamlit as st
import pandas as pd
import re
from datetime import date
from database.db import get_db
from database.models import Employee, Attendance, Overtime, Advance
from sqlalchemy.exc import IntegrityError
from services.rates import calc_daily_rate
from components.cards import (page_header, employee_card, empty_state, status_badge,
                               section_card, success_toast, danger_toast, info_banner,
                               warning_toast, stat_pills, confirm_delete_section)
from components.layout import render_topbar
from components.theme import COLORS


_CODE_RE = re.compile(r'^([A-Za-z\u0600-\u06FF]*)(\d+)$')


def _next_employee_code(db) -> str:
    """
    Suggest the next employee code based on the codes already in the DB —
    e.g. if the highest existing code is E040, suggest E041. Falls back to
    "E001" when there are no employees yet, or when no existing code
    matches the "letters + digits" pattern (a free-form code was used).
    Keeps the same zero-padding width as the highest matched code (so
    E007 → E008, but E0099 → E0100), and skips forward past any code
    that already exists, in case of gaps or manual overrides.
    """
    codes = [c for (c,) in db.query(Employee.code).all() if c]
    best_num, best_width, best_prefix = 0, 3, "E"
    for code in codes:
        m = _CODE_RE.match(code.strip())
        if not m:
            continue
        prefix, num_str = m.groups()
        num = int(num_str)
        if num > best_num:
            best_num, best_width, best_prefix = num, len(num_str), (prefix or "E")

    existing = set(codes)
    next_num = best_num + 1
    candidate = f"{best_prefix}{str(next_num).zfill(best_width)}"
    while candidate in existing:
        next_num += 1
        candidate = f"{best_prefix}{str(next_num).zfill(best_width)}"
    return candidate


def show():
    render_topbar("إدارة الموظفين", "👥", "الموظفون")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 قائمة الموظفين",
        "➕ إضافة موظف",
        "📥 استيراد Excel",
        "✏️ تعديل / حذف"
    ])
    with tab1: _list_employees()
    with tab2: _add_employee()
    with tab3: _import_employees()
    with tab4: _edit_delete_employee()


def _list_employees():
    db = get_db()
    try:
        employees = db.query(Employee).all()
        if not employees:
            empty_state("لا يوجد موظفون مسجلون", "👥", "أضف موظفاً جديداً من تبويب «إضافة موظف»")
            return

        # ── Filter bar (no wrapper div — avoids orphan bug) ──────────────
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        search        = col1.text_input("🔍 بحث بالاسم أو الكود", placeholder="اكتب للبحث...")
        depts         = sorted({e.department for e in employees if e.department})
        dept_filter   = col2.selectbox("🏢 القسم", ["الكل"] + depts)
        status_filter = col3.selectbox("🔵 الحالة", ["الكل", "Active", "Inactive", "Suspended"],
                                       format_func=lambda s: {"الكل": "الكل", "Active": "✅ نشط",
                                                              "Inactive": "⚫ غير نشط", "Suspended": "🔴 موقوف"}.get(s, s))
        view_mode     = col4.selectbox("عرض", ["بطاقات", "جدول"])

        # ── Filter data ───────────────────────────────────────────────────
        filtered = employees
        if search:
            s = search.strip().lower()
            filtered = [e for e in filtered if s in e.name.lower() or s in (e.code or '').lower()]
        if dept_filter != "الكل":
            filtered = [e for e in filtered if e.department == dept_filter]
        if status_filter != "الكل":
            filtered = [e for e in filtered if e.status == status_filter]

        total_sal  = sum(e.salary for e in filtered)
        active_cnt = sum(1 for e in filtered if e.status == 'Active')

        stat_pills([
            ("👥", "إجمالي",         str(len(filtered)), COLORS['primary']),
            ("✅", "نشط",            str(active_cnt),    COLORS['success']),
            ("💰", "إجمالي الرواتب", f"{total_sal:,.0f} ج.م", COLORS['warning']),
        ])

        if not filtered:
            empty_state("لا توجد نتائج مطابقة", "🔍", "جرب تغيير معايير البحث")
            return

        if view_mode == "بطاقات":
            cols = st.columns(3)
            for i, emp in enumerate(filtered):
                employee_card(cols[i % 3], emp.code, emp.name,
                              emp.job_title or "", emp.department or "",
                              emp.status, emp.salary)
        else:
            data = [{
                'الكود':         e.code,
                'الاسم':         e.name,
                'المسمى':        e.job_title or '',
                'القسم':         e.department or '',
                'الراتب':        e.salary,
                'المعدل اليومي': e.daily_rate,
                'الحالة':        e.status,
            } for e in filtered]
            st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
    finally:
        db.close()


def _add_employee():
    section_card("إضافة موظف جديد", "➕", COLORS['success'])

    db_code = get_db()
    try:
        suggested_code = _next_employee_code(db_code)
    finally:
        db_code.close()

    with st.form("add_employee_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        code        = col1.text_input("كود الموظف *", value=suggested_code,
                                       help="مقترح تلقائياً كآخر كود + 1 — تقدر تعدّله لو حابب.")
        name        = col2.text_input("الاسم الكامل *", placeholder="محمد أحمد علي")
        job_title   = col1.text_input("المسمى الوظيفي", placeholder="مهندس")
        department  = col2.text_input("القسم", placeholder="الصيانة")
        salary      = col1.number_input("الراتب (ج.م)", min_value=0.0, step=500.0)
        daily_rate  = col2.number_input("المعدل اليومي (ج.م)", min_value=0.0, step=10.0)
        auto_rate   = st.checkbox(
            "🔄 حساب المعدل اليومي تلقائياً = الراتب ÷ 30",
            value=True,
            help="عند التفعيل، سيتم تجاهل القيمة المكتوبة في «المعدل اليومي» "
                 "أعلاه وحسابها أوتوماتيكياً من الراتب عند الحفظ — لمنع أخطاء الإدخال اليدوي.",
            key="add_emp_auto_rate",
        )
        phone       = col1.text_input("الهاتف", placeholder="01xxxxxxxxx")
        national_id = col2.text_input("الرقم القومي")
        area        = col1.text_input("المنطقة")
        hire_date   = col2.date_input("تاريخ التعيين", value=date.today())
        status      = st.selectbox("الحالة", ["Active", "Inactive", "Suspended"],
                                   format_func=lambda s: {"Active": "✅ نشط",
                                                          "Inactive": "⚫ غير نشط",
                                                          "Suspended": "🔴 موقوف"}[s])
        submitted = st.form_submit_button("💾 حفظ الموظف", type="primary", use_container_width=True)
        if submitted:
            if not code.strip() or not name.strip():
                st.error("⚠️  الكود والاسم حقول إجبارية.")
                return
            final_daily_rate = calc_daily_rate(salary) if auto_rate else daily_rate
            db = get_db()
            try:
                db.add(Employee(
                    code=code.strip(), name=name.strip(),
                    job_title=job_title, department=department,
                    salary=salary, daily_rate=final_daily_rate,
                    phone=phone, national_id=national_id,
                    area=area, hire_date=hire_date, status=status
                ))
                db.commit()
                msg = f"تم إضافة الموظف {name.strip()} بنجاح! 🎉"
                if auto_rate:
                    msg += f" (المعدل اليومي المحسوب: {final_daily_rate:,.2f} ج.م)"
                success_toast(msg)
                st.rerun()
            except IntegrityError:
                db.rollback()
                danger_toast(f"الكود «{code}» مستخدم مسبقاً، اختر كوداً آخر.")
            except Exception as e:
                db.rollback()
                danger_toast(f"خطأ غير متوقع: {e}")
            finally:
                db.close()


def _import_employees():
    section_card("استيراد الموظفين من Excel", "📥", COLORS['info'])
    info_banner(
        "يجب أن يحتوي الملف على الأعمدة: ID · Name · Job Title · Department · Salary · Daily Rate",
        "📋", COLORS['info']
    )
    uploaded = st.file_uploader("اسحب وأفلت ملف Excel هنا", type=["xlsx", "xls"])
    if not uploaded:
        return
    try:
        df = pd.read_excel(uploaded)
        st.caption(f"معاينة البيانات — {len(df)} صف")
        st.dataframe(df.head(5), use_container_width=True, hide_index=True)

        col_map = {
            'ID': 'code', 'Name': 'name', 'Job Title': 'job_title',
            'Department': 'department', 'Salary': 'salary', 'Daily Rate': 'daily_rate'
        }
        mapped = {}
        for expected, field in col_map.items():
            for actual in df.columns:
                if expected.lower() in str(actual).lower():
                    mapped[field] = actual
                    break

        if 'code' not in mapped or 'name' not in mapped:
            danger_toast("لم يتم العثور على أعمدة ID و Name في الملف.")
            return

        if st.button("📥 استيراد الآن", type="primary", use_container_width=True):
            db = get_db()
            added = skipped = 0
            try:
                for _, row in df.iterrows():
                    code = str(row[mapped['code']]).strip()
                    name = str(row[mapped['name']]).strip()
                    if not code or not name or code == 'nan':
                        continue
                    if db.query(Employee).filter(Employee.code == code).first():
                        skipped += 1
                        continue
                    db.add(Employee(
                        code=code, name=name,
                        job_title=str(row.get(mapped.get('job_title', ''), '')).strip() if mapped.get('job_title') else '',
                        department=str(row.get(mapped.get('department', ''), '')).strip() if mapped.get('department') else '',
                        salary=float(row[mapped['salary']]) if mapped.get('salary') else 0.0,
                        daily_rate=float(row[mapped['daily_rate']]) if mapped.get('daily_rate') else 0.0,
                        status='Active'
                    ))
                    added += 1
                db.commit()
                success_toast(f"تم استيراد {added} موظف بنجاح. تم تخطي {skipped} مكرر.")
                st.rerun()
            except Exception as e:
                db.rollback()
                danger_toast(f"خطأ في الاستيراد: {e}")
            finally:
                db.close()
    except Exception as e:
        danger_toast(f"خطأ في قراءة الملف: {e}")


def _edit_delete_employee():
    # ── CRITICAL FIX: Use two separate DB sessions for read vs write ──────
    # Read list for selectbox
    db_read = get_db()
    try:
        employees = db_read.query(Employee).order_by(Employee.code).all()
        if not employees:
            empty_state("لا يوجد موظفون", "👥")
            return
        emp_options = {f"{e.code} — {e.name}": e.id for e in employees}
    finally:
        db_read.close()

    section_card("تعديل أو حذف موظف", "✏️", COLORS['warning'])
    selected = st.selectbox("🔍 اختر موظفاً", list(emp_options.keys()))
    emp_id   = emp_options[selected]

    # Load fresh record for display
    db_show = get_db()
    try:
        emp = db_show.query(Employee).filter(Employee.id == emp_id).first()
        if not emp:
            return

        st.markdown(
            f"<div style='margin:8px 0;'>الحالة الحالية: {status_badge(emp.status)}</div>",
            unsafe_allow_html=True
        )

        # Read current values into local variables before closing session
        v_code = emp.code; v_name = emp.name; v_job = emp.job_title or ''
        v_dept = emp.department or ''; v_salary = float(emp.salary or 0)
        v_rate = float(emp.daily_rate or 0); v_phone = emp.phone or ''
        v_nid  = emp.national_id or ''; v_area = emp.area or ''
        v_status = emp.status or 'Active'
    finally:
        db_show.close()

    with st.form("edit_employee_form"):
        col1, col2 = st.columns(2)
        code        = col1.text_input("الكود",           value=v_code)
        name        = col2.text_input("الاسم",            value=v_name)
        job_title   = col1.text_input("المسمى",           value=v_job)
        department  = col2.text_input("القسم",            value=v_dept)
        salary      = col1.number_input("الراتب",         value=v_salary, step=500.0)
        daily_rate  = col2.number_input("المعدل اليومي",  value=v_rate, step=10.0)
        auto_rate   = st.checkbox(
            "🔄 إعادة حساب المعدل اليومي تلقائياً = الراتب ÷ 30",
            value=False,
            help="عند التفعيل، سيتم تجاهل القيمة المكتوبة في «المعدل اليومي» "
                 "وحسابها أوتوماتيكياً من الراتب الجديد عند التحديث.",
            key="edit_emp_auto_rate",
        )
        phone       = col1.text_input("الهاتف",           value=v_phone)
        national_id = col2.text_input("الرقم القومي",    value=v_nid)
        area        = col1.text_input("المنطقة",          value=v_area)
        status_opts = ["Active", "Inactive", "Suspended"]
        status      = col2.selectbox(
            "الحالة", status_opts,
            index=status_opts.index(v_status) if v_status in status_opts else 0,
            format_func=lambda s: {"Active": "✅ نشط", "Inactive": "⚫ غير نشط", "Suspended": "🔴 موقوف"}[s]
        )

        confirm_del = st.checkbox("⚠️ أؤكد حذف هذا الموظف وجميع بياناته")
        c_save, c_del = st.columns(2)
        save   = c_save.form_submit_button("💾 تحديث",       type="primary",   use_container_width=True)
        delete = c_del.form_submit_button("🗑️ حذف الموظف", type="secondary", use_container_width=True)

        if save:
            if not name.strip():
                st.error("الاسم لا يمكن أن يكون فارغاً.")
            else:
                # ── FIX: Open fresh session, load object, mutate, commit ──
                db_w = get_db()
                try:
                    obj = db_w.query(Employee).filter(Employee.id == emp_id).first()
                    if obj:
                        final_daily_rate = calc_daily_rate(salary) if auto_rate else daily_rate
                        obj.code = code; obj.name = name; obj.job_title = job_title
                        obj.department = department; obj.salary = salary; obj.daily_rate = final_daily_rate
                        obj.phone = phone; obj.national_id = national_id; obj.area = area; obj.status = status
                        db_w.commit()
                        success_toast("تم تحديث بيانات الموظف بنجاح. ✅")
                        st.rerun()
                except Exception as e:
                    db_w.rollback()
                    danger_toast(f"خطأ: {e}")
                finally:
                    db_w.close()

        if delete:
            if not confirm_del:
                warning_toast("يرجى تأكيد الحذف بتفعيل خانة التأكيد أولاً.")
            else:
                db_d = get_db()
                try:
                    obj = db_d.query(Employee).filter(Employee.id == emp_id).first()
                    if obj:
                        db_d.delete(obj)
                        db_d.commit()
                        success_toast("تم حذف الموظف بنجاح.")
                        st.rerun()
                except Exception as e:
                    db_d.rollback()
                    danger_toast(f"خطأ في الحذف: {e}")
                finally:
                    db_d.close()
