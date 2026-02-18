import streamlit as st
import bcrypt

def show_auth(supabase):
    st.markdown("# 📄 Invoice Pro")
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Request Access"])

    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted:
            if not email or not password:
                st.error("Please enter email and password.")
                return
            try:
                res = supabase.table("profiles").select("*").eq("email", email).single().execute()
                profile = res.data
            except:
                st.error("Invalid email or password.")
                return

            if not profile:
                st.error("Invalid email or password.")
                return

            # Verify password
            try:
                pwd_res = supabase.table("signup_requests").select("raw_password").eq("email", email).single().execute()
                hashed = pwd_res.data.get("raw_password","") if pwd_res.data else ""
            except:
                hashed = ""

            if not hashed or not bcrypt.checkpw(password.encode(), hashed.encode()):
                st.error("Invalid email or password.")
                return

            if profile["status"] != "approved":
                st.warning("Your account is pending approval or has been suspended.")
                return

            st.session_state.user = profile
            st.session_state.role = profile["role"]
            st.rerun()

    with tab2:
        st.info("Fill in your details below. A Super Admin will review and approve your account.")
        with st.form("signup_form"):
            full_name = st.text_input("Full Name *")
            email_s = st.text_input("Email *")
            company = st.text_input("Company Name")
            phone = st.text_input("Phone")
            pwd = st.text_input("Password *", type="password")
            pwd2 = st.text_input("Confirm Password *", type="password")
            sub = st.form_submit_button("Submit Request", use_container_width=True)

        if sub:
            if not full_name or not email_s or not pwd:
                st.error("Full name, email and password are required.")
                return
            if pwd != pwd2:
                st.error("Passwords do not match.")
                return
            hashed_pwd = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
            try:
                supabase.table("signup_requests").insert({
                    "email": email_s, "full_name": full_name,
                    "company_name": company, "phone": phone,
                    "raw_password": hashed_pwd, "status": "pending"
                }).execute()
                st.success("✅ Request submitted! You'll be notified once a Super Admin approves your account.")
            except Exception as e:
                if "duplicate" in str(e).lower():
                    st.warning("A request with this email already exists.")
                else:
                    st.error(f"Error: {e}")