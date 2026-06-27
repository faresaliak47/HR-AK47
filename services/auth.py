"""Authentication service for HR Pro."""
import hashlib
import secrets
import streamlit as st
from database.db import get_db
from database.models import User


# ── Password hashing (sha256 + salt) ──────────────────────────────────────────
def _hash_password(password: str, salt: str = None) -> tuple[str, str]:
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return hashed, salt


def _verify_password(password: str, stored_hash: str) -> bool:
    """stored_hash format: salt$hash"""
    try:
        salt, hashed = stored_hash.split('$', 1)
        computed, _ = _hash_password(password, salt)
        return computed == hashed
    except Exception as e:
        print(f"[auth] Password verification error: {e}")
        return False


def make_password_hash(password: str) -> str:
    hashed, salt = _hash_password(password)
    return f"{salt}${hashed}"


# ── Role permissions ───────────────────────────────────────────────────────────
ROLE_PERMISSIONS = {
    'admin':      ['dashboard', 'employees', 'attendance', 'overtime', 'advances', 'payroll', 'reports', 'user_management'],
    'hr':         ['dashboard', 'employees', 'attendance', 'reports'],
    'accountant': ['dashboard', 'payroll', 'advances', 'reports'],
    'viewer':     ['dashboard'],
}

ROLE_LABELS = {
    'admin':      '🔑 مدير النظام',
    'hr':         '👥 مسؤول الموارد البشرية',
    'accountant': '📊 محاسب',
    'viewer':     '👁️ مشاهد',
}


def can_access(page_key: str) -> bool:
    role = st.session_state.get('user_role', 'viewer')
    return page_key in ROLE_PERMISSIONS.get(role, [])


def is_logged_in() -> bool:
    return st.session_state.get('logged_in', False)


def needs_setup() -> bool:
    """Return True if no users exist yet (first-run)."""
    db = get_db()
    try:
        return db.query(User).count() == 0
    finally:
        db.close()


def login(username: str, password: str) -> bool:
    db = get_db()
    try:
        user = db.query(User).filter(
            User.username == username,
            User.is_active == True
        ).first()
        if user and _verify_password(password, user.password_hash):
            st.session_state['logged_in'] = True
            st.session_state['user_id']   = user.id
            st.session_state['username']  = user.username
            st.session_state['full_name'] = user.full_name
            st.session_state['user_role'] = user.role
            return True
        return False
    finally:
        db.close()


def logout():
    keys = [
        'logged_in', 'user_id', 'username', 'full_name', 'user_role',
        'payroll_df', 'payroll_month', 'payroll_year',
    ]
    for key in keys:
        st.session_state.pop(key, None)
    # Explicitly mark as logged out so the login page renders
    st.session_state['logged_in'] = False


# ── User management ────────────────────────────────────────────────────────────
def create_user(username: str, password: str, full_name: str, role: str = 'viewer') -> tuple[bool, str]:
    db = get_db()
    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            return False, "اسم المستخدم مستخدم بالفعل."
        user = User(
            username=username,
            password_hash=make_password_hash(password),
            full_name=full_name,
            role=role,
            is_active=True,
        )
        db.add(user)
        db.commit()
        return True, "تم إنشاء المستخدم بنجاح."
    except Exception as e:
        db.rollback()
        return False, f"خطأ: {e}"
    finally:
        db.close()


def update_user(user_id: int, full_name: str, role: str) -> tuple[bool, str]:
    db = get_db()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "المستخدم غير موجود."
        user.full_name = full_name
        user.role = role
        db.commit()
        return True, "تم تحديث بيانات المستخدم."
    except Exception as e:
        db.rollback()
        return False, f"خطأ: {e}"
    finally:
        db.close()


def reset_password(user_id: int, new_password: str) -> tuple[bool, str]:
    db = get_db()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "المستخدم غير موجود."
        user.password_hash = make_password_hash(new_password)
        db.commit()
        return True, "تم تغيير كلمة المرور بنجاح."
    except Exception as e:
        db.rollback()
        return False, f"خطأ: {e}"
    finally:
        db.close()


def set_user_active(user_id: int, is_active: bool) -> tuple[bool, str]:
    db = get_db()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "المستخدم غير موجود."
        user.is_active = is_active
        db.commit()
        status = "تم تفعيل" if is_active else "تم تعطيل"
        return True, f"{status} المستخدم بنجاح."
    except Exception as e:
        db.rollback()
        return False, f"خطأ: {e}"
    finally:
        db.close()


def get_all_users():
    db = get_db()
    try:
        return db.query(User).order_by(User.id).all()
    finally:
        db.close()
