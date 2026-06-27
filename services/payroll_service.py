import calendar
from datetime import date
import pandas as pd
from database.db import get_db
from database.models import Employee, Attendance, Overtime, Advance, PayrollCache


def calculate_payroll(month: int, year: int) -> pd.DataFrame:
    """Calculate payroll for all active employees for a given month/year."""
    db = get_db()
    try:
        days_in_month = calendar.monthrange(year, month)[1]
        start_date = date(year, month, 1)
        end_date = date(year, month, days_in_month)
        employees = db.query(Employee).filter(Employee.status == 'Active').all()
        if not employees:
            return pd.DataFrame()
        emp_ids = [e.id for e in employees]
        att_records = db.query(Attendance).filter(
            Attendance.employee_id.in_(emp_ids),
            Attendance.attendance_date >= start_date,
            Attendance.attendance_date <= end_date,
            Attendance.status == 1
        ).all()
        att_count = {}
        for r in att_records:
            att_count[r.employee_id] = att_count.get(r.employee_id, 0) + 1
        ot_records = db.query(Overtime).filter(
            Overtime.employee_id.in_(emp_ids),
            Overtime.date >= start_date,
            Overtime.date <= end_date
        ).all()
        ot_total = {}
        for r in ot_records:
            ot_total[r.employee_id] = ot_total.get(r.employee_id, 0) + r.amount
        adv_records = db.query(Advance).filter(
            Advance.employee_id.in_(emp_ids),
            Advance.date >= start_date,
            Advance.date <= end_date
        ).all()
        adv_total = {}
        for r in adv_records:
            adv_total[r.employee_id] = adv_total.get(r.employee_id, 0) + r.amount
        rows = []
        for emp in employees:
            att_days = att_count.get(emp.id, 0)
            ot = ot_total.get(emp.id, 0.0)
            adv = adv_total.get(emp.id, 0.0)
            base = att_days * emp.daily_rate
            net = base + ot - adv
            rows.append({
                'كود الموظف': emp.code,
                'اسم الموظف': emp.name,
                'القسم': emp.department or '',
                'أيام الحضور': att_days,
                'المعدل اليومي': emp.daily_rate,
                'الراتب الأساسي': base,
                'الأوفر تايم': ot,
                'السلف': adv,
                'صافي الراتب': net
            })
        return pd.DataFrame(rows)
    finally:
        db.close()


def save_payroll_cache(month: int, year: int):
    """Save calculated payroll to cache table."""
    df = calculate_payroll(month, year)
    if df.empty:
        return
    db = get_db()
    try:
        employees = {e.code: e.id for e in db.query(Employee).all()}
        for _, row in df.iterrows():
            emp_id = employees.get(row['كود الموظف'])
            if not emp_id:
                continue
            existing = db.query(PayrollCache).filter(
                PayrollCache.employee_id == emp_id,
                PayrollCache.month == month,
                PayrollCache.year == year
            ).first()
            if existing:
                existing.attendance_days = row['أيام الحضور']
                existing.daily_rate = row['المعدل اليومي']
                existing.base_salary = row['الراتب الأساسي']
                existing.overtime = row['الأوفر تايم']
                existing.advances = row['السلف']
                existing.net_salary = row['صافي الراتب']
            else:
                pc = PayrollCache(
                    employee_id=emp_id, month=month, year=year,
                    attendance_days=row['أيام الحضور'],
                    daily_rate=row['المعدل اليومي'],
                    base_salary=row['الراتب الأساسي'],
                    overtime=row['الأوفر تايم'],
                    advances=row['السلف'],
                    net_salary=row['صافي الراتب']
                )
                db.add(pc)
        db.commit()
    except Exception as e:
        print(f"[payroll] Error saving payroll: {e}")
        db.rollback()
        raise
    finally:
        db.close()
