import base64
from datetime import datetime

def get_logo_html(logo_base64):
    if logo_base64:
        return f'<img src="data:image/png;base64,{logo_base64}" style="max-height:80px;max-width:200px;">'
    return ""

def render_items_rows(items, enabled_cols):
    rows = ""
    for idx, item in enumerate(items):
        amount = item.get("quantity", 0) * item.get("unit_price", 0)
        rows += f"<tr><td style='padding:8px;border:1px solid #ddd;text-align:center;'>{idx+1}</td>"
        for col in enabled_cols:
            if col["key"] == "quantity":
                rows += f"<td style='padding:8px;border:1px solid #ddd;text-align:center;'>{item.get('quantity',0):.2f}</td>"
            elif col["key"] == "unit_price":
                rows += f"<td style='padding:8px;border:1px solid #ddd;text-align:right;'>₹{item.get('unit_price',0):.2f}</td>"
            elif col["key"] == "amount":
                rows += f"<td style='padding:8px;border:1px solid #ddd;text-align:right;'>₹{amount:.2f}</td>"
            else:
                rows += f"<td style='padding:8px;border:1px solid #ddd;'>{item.get(col['key'],'')}</td>"
        rows += f"<td style='padding:8px;border:1px solid #ddd;text-align:right;'>₹{amount:.2f}</td></tr>"
    return rows

# ── TEMPLATE 1: Classic ─────────────────────────────────────────────────────
def classic_template(data):
    logo = get_logo_html(data.get("company_logo_base64",""))
    enabled = [c for c in data.get("custom_columns",[]) if c.get("enabled")]
    header_cells = "".join(f"<th style='padding:10px;background:#1a1a2e;color:white;text-align:left;'>{c['name']}</th>" for c in enabled)
    header_cells += "<th style='padding:10px;background:#1a1a2e;color:white;text-align:right;'>Amount</th>"
    rows = render_items_rows(data.get("items",[]), enabled)
    gst_section = ""
    if data.get("gst_enabled"):
        gst_section = f"""
        <tr><td colspan="4" style="border:none;"></td><td colspan="2" style="padding:6px;text-align:right;border-top:1px solid #eee;">CGST ({data['cgst_percent']}%):</td><td style="padding:6px;text-align:right;border-top:1px solid #eee;">₹{data['cgst_amount']:.2f}</td></tr>
        <tr><td colspan="4" style="border:none;"></td><td colspan="2" style="padding:6px;text-align:right;">SGST ({data['sgst_percent']}%):</td><td style="padding:6px;text-align:right;">₹{data['sgst_amount']:.2f}</td></tr>
        """
    return f"""
    <html>
    <head><style>
    @media print {{
        * {{ -webkit-print-color-adjust: exact !important; 
             print-color-adjust: exact !important; }}
        body {{ margin: 0; }}
    }}
    </style></head>
    <body style="font-family:Arial,sans-serif;margin:0;padding:20px;color:#333;">
    <div class="invoice-wrapper" style="max-width:800px;margin:auto;border:2px solid #1a1a2e;border-radius:8px;overflow:hidden;">
      <div style="background:#1a1a2e;color:white;padding:30px;display:flex;justify-content:space-between;align-items:center;">
        <div>{logo}<h1 style="margin:10px 0 0;font-size:28px;">{data['company_name']}</h1></div>
        <div style="text-align:right;"><h2 style="font-size:32px;margin:0;letter-spacing:3px;">{data['invoice_title']}</h2><p style="margin:5px 0;"># {data['invoice_number']}</p></div>
      </div>
      <div style="display:flex;justify-content:space-between;padding:20px 30px;background:#f8f9ff;">
        <div><strong>Bill To:</strong><br>{data['client_name']}<br><span style="white-space:pre-line;">{data['client_address']}</span></div>
        <div style="text-align:right;"><p><strong>Issue Date:</strong> {data['issue_date']}</p><p><strong>Due Date:</strong> {data['due_date']}</p></div>
      </div>
      <div style="padding:20px 30px;">
        <table style="width:100%;border-collapse:collapse;table-layout:fixed;">
          <thead><tr><th style="padding:10px;background:#1a1a2e;color:white;text-align:center;width:40px;">#</th>{header_cells}</tr></thead>
          <tbody>{rows}</tbody>
          <tfoot>
            <tr><td colspan="{len(enabled)+1}" style="border:none;"></td><td style="padding:8px;text-align:right;font-weight:bold;border-top:2px solid #1a1a2e;">Subtotal:</td><td style="padding:8px;text-align:right;border-top:2px solid #1a1a2e;">₹{data['subtotal']:.2f}</td></tr>
            {gst_section}
            <tr><td colspan="{len(enabled)+1}" style="border:none;"></td><td style="padding:10px;text-align:right;font-weight:bold;font-size:18px;background:#1a1a2e;color:white;">Grand Total:</td><td style="padding:10px;text-align:right;font-weight:bold;font-size:18px;background:#1a1a2e;color:white;">₹{data['grand_total']:.2f}</td></tr>
          </tfoot>
        </table>
      </div>
      <div style="padding:20px 30px;background:#f8f9ff;"><strong>Terms & Conditions</strong><p style="font-size:13px;">{data.get('terms_conditions','')}</p></div>
      <div style="background:#1a1a2e;color:white;padding:15px 30px;text-align:center;font-size:13px;">
        📞 {data.get('phone_number','')} &nbsp;|&nbsp; 🌐 {data.get('website','')} &nbsp;|&nbsp; ✉️ {data.get('email','')}
      </div>
    </div></body></html>"""

