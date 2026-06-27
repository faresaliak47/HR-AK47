import io
import calendar
from datetime import date
import pandas as pd
from database.db import get_db
from database.models import Employee, Attendance, Overtime, Advance
from services.payroll_service import calculate_payroll
from services.attendance_service import get_attendance_matrix
from components.theme import COLORS, COMPANY_NAME, COMPANY_TAGLINE


def export_full_report(month: int, year: int) -> bytes:
    """Generate full Excel report workbook."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        wb = writer.book

        # Formats — branded with TURF Landscape Co. colors
        header_fmt = wb.add_format({
            'bold': True, 'bg_color': COLORS['primary'], 'font_color': 'white',
            'border': 1, 'align': 'center', 'font_name': 'Arial', 'font_size': 11
        })
        cell_fmt = wb.add_format({'border': 1, 'align': 'center', 'font_name': 'Arial'})
        total_fmt = wb.add_format({
            'bold': True, 'bg_color': '#DCEFE8', 'border': 1,
            'align': 'center', 'font_name': 'Arial'
        })
        num_fmt = wb.add_format({'border': 1, 'align': 'center', 'num_format': '#,##0.00', 'font_name': 'Arial'})

        db = get_db()
        try:
            # Sheet 1: Employees
            employees = db.query(Employee).all()
            emp_data = [{
                'كود': e.code, 'الاسم': e.name, 'المسمى الوظيفي': e.job_title or '',
                'القسم': e.department or '', 'الراتب': e.salary, 'المعدل اليومي': e.daily_rate,
                'الهاتف': e.phone or '', 'الرقم القومي': e.national_id or '',
                'المنطقة': e.area or '', 'تاريخ التعيين': str(e.hire_date or ''),
                'الحالة': e.status
            } for e in employees]
            emp_df = pd.DataFrame(emp_data)
            emp_df.to_excel(writer, sheet_name='الموظفون', index=False)
            _format_sheet(writer, 'الموظفون', emp_df, header_fmt, cell_fmt, wb)

            # Sheet 2: Attendance Records
            days_in_month = calendar.monthrange(year, month)[1]
            start_date = date(year, month, 1)
            end_date = date(year, month, days_in_month)
            att_records = db.query(Attendance).filter(
                Attendance.attendance_date >= start_date,
                Attendance.attendance_date <= end_date
            ).all()
            emp_dict = {e.id: e for e in employees}
            att_data = [{
                'كود الموظف': emp_dict[r.employee_id].code if r.employee_id in emp_dict else '',
                'اسم الموظف': emp_dict[r.employee_id].name if r.employee_id in emp_dict else '',
                'التاريخ': str(r.attendance_date),
                'الحالة': 'حاضر' if r.status == 1 else 'غائب'
            } for r in att_records]
            att_df = pd.DataFrame(att_data) if att_data else pd.DataFrame(columns=['كود الموظف', 'اسم الموظف', 'التاريخ', 'الحالة'])
            att_df.to_excel(writer, sheet_name='سجلات الحضور', index=False)
            _format_sheet(writer, 'سجلات الحضور', att_df, header_fmt, cell_fmt, wb)

            # Sheet 3: Attendance Matrix
            matrix_df = get_attendance_matrix(month, year)
            if not matrix_df.empty:
                matrix_df.to_excel(writer, sheet_name='مصفوفة الحضور', index=False)
                ws = writer.sheets['مصفوفة الحضور']
                for col_num, col_name in enumerate(matrix_df.columns):
                    ws.write(0, col_num, col_name, header_fmt)
                    max_len = max(len(str(col_name)), matrix_df[col_name].astype(str).str.len().max() if len(matrix_df) > 0 else 5)
                    ws.set_column(col_num, col_num, min(max_len + 2, 20))
                for row_num, row in enumerate(matrix_df.itertuples(index=False), start=1):
                    for col_num, val in enumerate(row):
                        ws.write(row_num, col_num, val, cell_fmt)

            # Sheet 4: Overtime
            ot_records = db.query(Overtime).filter(
                Overtime.date >= start_date, Overtime.date <= end_date
            ).all()
            ot_data = [{
                'كود الموظف': emp_dict[r.employee_id].code if r.employee_id in emp_dict else '',
                'اسم الموظف': emp_dict[r.employee_id].name if r.employee_id in emp_dict else '',
                'التاريخ': str(r.date), 'الساعات': r.hours,
                'معدل الساعة': r.rate_per_hour, 'الإجمالي': r.amount,
                'ملاحظات': r.notes or ''
            } for r in ot_records]
            ot_df = pd.DataFrame(ot_data) if ot_data else pd.DataFrame(columns=['كود الموظف', 'اسم الموظف', 'التاريخ', 'الساعات', 'معدل الساعة', 'الإجمالي', 'ملاحظات'])
            ot_df.to_excel(writer, sheet_name='الأوفر تايم', index=False)
            _format_sheet(writer, 'الأوفر تايم', ot_df, header_fmt, cell_fmt, wb)

            # Sheet 5: Advances
            adv_records = db.query(Advance).filter(
                Advance.date >= start_date, Advance.date <= end_date
            ).all()
            adv_data = [{
                'كود الموظف': emp_dict[r.employee_id].code if r.employee_id in emp_dict else '',
                'اسم الموظف': emp_dict[r.employee_id].name if r.employee_id in emp_dict else '',
                'التاريخ': str(r.date), 'المبلغ': r.amount, 'ملاحظات': r.notes or ''
            } for r in adv_records]
            adv_df = pd.DataFrame(adv_data) if adv_data else pd.DataFrame(columns=['كود الموظف', 'اسم الموظف', 'التاريخ', 'المبلغ', 'ملاحظات'])
            adv_df.to_excel(writer, sheet_name='السلف', index=False)
            _format_sheet(writer, 'السلف', adv_df, header_fmt, cell_fmt, wb)

            # Sheet 6: Payroll Summary
            payroll_df = calculate_payroll(month, year)
            if not payroll_df.empty:
                totals = {
                    'كود الموظف': '', 'اسم الموظف': 'الإجمالي', 'القسم': '',
                    'أيام الحضور': payroll_df['أيام الحضور'].sum(),
                    'المعدل اليومي': '',
                    'الراتب الأساسي': payroll_df['الراتب الأساسي'].sum(),
                    'الأوفر تايم': payroll_df['الأوفر تايم'].sum(),
                    'السلف': payroll_df['السلف'].sum(),
                    'صافي الراتب': payroll_df['صافي الراتب'].sum()
                }
                totals_df = pd.DataFrame([totals])
                payroll_full = pd.concat([payroll_df, totals_df], ignore_index=True)
                payroll_full.to_excel(writer, sheet_name='مسير الرواتب', index=False)
                ws = writer.sheets['مسير الرواتب']
                for col_num, col_name in enumerate(payroll_full.columns):
                    ws.write(0, col_num, col_name, header_fmt)
                    ws.set_column(col_num, col_num, 18)
                for row_num, row in enumerate(payroll_full.itertuples(index=False), start=1):
                    fmt = total_fmt if row_num == len(payroll_full) else cell_fmt
                    for col_num, val in enumerate(row):
                        ws.write(row_num, col_num, val, fmt)
        finally:
            db.close()

    return output.getvalue()


def _format_sheet(writer, sheet_name, df, header_fmt, cell_fmt, wb):
    if sheet_name not in writer.sheets:
        return
    ws = writer.sheets[sheet_name]
    for col_num, col_name in enumerate(df.columns):
        ws.write(0, col_num, col_name, header_fmt)
        max_len = max(len(str(col_name)), df[col_name].astype(str).str.len().max() if len(df) > 0 else 5)
        ws.set_column(col_num, col_num, min(max_len + 4, 30))
