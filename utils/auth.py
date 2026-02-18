import streamlit as st
import bcrypt
from datetime import datetime, date

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def logout():
    st.session_state.clear()
    st.query_params.clear()

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
    """Try to restore session from query params on page refresh."""
    if st.session_state.get("user"):
        return True  # Already logged in

    try:
        user_id = st.query_params.get("uid")
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

def save_session(user_id: str):
    """Save user_id to query params to persist across refresh."""
    st.query_params["uid"] = user_id
