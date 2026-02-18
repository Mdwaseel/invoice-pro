import streamlit as st
import base64
import json
from utils.db import get_user_settings, save_user_settings

def show_settings(supabase):
    st.title("⚙️ Settings")
    uid = st.session_state.user["id"]
    s = get_user_settings(supabase, uid)

    st.subheader("🏢 Company / Header")
    col1, col2 = st.columns(2)
    with col1:
        s["company_name"] = st.text_input("Company Name", value=s.get("company_name",""))
        s["invoice_title"] = st.text_input("Invoice Title", value=s.get("invoice_title","INVOICE"))
        s["invoice_prefix"] = st.text_input("Invoice Prefix", value=s.get("invoice_prefix","INV-"))
    with col2:
        uploaded = st.file_uploader("Company Logo", type=["png","jpg","jpeg"])
        if uploaded:
            s["company_logo_base64"] = base64.b64encode(uploaded.read()).decode()
        if s.get("company_logo_base64"):
            st.image(f"data:image/png;base64,{s['company_logo_base64']}", width=150)

    st.subheader("📞 Footer / Contact")
    col1, col2, col3 = st.columns(3)
    with col1: s["phone_number"] = st.text_input("Phone Number", value=s.get("phone_number",""))
    with col2: s["website"] = st.text_input("Website", value=s.get("website",""))
    with col3: s["email"] = st.text_input("Email", value=s.get("email",""))

    st.subheader("🧾 Invoice Template")
    s["invoice_template"] = st.radio("Choose Template", ["classic","modern","minimal"],
        index=["classic","modern","minimal"].index(s.get("invoice_template","classic")),
        horizontal=True)

    st.subheader("💰 GST Configuration")
    col1, col2, col3 = st.columns(3)
    with col1: s["gst_enabled"] = st.checkbox("Enable GST", value=s.get("gst_enabled", False))
    with col2: s["cgst_percent"] = st.number_input("CGST %", value=float(s.get("cgst_percent",9.0)), min_value=0.0, max_value=100.0, step=0.1)
    with col3: s["sgst_percent"] = st.number_input("SGST %", value=float(s.get("sgst_percent",9.0)), min_value=0.0, max_value=100.0, step=0.1)

    st.subheader("📋 Terms & Conditions")
    s["terms_conditions"] = st.text_area("Terms & Conditions", value=s.get("terms_conditions",""), height=100)

    st.subheader("🗂️ Invoice Columns")
    st.caption("Enable/disable columns and rename them. You can also add custom columns.")
    cols_data = s.get("custom_columns", [])
    if not isinstance(cols_data, list): cols_data = []
    updated_cols = []
    for i, col in enumerate(cols_data):
        c1, c2, c3 = st.columns([1,3,1])
        with c1: enabled = st.checkbox("On", value=col.get("enabled",True), key=f"col_en_{i}")
        with c2: name = st.text_input("Column Name", value=col.get("name",""), key=f"col_nm_{i}", label_visibility="collapsed")
        with c3:
            if st.button("🗑️", key=f"del_col_{i}"):
                continue
        updated_cols.append({"key": col["key"], "name": name, "enabled": enabled})
    s["custom_columns"] = updated_cols

    c1, c2, c3 = st.columns(3)
    with c1: new_col_name = st.text_input("New Column Name", key="new_col_name")
    with c2:
        if st.button("➕ Add Column") and new_col_name:
            key = new_col_name.lower().replace(" ","_")
            s["custom_columns"].append({"key": key, "name": new_col_name, "enabled": True})
            st.rerun()

    if st.button("💾 Save All Settings", type="primary", use_container_width=True):
        save_user_settings(supabase, uid, s)
        st.success("✅ Settings saved permanently!")
        st.session_state["user_settings"] = s