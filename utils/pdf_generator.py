from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from io import BytesIO
import base64

def generate_pdf(invoice_data: dict) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=15*mm, leftMargin=15*mm,
                            topMargin=15*mm, bottomMargin=15*mm)

    styles = getSampleStyleSheet()
    elements = []

    # Colors based on template
    template = invoice_data.get("invoice_template", "classic")
    if template == "modern":
        primary = colors.HexColor("#667eea")
    elif template == "minimal":
        primary = colors.black
    else:
        primary = colors.HexColor("#1a1a2e")

    # Header
    header_data = [[
        Paragraph(f"<b>{invoice_data.get('company_name','')}</b>", ParagraphStyle('co', fontSize=16, textColor=colors.white)),
        Paragraph(f"<b>{invoice_data.get('invoice_title','INVOICE')}</b><br/># {invoice_data.get('invoice_number','')}", 
                  ParagraphStyle('inv', fontSize=14, textColor=colors.white, alignment=TA_RIGHT))
    ]]
    header_table = Table(header_data, colWidths=[90*mm, 90*mm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), primary),
        ('PADDING', (0,0), (-1,-1), 12),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 5*mm))

    # Bill To + Invoice Details
    bill_style = ParagraphStyle('bill', fontSize=9)
    info_data = [[
        Paragraph(f"<b>Bill To:</b><br/>{invoice_data.get('client_name','')}<br/>{invoice_data.get('client_address','').replace(chr(10),'<br/>')}", bill_style),
        Paragraph(f"<b>Issue Date:</b> {invoice_data.get('issue_date','')}<br/><b>Due Date:</b> {invoice_data.get('due_date','')}", 
                  ParagraphStyle('info', fontSize=9, alignment=TA_RIGHT))
    ]]
    info_table = Table(info_data, colWidths=[90*mm, 90*mm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8f9ff")),
        ('PADDING', (0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 5*mm))

    # Items Table
    enabled_cols = [c for c in invoice_data.get("custom_columns", []) if c.get("enabled")]
    col_names = ["#"] + [c["name"] for c in enabled_cols] + ["Amount"]
    items_data = [col_names]

    for idx, item in enumerate(invoice_data.get("items", [])):
        amount = float(item.get("quantity", 0)) * float(item.get("unit_price", 0))
        row = [str(idx + 1)]
        for col in enabled_cols:
            key = col["key"]
            if key == "quantity":
                row.append(f"{float(item.get(key,0)):.2f}")
            elif key == "unit_price":
                row.append(f"Rs.{float(item.get(key,0)):.2f}")
            else:
                row.append(str(item.get(key, "")))
        row.append(f"Rs.{amount:.2f}")
        items_data.append(row)

    num_cols = len(col_names)
    col_widths = [10*mm] + [40*mm if c["key"]=="description" else 25*mm for c in enabled_cols] + [25*mm]

    items_table = Table(items_data, colWidths=col_widths, repeatRows=1)
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('PADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f9f9f9")]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#dddddd")),
        ('ALIGN', (-1,0), (-1,-1), 'RIGHT'),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 5*mm))

    # Totals
    subtotal = invoice_data.get("subtotal", 0)
    cgst = invoice_data.get("cgst_amount", 0)
    sgst = invoice_data.get("sgst_amount", 0)
    grand = invoice_data.get("grand_total", 0)
    gst_on = invoice_data.get("gst_enabled", False)

    totals = [[" ", f"Subtotal:", f"Rs.{subtotal:.2f}"]]
    if gst_on:
        totals.append([" ", f"CGST ({invoice_data.get('cgst_percent',9)}%):", f"Rs.{cgst:.2f}"])
        totals.append([" ", f"SGST ({invoice_data.get('sgst_percent',9)}%):", f"Rs.{sgst:.2f}"])
    totals.append([" ", "GRAND TOTAL:", f"Rs.{grand:.2f}"])

    totals_table = Table(totals, colWidths=[110*mm, 40*mm, 30*mm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('BACKGROUND', (0,-1), (-1,-1), primary),
        ('TEXTCOLOR', (0,-1), (-1,-1), colors.white),
        ('PADDING', (0,0), (-1,-1), 6),
        ('LINEABOVE', (0,-1), (-1,-1), 1, primary),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 5*mm))

    # Terms
    terms = invoice_data.get("terms_conditions", "")
    if terms:
        elements.append(Paragraph("<b>Terms & Conditions</b>", ParagraphStyle('tc', fontSize=9)))
        elements.append(Paragraph(terms, ParagraphStyle('tcb', fontSize=8, textColor=colors.grey)))
        elements.append(Spacer(1, 5*mm))

    # Footer
    footer_text = f"{invoice_data.get('phone_number','')}  |  {invoice_data.get('website','')}  |  {invoice_data.get('email','')}"
    footer = Table([[Paragraph(footer_text, ParagraphStyle('ft', fontSize=8, alignment=TA_CENTER, textColor=colors.white))]],
                   colWidths=[180*mm])
    footer.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), primary),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    elements.append(footer)

    doc.build(elements)
    return buffer.getvalue()