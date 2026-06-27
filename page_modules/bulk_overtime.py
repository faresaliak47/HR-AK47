"""Bulk Overtime Entry — adds overtime for multiple employees, each with their own auto-calculated rate."""
import re
import streamlit as st
import pandas as pd
from datetime import date, datetime
from database.db import get_db
from database.models import Employee, Overtime
from components.cards import section_card, empty_state, success_toast, danger_toast, warning_toast, stat_pills
from components.layout import render_topbar
from components.theme import COLORS
from services.rates import calc_hourly_rate as _calc_hourly_rate


# ── Bulk-overtime tagging & safe delete-by-date (bulk overtime only) ─
# Overtime and "normal overtime" share the same `overtime` table with no
# column to tell them apart, and we must not change the DB schema. So every
# record created by THIS module is tagged inside the existing `notes` field.
# Deletion is then scoped to date + tag, never touching normal-overtime rows.
_BOT_TAG = "[BULK_OT]"


def _bot_tag_note(note: str) -> str:
    """Prefix a note with the bulk-overtime tag, used on every save in this module."""
    note = (note or "").strip()
    return f"{_BOT_TAG} {note}".strip() if note else _BOT_TAG


def delete_bulk_overtime_by_date(target_date):
    """
    Delete ONLY bulk-overtime-tagged Overtime records for the given date.

    Safety:
      - Filters by date AND the bulk-overtime tag in `notes`, so normal
        overtime (or any record not created via Bulk Overtime) is never
        touched, and other dates are never touched.
      - Note: legacy bulk-overtime rows saved before this tagging was
        introduced won't carry the tag, so they are intentionally NOT
        deleted by this function (we can't safely tell them apart from
        normal overtime without it).

    Returns: (deleted_count: int, error: str | None)
    """
    db = get_db()
    try:
        records = db.query(Overtime).filter(
            Overtime.date == target_date,
            Overtime.notes.like(f"{_BOT_TAG}%"),
        ).all()
        deleted_count = len(records)
        for r in records:
            db.delete(r)
        db.commit()
        return deleted_count, None
    except Exception as e:
        db.rollback()
        return 0, str(e)
    finally:
        db.close()


# ── Smart Paste: parsing helpers (bulk overtime only) ─────────────
# NOTE: Equipment entries (عربية / لودر / معدات) are treated EXACTLY like
# employee entries everywhere in this module — same parsing, same matching,
# same rate calculation, same save/list/delete pipeline. There is no
# separate "equipment" path anymore.
_BOT_AR_DIGITS   = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_BOT_NOISE_RE    = re.compile(r'\bعمال\b', re.UNICODE)
_BOT_UNITS_RE    = re.compile(r'\+\s*(\d+)\s*$')


def _bot_normalize_digits(s: str) -> str:
    """Convert Arabic-Indic digits (٠-٩) to Western digits (0-9)."""
    return s.translate(_BOT_AR_DIGITS)


def _bot_parse_line(line: str):
    """
    Parse a single bulk-overtime name line, extracting the optional "+N" bonus.
      "شريف أبو العزم+1"  -> {name:"شريف أبو العزم", bonus:1}
      "عربية نقل عمال"     -> {name:"عربية نقل",      bonus:0}

    `bonus` is added to the base hours (line 2) by the caller to get overtime_units.
    Every entry (employee or equipment name) goes through identical parsing —
    there is no type distinction.
    """
    line = _bot_normalize_digits(line).strip()
    if not line:
        return None

    bonus = 0
    m = _BOT_UNITS_RE.search(line)
    if m:
        bonus = int(m.group(1))
        line = line[:m.start()].strip()

    name = _BOT_NOISE_RE.sub('', line)
    name = re.sub(r'\s+', ' ', name).strip()
    if not name:
        return None

    return {"name": name, "bonus": bonus}


