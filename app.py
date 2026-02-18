import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(page_title="Invoice Pro", layout="wide", page_icon="📄")

from supabase import create_client

@st.cache_resource
def get_supabase():
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    return create_client(url, key)

supabase = get_supabase()

if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None

if not st.session_state.user:
    from views.auth_page import show_auth
    show_auth(supabase)
else:
    from utils.auth import check_access, logout

    # Check if access is still valid
    if not check_access(supabase, st.session_state.user["id"]):
        st.error("⛔ Your access has been suspended or has expired. Contact the administrator.")
        if st.button("Logout"):
            logout()
        st.stop()

    role = st.session_state.role

    # Sidebar
    with st.sidebar:
        st.markdown("## 📄 Invoice Pro")
        st.markdown(f"👤 **{st.session_state.user.get('full_name','User')}**")
        st.caption(f"Role: {role.title()}")
        st.divider()

        nav_options = ["📄 Invoice Builder", "🗂️ Invoices", "⚙️ Settings"]
        if role in ("superadmin", "admin"):
            nav_options += ["👥 User Management", "📊 Admin Dashboard"]
        if role == "superadmin":
            nav_options += ["🔐 Super Admin"]

        menu = st.radio("Navigation", nav_options, label_visibility="collapsed")
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()

    if menu == "📄 Invoice Builder":
        from views.invoice_builder import show_invoice_builder
        show_invoice_builder(supabase)
    elif menu == "🗂️ Invoices":
        from views.invoices_list import show_invoices
        show_invoices(supabase)
    elif menu == "⚙️ Settings":
        from views.settings import show_settings
        show_settings(supabase)
    elif menu == "👥 User Management":
        from views.user_management import show_user_management
        show_user_management(supabase)
    elif menu == "📊 Admin Dashboard":
        from views.admin_dashboard import show_admin_dashboard
        show_admin_dashboard(supabase)
    elif menu == "🔐 Super Admin":
        from views.super_admin import show_super_admin
        show_super_admin(supabase)