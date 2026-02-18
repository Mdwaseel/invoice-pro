import streamlit as st
from datetime import date, timedelta

def show_super_admin(supabase):
    st.title("🔐 Super Admin Panel")

    tab1, tab2, tab3 = st.tabs(["📋 Signup Requests", "👥 All Users", "📊 Stats"])

    with tab1:
        st.subheader("Pending Signup Requests")
        try:
            res = supabase.table("signup_requests").select("*").order("created_at", desc=True).execute()
            requests = res.data or []
        except:
            requests = []

        pending = [r for r in requests if r["status"] == "pending"]
        if not pending:
            st.info("No pending requests.")
        else:
            for req in pending:
                with st.expander(f"📩 {req['full_name']} ({req['email']}) — {req.get('created_at','')[:10]}"):
                    st.write(f"**Company:** {req.get('company_name','')}")
                    st.write(f"**Phone:** {req.get('phone','')}")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("✅ Approve", key=f"app_{req['id']}"):
                            # Create profile
                            supabase.table("profiles").insert({
                                "email": req["email"],
                                "full_name": req["full_name"],
                                "company_name": req.get("company_name",""),
                                "phone": req.get("phone",""),
                                "role": "user",
                                "status": "approved",
                                "access_type": "permanent",
                            }).execute()
                            # Get the new profile id
                            p = supabase.table("profiles").select("id").eq("email", req["email"]).single().execute().data
                            # Create default settings
                            supabase.table("user_settings").insert({"user_id": p["id"]}).execute()
                            # Mark request approved
                            supabase.table("signup_requests").update({
                                "status": "approved",
                                "reviewed_by": st.session_state.user["id"],
                                "reviewed_at": str(date.today())
                            }).eq("id", req["id"]).execute()
                            st.success("User approved!")
                            st.rerun()
                    with col2:
                        if st.button("❌ Reject", key=f"rej_{req['id']}"):
                            supabase.table("signup_requests").update({
                                "status": "rejected",
                                "reviewed_by": st.session_state.user["id"],
                                "reviewed_at": str(date.today())
                            }).eq("id", req["id"]).execute()
                            st.rerun()

    with tab2:
        st.subheader("Manage All Users")
        try:
            profiles = supabase.table("profiles").select("*").order("created_at", desc=True).execute().data or []
        except:
            profiles = []

        for p in profiles:
            if p["role"] == "superadmin": continue
            with st.expander(f"👤 {p['full_name']} ({p['email']}) — {p['status'].upper()} — {p.get('role','user')}"):
                col1, col2 = st.columns(2)
                with col1:
                    new_status = st.selectbox("Status", ["approved","suspended","pending"],
                        index=["approved","suspended","pending"].index(p.get("status","pending")),
                        key=f"pst_{p['id']}")
                    new_role = st.selectbox("Role", ["user","admin"],
                        index=["user","admin"].index(p.get("role","user")),
                        key=f"pr_{p['id']}")
                with col2:
                    access_type = st.selectbox("Access Type", ["permanent","monthly"],
                        index=["permanent","monthly"].index(p.get("access_type","permanent") or "permanent"),
                        key=f"at_{p['id']}")
                    months = None
                    if access_type == "monthly":
                        months = st.number_input("Months", min_value=1, max_value=24, value=p.get("access_months") or 1, key=f"am_{p['id']}")

                if st.button("💾 Save Changes", key=f"save_{p['id']}"):
                    update = {"status": new_status, "role": new_role, "access_type": access_type}
                    if access_type == "monthly" and months:
                        update["access_months"] = months
                        update["access_start_date"] = str(date.today())
                        update["access_end_date"] = str(date.today() + timedelta(days=30*months))
                    supabase.table("profiles").update(update).eq("id", p["id"]).execute()
                    st.success("Updated!")
                    st.rerun()

    with tab3:
        st.subheader("Platform Statistics")
        try:
            total_users = len(supabase.table("profiles").select("id").execute().data or [])
            total_invoices = len(supabase.table("invoices").select("id").execute().data or [])
            pending_req = len(supabase.table("signup_requests").select("id").eq("status","pending").execute().data or [])
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Users", total_users)
            col2.metric("Total Invoices", total_invoices)
            col3.metric("Pending Requests", pending_req)
        except:
            st.error("Could not load stats.")