def parse_bulk_overtime_text(text: str):
    """
    Parse the smart-paste bulk overtime format.

      line 1 -> date (DD/M/YYYY, also accepts Arabic digits)
      line 2 -> hours (number extracted from free text, e.g. "1 ساعة")
      remaining lines -> employee/equipment entries, one per line

    Returns: (ot_date | None, hours | None, entries: list[dict], errors: list[str])
    """
    raw_lines = [l.strip() for l in text.strip().splitlines()]
    lines = [l for l in raw_lines if l]

    if len(lines) < 2:
        return None, None, [], ['النص غير مكتمل: يجب أن يحتوي على سطر تاريخ وسطر ساعات على الأقل']

    date_line = _bot_normalize_digits(lines[0])
    ot_date = None
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y'):
        try:
            ot_date = datetime.strptime(date_line, fmt).date()
            break
        except ValueError:
            continue
    if ot_date is None:
        return None, None, [], [f'تنسيق التاريخ غير صحيح: {lines[0]}']

    hours_line = _bot_normalize_digits(lines[1])
    hm = re.search(r'(\d+(?:\.\d+)?)', hours_line)
    if not hm:
        return ot_date, None, [], [f'لم يتم العثور على عدد الساعات: {lines[1]}']
    hours = float(hm.group(1))
    if hours.is_integer():
        hours = int(hours)

    entries = []
    for line in lines[2:]:
        parsed = _bot_parse_line(line)
        if parsed:
            units = hours + parsed["bonus"]
            if isinstance(units, float) and units.is_integer():
                units = int(units)
            entries.append({
                "name": parsed["name"],
                "overtime_units": units,
            })

    if not entries:
        return ot_date, hours, [], ['لم يتم العثور على أسماء صالحة في النص']

    return ot_date, hours, entries, []


def show():
    render_topbar("إدخال أوفر تايم جماعي", "⏱", "الأوفر تايم الجماعي")

    tab1, tab2, tab3, tab4 = st.tabs([
        "➕ إدخال جماعي", "📋 سجلات الأوفر تايم", "🧠 لصق نص ذكي", "🗑️ حذف بالتاريخ",
    ])
    with tab1:
        _bulk_add_overtime()
    with tab2:
        _list_overtime()
    with tab3:
        _smart_paste_overtime()
    with tab4:
        _delete_bulk_overtime_tab()


