import streamlit as st

def show_admin_dashboard(supabase):
    st.title("📊 Admin Dashboard")
    try:
        invoices = supabase.table("invoices").select("*,profiles(full_name)").execute().data or []
        total_rev = sum(float(i.get("grand_total",0)) for i in invoices)
        paid = [i for i in invoices if i.get("invoice_status")=="paid"]
        draft = [i for i in invoices if i.get("invoice_status")=="draft"]

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Total Invoices", len(invoices))
        c2.metric("Total Revenue", f"₹{total_rev:,.2f}")
        c3.metric("Paid", len(paid))
        c4.metric("Draft", len(draft))

        st.subheader("Recent Invoices")
        for inv in invoices[:20]:
            st.write(f"**{inv['invoice_number']}** | {inv.get('client_name','N/A')} | ₹{inv.get('grand_total',0):.2f} | {inv.get('invoice_status','')}")
    except Exception as e:
        st.error(f"Error: {e}")