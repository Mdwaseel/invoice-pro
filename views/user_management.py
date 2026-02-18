import streamlit as st

def show_user_management(supabase):
    st.title("👥 User Management")
    try:
        profiles = supabase.table("profiles").select("*").execute().data or []
        for p in profiles:
            with st.expander(f"{p['full_name']} ({p['email']}) — {p['status']}"):
                st.write(f"Role: {p['role']}, Access: {p.get('access_type','permanent')}")
                if p.get('access_end_date'):
                    st.write(f"Access until: {p['access_end_date']}")
    except Exception as e:
        st.error(f"Error loading users: {e}")