import streamlit as st
import json

DEFAULT_COLUMNS = [
    {"key": "description", "name": "Description", "enabled": True},
    {"key": "serial_no", "name": "Part Serial No", "enabled": True},
    {"key": "quantity", "name": "Quantity", "enabled": True},
    {"key": "unit_price", "name": "Unit Price (₹)", "enabled": True},
]

DEFAULT_SETTINGS = {
    "company_name": "Your Company Name",
    "invoice_title": "INVOICE",
    "invoice_prefix": "INV-",
    "phone_number": "",
    "website": "",
    "email": "",
    "company_logo_base64": None,
    "gst_enabled": False,
    "cgst_percent": 9.0,
    "sgst_percent": 9.0,
    "terms_conditions": "Warranty will be valid only if the bill is present.",
    "invoice_template": "classic",
    "invoice_counter": 1,
    "custom_columns": DEFAULT_COLUMNS,
}

def get_user_settings(supabase, user_id: str) -> dict:
    """Fetch user settings from Supabase, create defaults if not found."""
    try:
        res = supabase.table("user_settings").select("*").eq("user_id", user_id).single().execute()
        if res.data:
            s = res.data
            if isinstance(s.get("custom_columns"), str):
                s["custom_columns"] = json.loads(s["custom_columns"])
            if s.get("custom_columns") is None:
                s["custom_columns"] = DEFAULT_COLUMNS
            return s
    except:
        pass
    # Create defaults
    defaults = {**DEFAULT_SETTINGS, "user_id": user_id}
    try:
        supabase.table("user_settings").insert(defaults).execute()
    except:
        pass
    return defaults

def save_user_settings(supabase, user_id: str, settings: dict):
    """Upsert user settings."""
    settings["user_id"] = user_id
    supabase.table("user_settings").upsert(settings, on_conflict="user_id").execute()

def save_invoice(supabase, invoice_data: dict):
    """Save invoice to DB."""
    return supabase.table("invoices").insert(invoice_data).execute()

def get_user_invoices(supabase, user_id: str):
    return supabase.table("invoices").select("*").eq("user_id", user_id).order("created_at", desc=True).execute().data or []

def get_all_invoices(supabase):
    return supabase.table("invoices").select("*, profiles(full_name, company_name)").order("created_at", desc=True).execute().data or []

def get_next_invoice_number(supabase, user_id: str, settings: dict) -> str:
    counter = settings.get("invoice_counter", 1)
    prefix = settings.get("invoice_prefix", "INV-")
    return f"{prefix}{counter:04d}"

def increment_invoice_counter(supabase, user_id: str, current_count: int):
    supabase.table("user_settings").update({"invoice_counter": current_count + 1}).eq("user_id", user_id).execute()