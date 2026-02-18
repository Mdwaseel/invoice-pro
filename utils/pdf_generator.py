from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from io import BytesIO

def generate_pdf(invoice_data: dict) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=15*mm, leftMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm
    )
    elements = []

    # Color based on template
    template = invoice_data.get("invoice_template", "classic")
    if template == "modern":
        primary = colors.HexColor("#667eea")
    elif template == "minimal":
        primary = colors.black
    else:
        primary = colors.HexColor("#1a1a2e")

    white = colors.white
    light_bg = colors.HexColor("#f8f9ff")

    def style(name, **kwargs):
        return ParagraphStyle(name, **kwargs)

    # ── HEADER ──────────────────────────────────────────
    header_data = [[
        Paragraph(
            f"<b>{invoice_data.get('company_name','')}</b>",
            style('co', fontSize=18, textColor=white)
        ),
        Paragraph(
            f"<b>{invoice_data.get('invoice_title','INVOICE')}</b><br/>"
            f"<font size=11>#{invoice_data.get('invoice_number','')}</font>",
            style('inv', fontSize=20, textColor=white, alignment=TA_RIGHT)
        )
    ]]
    ht = Table(header_data, colWidths=[95*mm, 85*mm])
    ht.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), primary),
        ('PADDING', (0,0), (-1,-1), 14),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROUNDEDCORNERS', [4, 4, 0, 0]),
    ]))
    elements.append(ht)

    # ── BILL TO + DATES ──────────────────────────────────
    addr = invoice_data.get('client_address', '').replace('\n', '<br/>')
    info_data = [[
        Paragraph(
            f"<b>Bill To:</b><br/>"
            f"<font size=11><b>{invoice_data.get('client_name','')}</b></font><br/>"
            f"<font size=9>{addr}</font>",
            style('bill', fontSize=9, leading=14)
        ),
        Paragraph(
            f"<b>Issue Date:</b> {invoice_data.get('issue_date','')}<br/><br/>"
            f"<b>Due Date:</b> {invoice_data.get('due_date','')}",
            style('dates', fontSize=9, alignment=TA_RIGHT, leading=16)
        )
    ]]
    it = Table(info_data, colWidths=[95*mm, 85*mm])
    it.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), light_bg),
        ('PADDING', (0,0), (-1,-1), 12),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elements.append(it)
    elements.append(Spacer(1, 6*mm))

    # ── ITEMS TABLE ───────────────────────────────────────
    enabled_cols = [c for c in invoice_data.get("custom_columns", []) if c.get("enabled")]
    col_names = ["#"] + [c["name"] for c in enabled_cols] + ["Amount"]

    header_row = [
        Paragraph(f"<b>{n}</b>", style(f'h{i}', fontSize=8, textColor=white))
        for i, n in enumerate(col_names)
    ]
    items_data = [header_row]

    for idx, item in enumerate(invoice_data.get("items", [])):
        amount = float(item.get("quantity", 0)) * float(item.get("unit_price", 0))
        row = [Paragraph(str(idx + 1), style(f'r{idx}0', fontSize=8))]
        for col in enabled_cols:
            key = col["key"]
            if key == "quantity":
                val = f"{float(item.get(key, 0)):.2f}"
            elif key == "unit_price":
                val = f"\u20b9{float(item.get(key, 0)):.2f}"
            else:
                val = str(item.get(key, ""))
            row.append(Paragraph(val, style(f'r{idx}{key}', fontSize=8)))
        row.append(Paragraph(f"\u20b9{amount:.2f}", style(f'r{idx}amt', fontSize=8, alignment=TA_RIGHT)))
        items_data.append(row)

    # Column widths
    desc_w = 45*mm
    other_w = 25*mm
    num_w = 10*mm
    amt_w = 25*mm
    col_widths = [num_w] + [desc_w if c["key"] == "description" else other_w for c in enabled_cols] + [amt_w]

    tbl = Table(items_data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('PADDING', (0, 0), (-1, -1), 7),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, colors.HexColor("#f5f5f5")]),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
        ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(tbl)
    elements.append(Spacer(1, 5*mm))

    # ── TOTALS ────────────────────────────────────────────
    subtotal = float(invoice_data.get("subtotal", 0))
    cgst = float(invoice_data.get("cgst_amount", 0))
    sgst = float(invoice_data.get("sgst_amount", 0))
    grand = float(invoice_data.get("grand_total", 0))
    gst_on = invoice_data.get("gst_enabled", False)

    right = style('right', fontSize=9, alignment=TA_RIGHT)
    bold_right = style('bright', fontSize=11, alignment=TA_RIGHT)

    totals_data = [[
        Paragraph("Subtotal:", right),
        Paragraph(f"\u20b9{subtotal:.2f}", right)
    ]]
    if gst_on:
        totals_data.append([
            Paragraph(f"CGST ({invoice_data.get('cgst_percent', 9)}%):", right),
            Paragraph(f"\u20b9{cgst:.2f}", right)
        ])
        totals_data.append([
            Paragraph(f"SGST ({invoice_data.get('sgst_percent', 9)}%):", right),
            Paragraph(f"\u20b9{sgst:.2f}", right)
        ])
    totals_data.append([
        Paragraph("<b>Grand Total:</b>", style('gt', fontSize=11, alignment=TA_RIGHT, textColor=white)),
        Paragraph(f"<b>\u20b9{grand:.2f}</b>", style('gtv', fontSize=11, alignment=TA_RIGHT, textColor=white))
    ])

    total_table = Table(totals_data, colWidths=[150*mm, 30*mm])
    last = len(totals_data) - 1
    total_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, last), (-1, last), primary),
        ('ROWBACKGROUNDS', (0, 0), (-1, last-1), [light_bg, white]),
        ('LINEABOVE', (0, last), (-1, last), 1, primary),
    ]))
    elements.append(total_table)
    elements.append(Spacer(1, 6*mm))

    # ── TERMS ─────────────────────────────────────────────
    terms = invoice_data.get("terms_conditions", "")
    if terms:
        elements.append(Paragraph(
            "<b>Terms & Conditions</b>",
            style('tct', fontSize=9, textColor=colors.HexColor("#333333"))
        ))
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph(
            terms,
            style('tcb', fontSize=8, textColor=colors.grey, leading=12)
        ))
        elements.append(Spacer(1, 5*mm))

    # ── FOOTER ────────────────────────────────────────────
    phone = invoice_data.get('phone_number', '')
    website = invoice_data.get('website', '')
    email = invoice_data.get('email', '')
    footer_text = f"{phone}   |   {website}   |   {email}"

    footer = Table(
        [[Paragraph(footer_text, style('ft', fontSize=8, alignment=TA_CENTER, textColor=white))]],
        colWidths=[180*mm]
    )
    footer.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), primary),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(footer)

    doc.build(elements)
    return buffer.getvalue()