def _bulk_add_overtime():
    section_card("اختيار الموظفين", "👥", COLORS['primary'])

    # ── Persistent selection set ──────────────────────────────────
    # We store selected employee IDs in a set that survives filter/search changes.
    if "bulk_ot_selected_ids" not in st.session_state:
        st.session_state["bulk_ot_selected_ids"] = set()

    db = get_db()
    try:
        employees = db.query(Employee).filter(Employee.status == 'Active').order_by(Employee.name).all()
        if not employees:
            empty_state("لا يوجد موظفون نشطون", "👥")
            return
        emp_data = [{
            "id":      e.id,
            "الاسم":  e.name,
            "الكود":  e.code,
            "القسم":  e.department or "—",
            "_emp":   e,
        } for e in employees]
    finally:
        db.close()

    df_all = pd.DataFrame(emp_data)
    emp_by_id = {row["id"]: row["_emp"] for _, row in df_all.iterrows()}

    # ── Filter Controls ──────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    search_name = col1.text_input("🔍 بحث بالاسم",  placeholder="اكتب اسم الموظف...")
    search_code = col2.text_input("🔍 بحث بالكود",  placeholder="اكتب كود الموظف...")
    depts       = ["الكل"] + sorted(df_all["القسم"].dropna().unique().tolist())
    filter_dept = col3.selectbox("📂 تصفية بالقسم", depts)

    df_filtered = df_all.copy()
    if search_name:
        df_filtered = df_filtered[df_filtered["الاسم"].str.contains(search_name, case=False, na=False)]
    if search_code:
        df_filtered = df_filtered[df_filtered["الكود"].str.contains(search_code, case=False, na=False)]
    if filter_dept != "الكل":
        df_filtered = df_filtered[df_filtered["القسم"] == filter_dept]

    # ── Select All / Unselect All (acts on filtered view only) ────
    ca, cb, _ = st.columns([1, 1, 4])
    if ca.button("✅ تحديد الكل", use_container_width=True):
        for eid in df_filtered["id"].tolist():
            st.session_state["bulk_ot_selected_ids"].add(eid)
        st.rerun()
    if cb.button("❌ إلغاء التحديد", use_container_width=True):
        for eid in df_filtered["id"].tolist():
            st.session_state["bulk_ot_selected_ids"].discard(eid)
        st.rerun()

    st.markdown(
        f"<p style='font-size:12px;color:{COLORS['text_muted']};'>"
        f"يُظهر {len(df_filtered)} موظف من أصل {len(df_all)}</p>",
        unsafe_allow_html=True,
    )

    # ── Employee Selection Table ──────────────────────────────────
    with st.container(key="bulk_ot_emp_table"):
        hc1, hc2, hc3, hc4, hc5 = st.columns([0.5, 3, 1.5, 2, 2])
        for col, label in zip(
            [hc1, hc2, hc3, hc4, hc5],
            ["✓", "الاسم", "الكود", "القسم", "معدل الساعة (ج.م)"],
        ):
            col.markdown(
                f"<span style='font-size:11px;font-weight:700;color:{COLORS['text_muted']};'>{label}</span>",
                unsafe_allow_html=True,
            )
        st.markdown(f"<hr style='margin:4px 0 8px;border-color:{COLORS['border']};'>", unsafe_allow_html=True)

        for _, row in df_filtered.iterrows():
            eid = row["id"]
            emp = row["_emp"]
            hr  = _calc_hourly_rate(emp)
            ec1, ec2, ec3, ec4, ec5 = st.columns([0.5, 3, 1.5, 2, 2])

            # Read current state from our persistent set (not from a keyed widget)
            current_checked = eid in st.session_state["bulk_ot_selected_ids"]
            new_checked = ec1.checkbox(
                "",
                value=current_checked,
                key=f"bulk_ot_cb_{eid}",
                label_visibility="collapsed",
            )

            # Sync checkbox change back to the persistent set
            if new_checked != current_checked:
                if new_checked:
                    st.session_state["bulk_ot_selected_ids"].add(eid)
                else:
                    st.session_state["bulk_ot_selected_ids"].discard(eid)

            ec2.markdown(f"<span style='font-size:13px;'>{row['الاسم']}</span>", unsafe_allow_html=True)
            ec3.markdown(f"<span style='font-size:12px;color:{COLORS['primary']};font-weight:600;'>{row['الكود']}</span>", unsafe_allow_html=True)
            ec4.markdown(f"<span style='font-size:12px;color:{COLORS['text_muted']};'>{row['القسم']}</span>", unsafe_allow_html=True)
            ec5.markdown(
                f"<span style='font-size:12px;color:{COLORS['success'] if hr > 0 else COLORS['danger']};font-weight:600;'>"
                f"{'%.4f' % hr if hr > 0 else '⚠️ غير محدد'}</span>",
                unsafe_allow_html=True,
            )

    # ── Selected Employees Counter ────────────────────────────────
    selected_ids = list(st.session_state["bulk_ot_selected_ids"])
    selected_count = len(selected_ids)

    st.markdown(
        f"<div style=\"background:{COLORS['primary']}18;border:1px solid {COLORS['primary']}40;"
        f"border-radius:8px;padding:10px 16px;margin:12px 0;font-size:14px;font-weight:700;"
        f"color:{COLORS['primary']};\">"
        f"👥 الموظفون المحددون: {selected_count}</div>",
        unsafe_allow_html=True,
    )

    # ── Selected Employees Preview Panel ─────────────────────────
    if selected_count > 0:
        with st.expander(f"👁 عرض الموظفين المحددين ({selected_count})", expanded=True):
            preview_rows = []
            for eid in selected_ids:
                emp = emp_by_id.get(eid)
                if emp:
                    hr = _calc_hourly_rate(emp)
                    preview_rows.append({
                        "الاسم":              emp.name,
                        "الكود":              emp.code,
                        "القسم":              emp.department or "—",
                        "معدل الساعة (ج.م)": f"{hr:.4f}" if hr > 0 else "⚠️ غير محدد",
                    })
            if preview_rows:
                st.dataframe(pd.DataFrame(preview_rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    section_card("بيانات الأوفر تايم", "⏱", COLORS['warning'])

    # ── Overtime Data Entry ───────────────────────────────────────
    with st.form("bulk_overtime_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        ot_date = col1.date_input("📅 التاريخ", value=date.today())
        hours   = col2.number_input("⏱ الساعات", min_value=0.0, max_value=24.0, step=0.5, value=2.0)
        notes   = st.text_input("📝 ملاحظات", placeholder="اختياري")

        st.info(
            "💡 سيتم حساب معدل الساعة والمبلغ تلقائياً لكل موظف بناءً على راتبه أو يوميته.",
            icon=None,
        )

        submitted = st.form_submit_button(
            "💾 حفظ الأوفر تايم للموظفين المحددين",
            type="primary",
            use_container_width=True,
        )

        if submitted:
            # Read final selection from the persistent set
            final_ids = list(st.session_state.get("bulk_ot_selected_ids", set()))

            if not final_ids:
                st.error("⚠️ يرجى تحديد موظف واحد على الأقل.")
            elif hours <= 0:
                st.error("⚠️ الساعات يجب أن تكون أكبر من صفر.")
            else:
                no_rate = [emp_by_id[eid].name for eid in final_ids if _calc_hourly_rate(emp_by_id[eid]) <= 0]
                if no_rate:
                    st.error(
                        f"⚠️ الموظفون التاليون ليس لديهم راتب أو يومية محددة:\n"
                        + "\n".join(f"• {n}" for n in no_rate)
                    )
                else:
                    db_w = get_db()
                    try:
                        total_amount  = 0.0
                        records_added = 0
                        for emp_id in final_ids:
                            emp         = emp_by_id[emp_id]
                            hr          = _calc_hourly_rate(emp)
                            amt         = round(hours * hr, 2)
                            total_amount += amt
                            db_w.add(Overtime(
                                employee_id=emp_id,
                                date=ot_date,
                                hours=hours,
                                rate_per_hour=hr,
                                amount=amt,
                                notes=_bot_tag_note(notes),
                            ))
                            records_added += 1
                        db_w.commit()
                        success_toast(
                            f"✅ تم حفظ الأوفر تايم بنجاح لـ {records_added} موظف. "
                            f"إجمالي المبلغ: {total_amount:,.2f} ج.م"
                        )
                        # Clear selections after successful save
                        st.session_state["bulk_ot_selected_ids"] = set()
                        st.rerun()
                    except Exception as e:
                        db_w.rollback()
                        danger_toast(f"خطأ أثناء الحفظ، تم التراجع عن جميع التغييرات: {e}")
                    finally:
                        db_w.close()


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
            'الموظف':      employees[r.employee_id].name if r.employee_id in employees else '—',
            'كود الموظف':  employees[r.employee_id].code if r.employee_id in employees else '—',
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
        ("📋", "عدد السجلات",    str(len(df)),                           COLORS['primary']),
        ("⏱",  "إجمالي الساعات", f"{df['الساعات'].sum():.1f} ساعة",    COLORS['warning']),
        ("💰", "إجمالي المبلغ",   f"{df['قيمة الأوفر'].sum():,.0f} ج.م", COLORS['success']),
    ])

    search = st.text_input("🔍 بحث في السجلات", placeholder="ابحث بالاسم أو القسم...")
    if search:
        mask = df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
        df = df[mask]

    st.dataframe(df, use_container_width=True, hide_index=True)


# ── Smart Paste Tab (additive — does not affect the two tabs above) ──
def _bot_match_employee(name: str, emp_by_norm: dict):
    """Exact match first, then loose substring fallback. Local to bulk overtime only."""
    emp = emp_by_norm.get(name)
    if emp:
        return emp
    for norm_name, ev in emp_by_norm.items():
        if name in norm_name or norm_name in name:
            return ev
    return None


def _smart_paste_overtime():
    import json as _json

    section_card("لصق نص ذكي للأوفر تايم الجماعي", "🧠", COLORS['primary'])

    st.markdown(
        f"<div style=\"background:{COLORS['primary']}12;border:1px solid {COLORS['primary']}30;"
        f"border-radius:8px;padding:10px 16px;margin-bottom:12px;font-size:13px;color:{COLORS['primary']};\">"
        f"💡 السطر الأول: التاريخ (مثال 16/6/2026) — السطر الثاني: عدد الساعات (مثال \"1 ساعة\")"
        f" — باقي السطور: اسم الموظف أو المعدة، ويمكن إضافة \"+1\" لعدد وحدات إضافية."
        f" المعدات (عربية / لودر / معدات...) تُعامل تمامًا كأي موظف — لا يوجد فصل بينهما."
        f"</div>",
        unsafe_allow_html=True,
    )

    sample = """16/6/2026
1 ساعة
علاء محمد
شريف أبو العزم+1
عادل عربي +1
محمود فتحي
عربية نقل عمال"""

    text = st.text_area(
        "📋 الصق النص هنا:",
        placeholder=sample,
        height=240,
        key="bot_smart_paste_input",
    )

    if not text.strip():
        return

    ot_date, hours, entries, errors = parse_bulk_overtime_text(text)

    if errors:
        st.error(" | ".join(errors))
        return

    db = get_db()
    try:
        employees = db.query(Employee).filter(Employee.status == 'Active').all()
        emp_by_norm = {e.name.strip(): e for e in employees}

        # All entries (employee names AND equipment names) go through the
        # exact same matching + rate-calculation + save pipeline. There is
        # no separate equipment path: an equipment entry only "counts" if it
        # matches an active record in the Employee table, exactly like any
        # other name — same as a worker would.
        matched_rows, unmatched_rows = [], []
        for e in entries:
            emp = _bot_match_employee(e["name"], emp_by_norm)
            if emp:
                hr = _calc_hourly_rate(emp)
                total_hours = e["overtime_units"]  # already base_hours + bonus
                matched_rows.append({
                    **e,
                    "employee_id": emp.id,
                    "rate_per_hour": hr,
                    "amount": round(total_hours * hr, 2),
                    "total_hours": total_hours,
                })
            else:
                unmatched_rows.append(e)
    finally:
        db.close()

    st.markdown(
        f"<div style='background:{COLORS['info']}18;border:1px solid {COLORS['info']}33;"
        f"border-radius:8px;padding:8px 16px;margin:8px 0;font-size:13px;color:{COLORS['info']};font-weight:600;'>"
        f"📅 التاريخ: {ot_date.strftime('%d/%m/%Y')} — ⏱ الساعات: {hours:g}</div>",
        unsafe_allow_html=True,
    )

    stat_pills([
        ("✅", "مطابقون (موظفون/معدات)", str(len(matched_rows)),   COLORS['success']),
        ("⚠️", "غير متطابق",            str(len(unmatched_rows)), COLORS['danger']),
    ])

    if matched_rows:
        st.dataframe(
            pd.DataFrame([{
                "الاسم": r["name"],
                "الوحدات": r["overtime_units"],
                "إجمالي الساعات": r["total_hours"],
                "معدل الساعة": r["rate_per_hour"],
                "المبلغ المتوقع": r["amount"],
            } for r in matched_rows]),
            use_container_width=True, hide_index=True,
        )

    if unmatched_rows:
        with st.expander(f"⚠️ أسماء غير متطابقة مع الموظفين/المعدات ({len(unmatched_rows)})", expanded=True):
            for r in unmatched_rows:
                st.markdown(f"- {r['name']} (وحدات: {r['overtime_units']})")

    with st.expander("🔧 عرض JSON الناتج عن التحليل", expanded=False):
        st.code(_json.dumps({
            "date": ot_date.isoformat(),
            "hours": hours,
            "entries": entries,
        }, ensure_ascii=False, indent=2), language="json")

    if matched_rows:
        if st.button(
            f"💾 حفظ أوفر تايم لـ {len(matched_rows)} عنصر مطابق (موظفون/معدات)",
            type="primary",
            use_container_width=True,
            key="bot_smart_save_btn",
        ):
            db_w = get_db()
            try:
                for r in matched_rows:
                    bonus = r['overtime_units'] - hours
                    note = "لصق نص ذكي" + (f" (+{bonus:g} ساعة إضافية)" if bonus > 0 else "")
                    db_w.add(Overtime(
                        employee_id=r["employee_id"],
                        date=ot_date,
                        hours=r["total_hours"],
                        rate_per_hour=r["rate_per_hour"],
                        amount=r["amount"],
                        notes=_bot_tag_note(note),
                    ))
                db_w.commit()
                success_toast(f"✅ تم حفظ الأوفر تايم لـ {len(matched_rows)} عنصر بنجاح.")
                st.rerun()
            except Exception as ex:
                db_w.rollback()
                danger_toast(f"خطأ أثناء الحفظ، تم التراجع عن جميع التغييرات: {ex}")
            finally:
                db_w.close()


# ── Delete Day Tab (additive — only ever deletes bulk-overtime-tagged rows) ──
def _delete_bulk_overtime_tab():
    section_card("حذف الأوفر تايم الجماعي بالتاريخ", "🗑️", COLORS['danger'])

    st.markdown(
        f"<div style=\"background:{COLORS['danger']}12;border:1px solid {COLORS['danger']}30;"
        f"border-radius:8px;padding:10px 16px;margin-bottom:12px;font-size:13px;color:{COLORS['danger']};\">"
        f"⚠️ يحذف هذا الإجراء سجلات الأوفر تايم <b>الجماعي فقط</b> (المُدخَلة من هذه الصفحة) ليوم واحد محدد."
        f" لا يؤثر على الأوفر تايم العادي ولا على أي تاريخ آخر."
        f"</div>",
        unsafe_allow_html=True,
    )

    target_date = st.date_input("📅 اختر التاريخ المطلوب حذفه", value=date.today(), key="bot_delete_date")

    db = get_db()
    try:
        records = db.query(Overtime).filter(
            Overtime.date == target_date,
            Overtime.notes.like(f"{_BOT_TAG}%"),
        ).all()
        preview_count = len(records)
        if preview_count:
            emp_ids = {r.employee_id for r in records}
            emps = {e.id: e for e in db.query(Employee).filter(Employee.id.in_(emp_ids)).all()}
            preview_rows = [{
                "الاسم":    emps[r.employee_id].name if r.employee_id in emps else "—",
                "الساعات":  r.hours,
                "المبلغ":   r.amount,
                "ملاحظات":  r.notes or "",
            } for r in records]
    finally:
        db.close()

    if preview_count == 0:
        empty_state("لا توجد سجلات أوفر تايم جماعي في هذا التاريخ", "🗑️")
        return

    st.markdown(
        f"<div style=\"background:{COLORS['warning']}18;border:1px solid {COLORS['warning']}40;"
        f"border-radius:8px;padding:10px 16px;margin:12px 0;font-size:14px;font-weight:700;"
        f"color:{COLORS['warning']};\">"
        f"سيتم حذف {preview_count} سجل أوفر تايم جماعي بتاريخ {target_date.strftime('%d/%m/%Y')}</div>",
        unsafe_allow_html=True,
    )

    with st.expander(f"👁 عرض السجلات المطلوب حذفها ({preview_count})", expanded=True):
        st.dataframe(pd.DataFrame(preview_rows), use_container_width=True, hide_index=True)

    confirm = st.checkbox(
        f"⚠️ أؤكد حذف جميع سجلات الأوفر تايم الجماعي ({preview_count}) بتاريخ "
        f"{target_date.strftime('%d/%m/%Y')} — لا يمكن التراجع عن هذا الإجراء.",
        key="bot_delete_confirm",
    )

    if st.button(
        "🗑️ حذف اليوم (Delete Day)",
        type="primary",
        use_container_width=True,
        disabled=not confirm,
        key="bot_delete_btn",
    ):
        deleted, err = delete_bulk_overtime_by_date(target_date)
        if err:
            danger_toast(f"خطأ أثناء الحذف: {err}")
        else:
            success_toast(
                f"✅ تم حذف {deleted} سجل أوفر تايم جماعي بتاريخ {target_date.strftime('%d/%m/%Y')}."
            )
            st.rerun()
