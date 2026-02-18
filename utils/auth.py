import streamlit as st
from datetime import datetime, date
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def logout():
    st.session_state.user = None
    st.session_state.role = None
    st.session_state.clear()

def check_access(supabase, user_id: str) -> bool:
    """Check if user account is active and access hasn't expired."""
    try:
        res = supabase.table("profiles").select("status,access_type,access_end_date").eq("id", user_id).single().execute()
        profile = res.data
        if not profile:
            return False
        if profile["status"] != "approved":
            return False
        if profile["access_type"] == "monthly" and profile["access_end_date"]:
            end_date = datetime.strptime(profile["access_end_date"], "%Y-%m-%d").date()
            if date.today() > end_date:
                return False
        return True
    except:
        return False