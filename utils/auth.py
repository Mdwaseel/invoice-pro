import streamlit as st
import bcrypt
import extra_streamlit_components as stx
from datetime import datetime, date

@st.cache_resource
def get_cookie_manager():
    return stx.CookieManager(key="cookie_manager")

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def logout():
    try:
        cm = get_cookie_manager()
        cm.delete("user_id", key="logout_uid")
        cm.delete("user_role", key="logout_role")
    except:
        pass
    st.session_state.clear()

def check_access(supabase, user_id: str) -> bool:
    try:
        res = supabase.table("profiles").select(
            "status,access_type,access_end_date"
        ).eq("id", user_id).single().execute()
        profile = res.data
        if not profile:
            return False
        if profile["status"] != "approved":
            return False
        if profile["access_type"] == "monthly" and profile.get("access_end_date"):
            end_date = datetime.strptime(profile["access_end_date"], "%Y-%m-%d").date()
            if date.today() > end_date:
                return False
        return True
    except:
        return False

def restore_session(supabase):
    """Try to restore session from cookies on page refresh."""
    if st.session_state.get("user"):
        return True  # Already logged in
    try:
        cm = get_cookie_manager()
        user_id = cm.get("user_id")
        if user_id:
            res = supabase.table("profiles").select("*").eq(
                "id", user_id
            ).single().execute()
            if res.data and res.data["status"] == "approved":
                st.session_state.user = res.data
                st.session_state.role = res.data["role"]
                return True
    except:
        pass
    return False

def save_session_cookie(user_id: str, role: str):
    """Save session to cookies after login."""
    try:
        cm = get_cookie_manager()
        cm.set("user_id", user_id, key="save_uid")
        cm.set("user_role", role, key="save_role")
    except:
        pass