# ── TEMPLATE 2: Modern ──────────────────────────────────────────────────────
def modern_template(data):
    logo = get_logo_html(data.get("company_logo_base64",""))
    enabled = [c for c in data.get("custom_columns",[]) if c.get("enabled")]
    header_cells = "".join(f"<th style='padding:12px 15px;text-align:left;color:#666;font-weight:600;border-bottom:2px solid #f0f0f0;'>{c['name']}</th>" for c in enabled)
    header_cells += "<th style='padding:12px 15px;text-align:right;color:#666;font-weight:600;border-bottom:2px solid #f0f0f0;'>Amount</th>"
    rows = ""
    for idx, item in enumerate(data.get("items",[])):
        amount = item.get("quantity",0)*item.get("unit_price",0)
        bg = "#fafafa" if idx%2==0 else "white"
        rows += f"<tr style='background:{bg};'><td style='padding:12px 15px;'>{idx+1}</td>"
        for col in enabled:
            if col["key"] == "quantity":
                rows += f"<td style='padding:12px 15px;text-align:center;'>{item.get('quantity',0):.2f}</td>"
            elif col["key"] == "unit_price":
                rows += f"<td style='padding:12px 15px;text-align:right;'>₹{item.get('unit_price',0):.2f}</td>"
            else:
                rows += f"<td style='padding:12px 15px;'>{item.get(col['key'],'')}</td>"
        rows += f"<td style='padding:12px 15px;text-align:right;font-weight:600;'>₹{amount:.2f}</td></tr>"
    gst_rows = ""
    if data.get("gst_enabled"):
        gst_rows = f"""
        <tr>
          <td colspan="{len(enabled)+1}" style="border:none;"></td>
          <td style="padding:6px 15px;text-align:right;color:#666;border:none;">CGST ({data['cgst_percent']}%)</td>
          <td style="padding:6px 15px;text-align:right;border:none;">₹{data['cgst_amount']:.2f}</td>
        </tr>
        <tr>
          <td colspan="{len(enabled)+1}" style="border:none;"></td>
          <td style="padding:6px 15px;text-align:right;color:#666;border:none;">SGST ({data['sgst_percent']}%)</td>
          <td style="padding:6px 15px;text-align:right;border:none;">₹{data['sgst_amount']:.2f}</td>
        </tr>"""
    return f"""
    <html>
    <head><style>
    @media print {{
        * {{ -webkit-print-color-adjust: exact !important; 
             print-color-adjust: exact !important; }}
        body {{ margin: 0; }}
    }}
    </style></head>
    <body style="font-family:'Segoe UI',sans-serif;margin:0;padding:30px;background:#f5f5f5;">
    <div class="invoice-wrapper" style="max-width:800px;margin:auto;background:white;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.1);">
      <div style="padding:40px;background:linear-gradient(135deg,#667eea,#764ba2);color:white;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
          <div>{logo}<h1 style="margin:15px 0 0;font-size:24px;">{data['company_name']}</h1></div>
          <div style="text-align:right;"><div style="font-size:40px;font-weight:300;letter-spacing:4px;">{data['invoice_title']}</div><div style="font-size:18px;opacity:0.8;">#{data['invoice_number']}</div></div>
        </div>
      </div>
      <div style="padding:30px 40px;display:flex;justify-content:space-between;border-bottom:1px solid #f0f0f0;">
        <div><div style="color:#999;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Bill To</div>
        <div style="font-size:18px;font-weight:600;">{data['client_name']}</div>
        <div style="color:#666;white-space:pre-line;">{data['client_address']}</div></div>
        <div style="text-align:right;">
          <div style="margin-bottom:8px;"><span style="color:#999;font-size:12px;text-transform:uppercase;">Issue Date</span><br><strong>{data['issue_date']}</strong></div>
          <div><span style="color:#999;font-size:12px;text-transform:uppercase;">Due Date</span><br><strong style="color:#e74c3c;">{data['due_date']}</strong></div>
        </div>
      </div>
      <div style="padding:20px 40px;">
        <table style="width:100%;border-collapse:collapse;">
          <thead><tr><th style="padding:12px 15px;text-align:left;color:#666;font-weight:600;border-bottom:2px solid #f0f0f0;">#</th>{header_cells}</tr></thead>
          <tbody>{rows}</tbody>
        </table>

        <div style="margin-top:10px;border-top:1px solid #f0f0f0;padding-top:10px;">
          <div style="display:flex;justify-content:flex-end;padding:6px 0;">
            <span style="color:#666;min-width:120px;text-align:right;padding-right:20px;">Subtotal</span>
            <span style="min-width:100px;text-align:right;">₹{data['subtotal']:.2f}</span>
          </div>
          {gst_rows}
          <div style="display:flex;justify-content:flex-end;margin-top:8px;">
            <div style="display:flex;border-radius:8px;overflow:hidden;">
              <span style="padding:12px 20px;font-size:18px;font-weight:700;background:linear-gradient(135deg,#667eea,#764ba2);color:white;">Total</span>
              <span style="padding:12px 20px;font-size:18px;font-weight:700;background:linear-gradient(135deg,#667eea,#764ba2);color:white;">₹{data['grand_total']:.2f}</span>
            </div>
          </div>
        </div>
      </div>
      <div style="padding:20px 40px;background:#fafafa;"><strong>Terms & Conditions</strong><p style="color:#666;font-size:13px;">{data.get('terms_conditions','')}</p></div>
      <div style="padding:20px 40px;text-align:center;color:#999;font-size:13px;border-top:1px solid #f0f0f0;">
        📞 {data.get('phone_number','')} &nbsp;·&nbsp; 🌐 {data.get('website','')} &nbsp;·&nbsp; ✉️ {data.get('email','')}
      </div>
    </div></body></html>"""

