from sqlalchemy import (
    Column, Integer, String, Float, Date, Text, UniqueConstraint, Boolean,
    DateTime, ForeignKey, Index,
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id           = Column(Integer, primary_key=True, autoincrement=True)
    username     = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name    = Column(String(100), nullable=False)
    role         = Column(String(20), default='viewer')   # admin | hr | accountant | viewer
    is_active    = Column(Boolean, default=True)
    created_at   = Column(DateTime, default=datetime.utcnow)


class Employee(Base):
    __tablename__ = 'employees'
    id          = Column(Integer, primary_key=True, autoincrement=True)
    code        = Column(String(20), unique=True, nullable=False)
    name        = Column(String(100), nullable=False)
    job_title   = Column(String(100))
    department  = Column(String(100))
    salary      = Column(Float, default=0.0)
    daily_rate  = Column(Float, default=0.0)
    phone       = Column(String(20))
    national_id = Column(String(20))
    area        = Column(String(100))
    hire_date   = Column(Date)
    status      = Column(String(20), default='Active')

    # ── Relationships ────────────────────────────────────────────────
    # cascade="all, delete-orphan" makes SQLAlchemy itself walk these
    # collections and delete the child rows whenever an Employee is
    # deleted through the ORM (session.delete(...)), so the delete
    # button in page_modules/employees.py can no longer leave orphaned
    # attendance/overtime/advance/payroll rows behind. This works
    # independently of whatever the underlying SQLite file's physical
    # schema looks like (see note in database/db.py about FK
    # enforcement on already-existing databases), so it protects data
    # integrity on both old and freshly-created databases.
    attendances = relationship(
        'Attendance', back_populates='employee',
        cascade='all, delete-orphan',
    )
    overtimes = relationship(
        'Overtime', back_populates='employee',
        cascade='all, delete-orphan',
    )
    advances = relationship(
        'Advance', back_populates='employee',
        cascade='all, delete-orphan',
    )
    payroll_entries = relationship(
        'PayrollCache', back_populates='employee',
        cascade='all, delete-orphan',
    )


class Attendance(Base):
    __tablename__ = 'attendance'
    id              = Column(Integer, primary_key=True, autoincrement=True)
    employee_id     = Column(
        Integer, ForeignKey('employees.id', ondelete='CASCADE'),
        nullable=False, index=True,
    )
    attendance_date = Column(Date, nullable=False, index=True)
    status          = Column(Integer, default=1, index=True)
    # Real headcount represented by this row (e.g. "5 عمال أشرف" -> 5).
    # Separate from `status`, which stays the 1-per-day attendance "credit"
    # used by payroll (services/payroll_service.py counts ROWS, not this
    # value, so payroll/day-credit logic is unaffected by this field).
    workers_count   = Column(Float, default=1.0)
    __table_args__  = (
        UniqueConstraint('employee_id', 'attendance_date', name='uq_emp_date'),
        # Speeds up the very common "month + status" filter used by
        # payroll_service.calculate_payroll() / attendance_service /
        # the monthly attendance matrix, on top of the single-column
        # indexes above.
        Index('ix_attendance_date_status', 'attendance_date', 'status'),
    )

    employee = relationship('Employee', back_populates='attendances')


class Overtime(Base):
    __tablename__ = 'overtime'
    id           = Column(Integer, primary_key=True, autoincrement=True)
    employee_id  = Column(
        Integer, ForeignKey('employees.id', ondelete='CASCADE'),
        nullable=False, index=True,
    )
    date         = Column(Date, nullable=False, index=True)
    hours        = Column(Float, default=0.0)
    rate_per_hour = Column(Float, default=0.0)
    amount       = Column(Float, default=0.0)
    notes        = Column(Text)

    employee = relationship('Employee', back_populates='overtimes')


class Advance(Base):
    __tablename__ = 'advances'
    id          = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(
        Integer, ForeignKey('employees.id', ondelete='CASCADE'),
        nullable=False, index=True,
    )
    date        = Column(Date, nullable=False, index=True)
    amount      = Column(Float, default=0.0)
    notes       = Column(Text)

    employee = relationship('Employee', back_populates='advances')


class PayrollCache(Base):
    __tablename__ = 'payroll_cache'
    id              = Column(Integer, primary_key=True, autoincrement=True)
    employee_id     = Column(
        Integer, ForeignKey('employees.id', ondelete='CASCADE'),
        nullable=False, index=True,
    )
    month           = Column(Integer, nullable=False)
    year            = Column(Integer, nullable=False)
    attendance_days = Column(Integer, default=0)
    daily_rate      = Column(Float, default=0.0)
    base_salary     = Column(Float, default=0.0)
    overtime        = Column(Float, default=0.0)
    advances        = Column(Float, default=0.0)
    net_salary      = Column(Float, default=0.0)
    __table_args__  = (UniqueConstraint('employee_id', 'month', 'year', name='uq_payroll'),)

    employee = relationship('Employee', back_populates='payroll_entries')


class Expense(Base):
    """
    Petty-cash expenses entered on the Expenses page (Smart Paste or the
    manual-entry form), excluding employee advances — those are tracked
    separately in `Advance`, which already has its own table and is tied
    into payroll.

    Previously these rows lived only in st.session_state and were wiped
    on every page refresh / Streamlit rerun. This table makes them
    durable across sessions and restarts.
    """
    __tablename__ = 'expenses'
    id          = Column(Integer, primary_key=True, autoincrement=True)
    date        = Column(Date, nullable=False, index=True)
    description = Column(String(255), nullable=False, default='مصروف')
    category    = Column(String(50), default='أخرى', index=True)
    amount      = Column(Float, default=0.0)
    notes       = Column(Text)
    created_at  = Column(DateTime, default=datetime.utcnow)


class ReceivedFund(Base):
    """
    Income / petty-cash funding records (bank transfers, cash handed to
    the site, etc.) from the "صندوق الوارد" tab of the Expenses page.

    Stored for the same reason as `Expense`: without a table, the
    received-funds list reset on every refresh, which made the balance
    report on that page unreliable.
    """
    __tablename__ = 'received_funds'
    id         = Column(Integer, primary_key=True, autoincrement=True)
    date       = Column(Date, nullable=False, index=True)
    amount     = Column(Float, default=0.0)
    tax        = Column(Float, default=0.0)
    net_amount = Column(Float, default=0.0)
    source     = Column(String(100))
    notes      = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
