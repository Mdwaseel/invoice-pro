import streamlit as st
from datetime import datetime, timedelta
from io import BytesIO
import json
from utils.db import get_user_settings, save_user_settings, save_invoice, get_next_invoice_number, increment_invoice_counter
from utils.templates import render_invoice

def show_invoice_builder(supabase):
    st.title("📄 Invoice Builder")
    uid = st.session_state.user["id"]

    # Load settings
    if "user_settings" not in st.session_state:
        st.session_state.user_settings = get_user_settings(supabase, uid)
    s = st.session_state.user_settings

    # Item state - renamed to avoid conflict with st.session_state.items method
    if "invoice_items" not in st.session_state:
        st.session_state.invoice_items = []

    # Invoice details
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Bill To")
        client_name = st.text_input("Client Name", key="client_name")
        client_address = st.text_area("Client Address", key="client_address", height=80)
        client_email = st.text_input("Client Email", key="client_email")
        client_phone = st.text_input("Client Phone", key="client_phone")
    with col2:
        st.subheader("Invoice Details")
        issue_date = st.date_input("Issue Date", value=datetime.now().date())
        due_date = st.date_input("Due Date", value=(datetime.now() + timedelta(days=30)).date())
        invoice_number = get_next_invoice_number(supabase, uid, s)
        st.info(f"Invoice #: **{invoice_number}**")

    # Items table
    st.subheader("Line Items")
    enabled_cols = [c for c in s.get("custom_columns", []) if c.get("enabled")]

    # Header row
    col_widths = [0.5] + [2 if c["key"] == "description" else 1.5 for c in enabled_cols] + [0.5]
    header = st.columns(col_widths)
    header[0].markdown("**#**")
    for i, col in enumerate(enabled_cols):
        header[i + 1].markdown(f"**{col['name']}**")
    header[-1].markdown("")

    items_to_remove = []
    for idx, item in enumerate(st.session_state.invoice_items):
        cols = st.columns(col_widths)
        cols[0].write(f"{idx + 1}")
        for i, col in enumerate(enabled_cols):
            key = col["key"]
            if key == "quantity":
                val = cols[i + 1].number_input(
                    "", value=float(item.get(key, 1.0)),
                    min_value=0.0, step=1.0,
                    key=f"{key}_{idx}",
                    label_visibility="collapsed"
                )
            elif key == "unit_price":
                val = cols[i + 1].number_input(
                    "", value=float(item.get(key, 0.0)),
                    min_value=0.0, step=1.0,
                    key=f"{key}_{idx}",
                    label_visibility="collapsed"
                )
            else:
                val = cols[i + 1].text_input(
                    "", value=item.get(key, ""),
                    key=f"{key}_{idx}",
                    label_visibility="collapsed"
                )
            st.session_state.invoice_items[idx][key] = val

        if cols[-1].button("✕", key=f"rm_{idx}"):
            items_to_remove.append(idx)

    for idx in sorted(items_to_remove, reverse=True):
        st.session_state.invoice_items.pop(idx)
    if items_to_remove:
        st.rerun()

    if st.button("➕ Add Item"):
        new_item = {
            c["key"]: (1.0 if c["key"] == "quantity" else (0.0 if c["key"] == "unit_price" else ""))
            for c in enabled_cols
        }
        st.session_state.invoice_items.append(new_item)
        st.rerun()

    # Totals
    subtotal = sum(
        float(i.get("quantity", 0)) * float(i.get("unit_price", 0))
        for i in st.session_state.invoice_items
    )
    gst_on = s.get("gst_enabled", False)
    cgst_pct = float(s.get("cgst_percent", 9.0))
    sgst_pct = float(s.get("sgst_percent", 9.0))
    cgst_amt = (subtotal * cgst_pct / 100) if gst_on else 0
    sgst_amt = (subtotal * sgst_pct / 100) if gst_on else 0
    grand_total = subtotal + cgst_amt + sgst_amt

    col1, col2 = st.columns([2, 1])
    with col2:
        st.metric("Subtotal", f"₹{subtotal:.2f}")
        if gst_on:
            st.metric(f"CGST ({cgst_pct}%)", f"₹{cgst_amt:.2f}")
            st.metric(f"SGST ({sgst_pct}%)", f"₹{sgst_amt:.2f}")
        st.metric("Grand Total", f"₹{grand_total:.2f}")

    # Build invoice data
    invoice_data = {
        **s,
        "invoice_number": invoice_number,
        "client_name": client_name,
        "client_address": client_address,
        "client_email": client_email,
        "client_phone": client_phone,
        "issue_date": str(issue_date),
        "due_date": str(due_date),
        "items": st.session_state.invoice_items,
        "subtotal": subtotal,
        "cgst_amount": cgst_amt,
        "sgst_amount": sgst_amt,
        "grand_total": grand_total,
        "cgst_percent": cgst_pct,
        "sgst_percent": sgst_pct,
    }

    # Preview
    st.subheader("📋 Preview")
    template_name = s.get("invoice_template", "classic")
    html = render_invoice(template_name, invoice_data)
    st.components.v1.html(html, height=1100, scrolling=True)

    # Actions
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("💾 Save Invoice", type="primary", use_container_width=True):
            record = {
                "user_id": uid,
                "invoice_number": invoice_number,
                "client_name": client_name,
                "client_address": client_address,
                "client_email": client_email,
                "client_phone": client_phone,
                "issue_date": str(issue_date),
                "due_date": str(due_date),
                "items": json.dumps(st.session_state.invoice_items),
                "subtotal": subtotal,
                "cgst_amount": cgst_amt,
                "sgst_amount": sgst_amt,
                "grand_total": grand_total,
                "gst_enabled": gst_on,
                "cgst_percent": cgst_pct,
                "sgst_percent": sgst_pct,
                "terms_conditions": s.get("terms_conditions", ""),
                "template": template_name,
                "invoice_status": "draft",
            }
            save_invoice(supabase, record)
            increment_invoice_counter(supabase, uid, int(s.get("invoice_counter", 1)))
            st.session_state.user_settings = get_user_settings(supabase, uid)
            st.success(f"✅ Invoice {invoice_number} saved!")
            st.session_state.invoice_items = []
            st.rerun()

    with c2:
        if st.button("📥 Download PDF", use_container_width=True):
            from utils.pdf_generator import generate_pdf
            pdf_bytes = generate_pdf(html)
            st.download_button(
                "💾 Save PDF",
                data=pdf_bytes,
                file_name=f"{invoice_number}.pdf",
                mime="application/pdf"
            )