# ── TEMPLATE 3: Minimal ─────────────────────────────────────────────────────
def minimal_template(data):
    logo = get_logo_html(data.get("company_logo_base64",""))
    enabled = [c for c in data.get("custom_columns",[]) if c.get("enabled")]
    header_cells = "".join(f"<th style='padding:10px;text-align:left;border-bottom:1px solid #000;'>{c['name']}</th>" for c in enabled)
    header_cells += "<th style='padding:10px;text-align:right;border-bottom:1px solid #000;'>Amount</th>"
    rows = ""
    for idx, item in enumerate(data.get("items",[])):
        amount = item.get("quantity",0)*item.get("unit_price",0)
        rows += f"<tr><td style='padding:10px;border-bottom:1px solid #eee;'>{idx+1}</td>"
        for col in enabled:
            if col["key"]=="quantity": rows += f"<td style='padding:10px;border-bottom:1px solid #eee;text-align:center;'>{item.get('quantity',0):.2f}</td>"
            elif col["key"]=="unit_price": rows += f"<td style='padding:10px;border-bottom:1px solid #eee;text-align:right;'>₹{item.get('unit_price',0):.2f}</td>"
            else: rows += f"<td style='padding:10px;border-bottom:1px solid #eee;'>{item.get(col['key'],'')}</td>"
        rows += f"<td style='padding:10px;border-bottom:1px solid #eee;text-align:right;'>₹{amount:.2f}</td></tr>"
    gst_rows = ""
    if data.get("gst_enabled"):
        gst_rows = f"<tr><td colspan='{len(enabled)+1}' style='text-align:right;padding:6px;color:#555;'>CGST ({data['cgst_percent']}%): ₹{data['cgst_amount']:.2f}</td></tr><tr><td colspan='{len(enabled)+1}' style='text-align:right;padding:6px;color:#555;'>SGST ({data['sgst_percent']}%): ₹{data['sgst_amount']:.2f}</td></tr>"
    return f"""
    <html>
    <head><style>
    @media print {{
        * {{ -webkit-print-color-adjust: exact !important; 
             print-color-adjust: exact !important; }}
        body {{ margin: 0; }}
    }}
    </style></head>
    <body style="font-family:Georgia,serif;margin:0;padding:40px;color:#222;">
    <div class="invoice-wrapper" style="max-width:780px;margin:auto;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;border-bottom:3px solid #000;padding-bottom:20px;margin-bottom:30px;">
        <div>{logo}<div style="font-size:24px;font-weight:bold;margin-top:10px;">{data['company_name']}</div></div>
        <div style="text-align:right;"><div style="font-size:36px;letter-spacing:5px;font-weight:300;">{data['invoice_title']}</div><div style="font-size:14px;color:#666;">No. {data['invoice_number']}</div></div>
      </div>
      <div style="display:flex;justify-content:space-between;margin-bottom:30px;">
        <div><div style="font-size:11px;text-transform:uppercase;letter-spacing:2px;color:#888;margin-bottom:5px;">BILLED TO</div>
        <div style="font-size:16px;font-weight:bold;">{data['client_name']}</div>
        <div style="color:#555;white-space:pre-line;">{data['client_address']}</div></div>
        <div style="text-align:right;font-size:14px;"><div><span style="color:#888;">Issue Date: </span>{data['issue_date']}</div><div><span style="color:#888;">Due Date: </span>{data['due_date']}</div></div>
      </div>
      <table style="width:100%;border-collapse:collapse;table-layout:fixed;">
        <thead><tr><th style="padding:10px;text-align:left;border-bottom:1px solid #000;">#</th>{header_cells}</tr></thead>
        <tbody>{rows}</tbody>
        <tfoot>
          <tr><td colspan="{len(enabled)+1}" style="padding:8px;text-align:right;color:#555;">Subtotal:</td><td style="padding:8px;text-align:right;">₹{data['subtotal']:.2f}</td></tr>
          {gst_rows}
          <tr style="border-top:2px solid #000;"><td colspan="{len(enabled)+1}" style="padding:12px 8px;text-align:right;font-size:18px;font-weight:bold;">TOTAL:</td><td style="padding:12px 8px;text-align:right;font-size:18px;font-weight:bold;">₹{data['grand_total']:.2f}</td></tr>
        </tfoot>
      </table>
      <div style="border-top:1px solid #ccc;padding-top:15px;margin-bottom:20px;"><strong style="font-size:12px;text-transform:uppercase;letter-spacing:1px;">Terms & Conditions</strong><p style="font-size:13px;color:#555;">{data.get('terms_conditions','')}</p></div>
      <div style="text-align:center;font-size:12px;color:#999;border-top:1px solid #eee;padding-top:15px;">
        {data.get('phone_number','')} &nbsp;|&nbsp; {data.get('website','')} &nbsp;|&nbsp; {data.get('email','')}
      </div>
    </div></body></html>"""

def render_invoice(template_name, data):
    templates = {"classic": classic_template, "modern": modern_template, "minimal": minimal_template}
    fn = templates.get(template_name, classic_template)
    return fn(data)