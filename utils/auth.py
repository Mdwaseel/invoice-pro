import streamlit as st
import bcrypt
import extra_streamlit_components as stx
from datetime import datetime, date
import json

def get_cookie_manager():
    return stx.CookieManager(key="invoice_pro_cookies")

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def logout():
    cookie_manager = get_cookie_manager()
    try:
        cookie_manager.delete("user_id")
        cookie_manager.delete("user_role")
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
    cookie_manager = get_cookie_manager()
    
    if st.session_state.get("user"):
        return True  # Already logged in

    try:
        user_id = cookie_manager.get("user_id")
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
    cookie_manager = get_cookie_manager()
    try:
        cookie_manager.set("user_id", user_id, key="set_uid")
        cookie_manager.set("user_role", role, key="set_role")
    except:
        pass