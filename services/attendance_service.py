import re
from datetime import date, datetime
from database.db import get_db
from database.models import Employee, Attendance
import pandas as pd


# ── Arabic/English noise words to strip from name lines ──────────
# These are the "multiplier unit" words that can sit next to a count
# (e.g. "5 عمال أشرف", "3 ع محمد", "2 workers Ali") and must be removed
# from the name without affecting the parsed count.
_NOISE_WORDS = re.compile(
    r'\b(عمال|عامل|موظف|موظفون|مهندس|مساعد|فني|ع|workers?)\b',
    re.UNICODE | re.IGNORECASE,
)

# Arabic-Indic digits (٠-٩) → Western digits (0-9)
_AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

# Matches an integer or decimal number (accepts "." or "," as the separator),
# anywhere in the line — not just at the start.
_COUNT_RE = re.compile(r'(\d+(?:[.,]\d+)?)')


def normalize_name(name: str) -> str:
    """Remove prefixes and normalize Arabic name for matching."""
    name = name.strip()
    prefixes = ['م ', 'م. ', 'أ. ', 'أ ', 'د. ', 'د ', 'مهندس ', 'دكتور ']
    for p in prefixes:
        if name.startswith(p):
            name = name[len(p):]
    return name.strip()


def parse_smart_line(line: str) -> dict:
    """
    Parse a single smart-attendance line.

    Formats handled:
      • "خالد طارق"          → {name: "خالد طارق", workers_count: 1}
      • "6 عمال سامح"        → {name: "سامح",       workers_count: 6}
      • "2 أشرف"             → {name: "أشرف",        workers_count: 2}
      • "3 ع محمد"           → {name: "محمد",        workers_count: 3}
      • "2 workers Ali"      → {name: "Ali",         workers_count: 2}
      • "عمال خالد 3.5"      → {name: "خالد",        workers_count: 3.5}  (fractional, trailing count)
      • "م محمد"             → {name: "محمد",        workers_count: 1}  (old prefix style)

    The count can be a whole number or a fraction (e.g. "3.5" or "3,5"),
    and can appear either before or after the name. Arabic-Indic digits
    (٠-٩) are normalized to Western digits first. If no number is found,
    workers_count defaults to 1 (a single person).

    Returns dict with keys: name (str), workers_count (int | float)
    """
    line = line.strip()
    if not line:
        return None

    line = line.translate(_AR_DIGITS)

    workers_count = 1
    m = _COUNT_RE.search(line)
    if m:
        num_str = m.group(1).replace(',', '.')
        try:
            workers_count = float(num_str)
            if workers_count.is_integer():
                workers_count = int(workers_count)
        except ValueError:
            workers_count = 1
        else:
            # Remove just the matched number, wherever it sits in the line
            line = (line[:m.start()] + ' ' + line[m.end():]).strip()

    # Strip noise words (e.g. "عمال", "عامل")
    name = _NOISE_WORDS.sub('', line).strip()
    name = re.sub(r'\s+', ' ', name).strip()

    # Strip legacy name prefixes
    name = normalize_name(name)

    if not name:
        return None

    return {'name': name, 'workers_count': workers_count}


def parse_smart_attendance_text(text: str):
    """
    Parse the smart pasted attendance format.

    First line may optionally be a date (DD/MM/YYYY).
    Remaining lines are employee entries (with optional leading count).

    Returns:
        att_date  – date object (today if not found in text)
        entries   – list of {name, workers_count}
        errors    – list of error strings
    """
    lines = [l.strip() for l in text.strip().splitlines()]
    lines = [l for l in lines if l]

    if not lines:
        return None, [], ['النص فارغ']

    att_date = None
    start_idx = 0

    # Try to parse first line as a date
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y'):
        try:
            att_date = datetime.strptime(lines[0], fmt).date()
            start_idx = 1
            break
        except ValueError:
            continue

    # Default to today if no date found
    if att_date is None:
        att_date = date.today()

    entries = []
    for line in lines[start_idx:]:
        parsed = parse_smart_line(line)
        if parsed:
            entries.append(parsed)

    if not entries:
        return att_date, [], ['لم يتم العثور على أسماء صالحة في النص']

    return att_date, entries, []


