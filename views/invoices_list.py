import streamlit as st
import json
from utils.db import get_user_invoices, get_all_invoices, get_user_settings
from utils.templates import render_invoice
from utils.pdf_generator import generate_pdf

def show_invoices(supabase):
    st.title("🗂️ Invoices")
    uid = st.session_state.user["id"]
    role = st.session_state.role

    if role in ("superadmin", "admin"):
        invoices = get_all_invoices(supabase)
    else:
        invoices = get_user_invoices(supabase, uid)

    if not invoices:
        st.info("No invoices found.")
        return

    # Search / filter
    search = st.text_input("🔍 Search by client or invoice number")
    status_filter = st.selectbox("Status", ["All", "draft", "sent", "paid"])

    filtered = invoices
    if search:
        filtered = [i for i in filtered if search.lower() in i.get("client_name", "").lower()
                    or search.lower() in i.get("invoice_number", "").lower()]
    if status_filter != "All":
        filtered = [i for i in filtered if i.get("invoice_status", "") == status_filter]

    st.markdown(f"**{len(filtered)}** invoices found")
    st.divider()

    for inv in filtered:
        with st.expander(f"#{inv['invoice_number']} — {inv.get('client_name','N/A')} — ₹{inv.get('grand_total',0):.2f} — {inv.get('invoice_status','draft').upper()}"):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**Client:** {inv.get('client_name')}")
                st.write(f"**Issue Date:** {inv.get('issue_date')}")
                st.write(f"**Due Date:** {inv.get('due_date')}")
            with col2:
                st.write(f"**Subtotal:** ₹{inv.get('subtotal', 0):.2f}")
                st.write(f"**Grand Total:** ₹{inv.get('grand_total', 0):.2f}")
                st.write(f"**Template:** {inv.get('template', 'classic')}")
            with col3:
                new_status = st.selectbox(
                    "Status", ["draft", "sent", "paid"],
                    index=["draft", "sent", "paid"].index(inv.get("invoice_status", "draft")),
                    key=f"st_{inv['id']}"
                )
                if st.button("Update", key=f"upd_{inv['id']}"):
                    supabase.table("invoices").update({"invoice_status": new_status}).eq("id", inv["id"]).execute()
                    st.rerun()

            if st.button("📄 View & Download PDF", key=f"pdf_{inv['id']}"):
                # Parse items
                items = inv.get("items", [])
                if isinstance(items, str):
                    items = json.loads(items)

                # Get user settings for template/branding
                settings = get_user_settings(supabase, inv["user_id"])
                inv_data = {**settings, **inv, "items": items}

                # Show HTML preview
                html = render_invoice(inv.get("template", "classic"), inv_data)
                st.components.v1.html(html, height=800, scrolling=True)

                # Generate and offer PDF download
                pdf_bytes = generate_pdf(inv_data)
                st.download_button(
                    "💾 Download PDF",
                    data=pdf_bytes,
                    file_name=f"{inv['invoice_number']}.pdf",
                    mime="application/pdf",
                    key=f"dl_{inv['id']}"
                )