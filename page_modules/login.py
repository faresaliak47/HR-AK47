"""Login page for TURF Landscape Co. — HR Pro authentication."""
import streamlit as st
import base64
from services.auth import login
from components.theme import COLORS, COMPANY_NAME, COMPANY_TAGLINE, LOGO_PATH


def _logo_data_uri() -> str:
    try:
        with open(LOGO_PATH, "rb") as f:
            return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()
    except Exception as e:
        print(f"[login] Could not load logo: {e}")
        return ""


def show_login():
    """Render the login page — no default credentials shown."""
    _, col, _ = st.columns([1, 2, 1])
    with col:
        logo_uri = _logo_data_uri()
        logo_html = (
            f'<img src="{logo_uri}" style="width:96px;height:auto;margin:0 auto 14px;display:block;" />'
            if logo_uri else
            f'''<div style="background:linear-gradient(135deg,{COLORS['primary']},{COLORS['primary_light']});
              border-radius:20px;width:72px;height:72px;
              display:flex;align-items:center;justify-content:center;
              font-size:34px;margin:0 auto 16px;
              box-shadow:0 8px 24px {COLORS['primary']}55;">🌳</div>'''
        )
        st.markdown(f"""
<div style="text-align:center;padding:32px 0 24px;">
  {logo_html}
  <div style="font-size:22px;font-weight:900;color:{COLORS['primary']};letter-spacing:-0.5px;">{COMPANY_NAME}</div>
  <div style="font-size:13px;color:{COLORS['text_muted']};margin-top:4px;">{COMPANY_TAGLINE}</div>
</div>
""", unsafe_allow_html=True)

        st.markdown(f"""
<div style="background:{COLORS['surface']};border-radius:16px;padding:28px 24px 8px;
            border:1px solid {COLORS['border']};box-shadow:0 4px 24px {COLORS['shadow']};
            margin-bottom:16px;">
  <div style="font-size:16px;font-weight:700;color:{COLORS['text']};margin-bottom:16px;text-align:center;">
    🔐 تسجيل الدخول
  </div>
</div>
""", unsafe_allow_html=True)

        with st.form("login_form"):
            username  = st.text_input("اسم المستخدم", placeholder="أدخل اسم المستخدم")
            password  = st.text_input("كلمة المرور", type="password", placeholder="أدخل كلمة المرور")
            submitted = st.form_submit_button("🔑 دخول", type="primary", use_container_width=True)

            if submitted:
                if not username.strip() or not password:
                    st.error("يرجى إدخال اسم المستخدم وكلمة المرور.")
                elif login(username.strip(), password):
                    st.success(f"أهلاً {st.session_state.get('full_name', username)}! 👋")
                    st.rerun()
                else:
                    st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة.")
