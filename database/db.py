from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from database.models import Base
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'hr.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# expire_on_commit=False prevents stale-data issues after commit/rerun cycles
engine = create_engine(
    f'sqlite:///{DB_PATH}',
    echo=False,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,   # ← FIX: prevents stale reads after commit
)


# SQLite ships with foreign-key *enforcement* OFF by default for every
# connection, even when the schema declares ForeignKey columns (this is a
# SQLite quirk, not a SQLAlchemy one). Turning it on here means the
# employees.id ForeignKey on Attendance/Overtime/Advance/PayrollCache
# actually protects data integrity (e.g. blocks inserting a row with an
# employee_id that doesn't exist) on every NEW database created by
# create_all(). It's a safe no-op for already-existing databases whose
# tables were created before the FK existed — SQLite can't retroactively
# enforce a constraint that was never part of a table's schema (see the
# note in _migrate_add_missing_columns below).
@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    _migrate_add_missing_columns()


# ── Lightweight migrations for existing SQLite DBs ───────────────────────
#
# Base.metadata.create_all() only creates tables that don't exist yet —
# it never alters a table that's already there. So whenever a column is
# added to a model after the app has already shipped, it needs an entry
# here too, or anyone upgrading from an older database silently keeps the
# old schema and the app breaks at the first query that touches the new
# column.
#
# Each entry is self-contained and independent, so adding a future
# column migration is just "append a dict to this list" — no need to
# touch the loop in _migrate_add_missing_columns itself.
#
# IMPORTANT — what this mechanism can and can't do:
#   - It CAN safely add a new nullable/defaulted column to an existing
#     table (SQLite supports `ALTER TABLE ... ADD COLUMN` for that).
#   - It CANNOT add or change a constraint (NOT NULL without a default,
#     UNIQUE, FOREIGN KEY, etc.) on a table that already exists — SQLite
#     has no `ALTER TABLE ... ADD CONSTRAINT`; that requires rebuilding
#     the table (create new table → copy data → drop old → rename), or a
#     real migration tool such as Alembic. The ForeignKey constraints
#     added to models.py, for example, will only be physically present
#     on brand-new databases; existing data/hr.db files won't gain them
#     retroactively. If/when more constraint-level changes are needed,
#     prefer adopting Alembic rather than growing ad-hoc table-rebuild
#     code here.
_COLUMN_MIGRATIONS = [
    {
        'table':    'attendance',
        'column':   'workers_count',
        'ddl':      "ALTER TABLE attendance ADD COLUMN workers_count FLOAT DEFAULT 1.0",
        'backfill': "UPDATE attendance SET workers_count = 1.0 WHERE workers_count IS NULL",
    },
    # Add future "new column on an existing table" migrations here, e.g.:
    # {
    #     'table':    'employees',
    #     'column':   'email',
    #     'ddl':      "ALTER TABLE employees ADD COLUMN email VARCHAR(120)",
    #     'backfill': None,
    # },
]

# Indexes that may be missing from databases created before they were
# added to models.py. Unlike column additions, `CREATE INDEX IF NOT
# EXISTS` is always safe to run unconditionally on every startup — no
# existence check needed beforehand, and no harm done on a brand-new DB
# where create_all() already created the very same index (names below
# match SQLAlchemy's default `ix_<table>_<column>` convention so no
# duplicate index is created).
_INDEX_MIGRATIONS = [
    "CREATE INDEX IF NOT EXISTS ix_attendance_employee_id ON attendance (employee_id)",
    "CREATE INDEX IF NOT EXISTS ix_attendance_attendance_date ON attendance (attendance_date)",
    "CREATE INDEX IF NOT EXISTS ix_attendance_status ON attendance (status)",
    "CREATE INDEX IF NOT EXISTS ix_attendance_date_status ON attendance (attendance_date, status)",
    "CREATE INDEX IF NOT EXISTS ix_overtime_employee_id ON overtime (employee_id)",
    "CREATE INDEX IF NOT EXISTS ix_overtime_date ON overtime (date)",
    "CREATE INDEX IF NOT EXISTS ix_advances_employee_id ON advances (employee_id)",
    "CREATE INDEX IF NOT EXISTS ix_advances_date ON advances (date)",
    "CREATE INDEX IF NOT EXISTS ix_payroll_cache_employee_id ON payroll_cache (employee_id)",
    "CREATE INDEX IF NOT EXISTS ix_expenses_date ON expenses (date)",
    "CREATE INDEX IF NOT EXISTS ix_expenses_category ON expenses (category)",
    "CREATE INDEX IF NOT EXISTS ix_received_funds_date ON received_funds (date)",
]


def _migrate_add_missing_columns():
    """
    Run all lightweight migrations. Safe to call on every app startup —
    every step below is a no-op once already applied.
    """
    with engine.connect() as conn:
        # 1) New columns on existing tables — each needs an explicit
        #    existence check since SQLite has no "ADD COLUMN IF NOT
        #    EXISTS".
        for m in _COLUMN_MIGRATIONS:
            cols = [row[1] for row in conn.exec_driver_sql(f"PRAGMA table_info({m['table']})").fetchall()]
            if not cols:
                continue  # table doesn't exist yet — create_all() already built it with the column included
            if m['column'] in cols:
                continue  # migration already applied previously
            conn.exec_driver_sql(m['ddl'])
            if m.get('backfill'):
                conn.exec_driver_sql(m['backfill'])
            conn.commit()

        # 2) Indexes — safe to (re)run unconditionally every startup.
        for stmt in _INDEX_MIGRATIONS:
            conn.exec_driver_sql(stmt)
        conn.commit()


def get_db() -> Session:
    """Return a fresh database session. Caller MUST call db.close() in a finally block."""
    return SessionLocal()