def process_smart_attendance(text: str):
    """
    Parse smart attendance text and save to DB.

    Each entry's workers_count is stored on the Attendance record
    (falls back gracefully if column absent).

    Returns result dict compatible with the UI.
    """
    att_date, entries, errors = parse_smart_attendance_text(text)
    if errors:
        return {'success': False, 'errors': errors}

    db = get_db()
    try:
        employees = db.query(Employee).filter(Employee.status == 'Active').all()
        emp_map = {normalize_name(e.name): e for e in employees}

        matched      = []
        unmatched    = []
        saved        = 0
        duplicates   = 0
        seen_in_batch = set()   # employee_ids already queued for insert in THIS run

        for entry in entries:
            name          = entry['name']
            workers_count = entry['workers_count']

            emp = emp_map.get(name)
            if emp is None:
                # Fuzzy fallback: substring match
                for en, ev in emp_map.items():
                    if name in en or en in name:
                        emp = ev
                        break

            if emp:
                already_in_db = db.query(Attendance).filter(
                    Attendance.employee_id == emp.id,
                    Attendance.attendance_date == att_date
                ).first()
                if already_in_db or emp.id in seen_in_batch:
                    duplicates += 1
                else:
                    att = Attendance(
                        employee_id=emp.id,
                        attendance_date=att_date,
                        status=1,            # presence "credit" for payroll — always 1 per day, unaffected by count
                        workers_count=workers_count,  # real headcount for the matrix
                    )
                    db.add(att)
                    seen_in_batch.add(emp.id)
                    saved += 1
                matched.append({'name': emp.name, 'workers_count': workers_count})
            else:
                unmatched.append({'name': name, 'workers_count': workers_count})

        db.commit()
        return {
            'success':    True,
            'date':       att_date,
            'matched':    matched,
            'unmatched':  unmatched,
            'saved':      saved,
            'duplicates': duplicates,
            'entries':    entries,
        }
    except Exception as e:
        db.rollback()
        return {'success': False, 'errors': [str(e)]}
    finally:
        db.close()


# ── Legacy functions (unchanged) ─────────────────────────────────

def parse_attendance_text(text: str):
    """Parse attendance plain text. Returns (date, names_list, errors)."""
    lines = [l.strip() for l in text.strip().splitlines()]
    lines = [l for l in lines if l]
    if not lines:
        return None, [], ['النص فارغ']
    date_line = lines[0]
    att_date = None
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y'):
        try:
            att_date = datetime.strptime(date_line, fmt).date()
            break
        except ValueError:
            continue
    if att_date is None:
        return None, [], [f'تنسيق التاريخ غير صحيح: {date_line}']
    names = list(dict.fromkeys([normalize_name(l) for l in lines[1:] if l.strip()]))
    return att_date, names, []


def process_attendance(text: str):
    """Process attendance text and save to DB. Returns result dict."""
    att_date, names, errors = parse_attendance_text(text)
    if errors:
        return {'success': False, 'errors': errors}
    db = get_db()
    try:
        employees = db.query(Employee).filter(Employee.status == 'Active').all()
        emp_map = {normalize_name(e.name): e for e in employees}
        matched = []
        unmatched = []
        saved = 0
        duplicates = 0
        seen_in_batch = set()   # employee_ids already queued for insert in THIS run
        for name in names:
            emp = emp_map.get(name)
            if emp is None:
                for en, ev in emp_map.items():
                    if name in en or en in name:
                        emp = ev
                        break
            if emp:
                already_in_db = db.query(Attendance).filter(
                    Attendance.employee_id == emp.id,
                    Attendance.attendance_date == att_date
                ).first()
                if already_in_db or emp.id in seen_in_batch:
                    duplicates += 1
                else:
                    att = Attendance(employee_id=emp.id, attendance_date=att_date, status=1)
                    db.add(att)
                    seen_in_batch.add(emp.id)
                    saved += 1
                matched.append(emp.name)
            else:
                unmatched.append(name)
        db.commit()
        return {
            'success': True,
            'date': att_date,
            'matched': matched,
            'unmatched': unmatched,
            'saved': saved,
            'duplicates': duplicates
        }
    except Exception as e:
        db.rollback()
        return {'success': False, 'errors': [str(e)]}
    finally:
        db.close()


def get_attendance_matrix(month: int, year: int, department: str = None, employee_id: int = None) -> pd.DataFrame:
    """Generate attendance matrix for a given month/year."""
    import calendar
    db = get_db()
    try:
        days_in_month = calendar.monthrange(year, month)[1]
        query = db.query(Employee)
        if department:
            query = query.filter(Employee.department == department)
        if employee_id:
            query = query.filter(Employee.id == employee_id)
        employees = query.filter(Employee.status == 'Active').all()
        if not employees:
            return pd.DataFrame()
        emp_ids = [e.id for e in employees]
        from sqlalchemy import and_
        start_date = date(year, month, 1)
        end_date = date(year, month, days_in_month)
        records = db.query(Attendance).filter(
            Attendance.employee_id.in_(emp_ids),
            Attendance.attendance_date >= start_date,
            Attendance.attendance_date <= end_date
        ).all()
        # Matrix cells show the real headcount for that day (workers_count),
        # not just a presence flag. Older rows or rows saved without a
        # parsed count default to 1 person, same as before.
        att_set = {
            (r.employee_id, r.attendance_date.day):
                (r.workers_count if r.workers_count is not None else r.status)
            for r in records
        }
        rows = []
        for emp in employees:
            row = {'كود الموظف': emp.code, 'اسم الموظف': emp.name}
            for d in range(1, days_in_month + 1):
                row[str(d)] = att_set.get((emp.id, d), 0)
            row['إجمالي الحضور'] = sum(att_set.get((emp.id, d), 0) for d in range(1, days_in_month + 1))
            rows.append(row)
        return pd.DataFrame(rows)
    finally:
        db.close()
