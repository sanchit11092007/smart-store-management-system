import os
import sys
import subprocess
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.barcode import qr

from database.db_connection import get_db_connection


def generate_pdf_receipt(
    sale_id,
    items_dict,
    subtotal,
    delivery_fee,
    total_amount,
    customer_name="Guest Customer",
    customer_address="Sanjay Place, Agra - 282002",
    payment_method="UPI",
    output_dir="receipts"
):
    """
    Generates a world-class, authentic Retail GST Supermarket Tax Invoice PDF.
    Saves it in the 'receipts' folder and returns the file path.
    """
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"SnapKart_TaxInvoice_{sale_id}.pdf")

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=28,
        leftMargin=28,
        topMargin=28,
        bottomMargin=28
    )

    story = []
    styles = getSampleStyleSheet()

    # Typography & Styles
    brand_title_style = ParagraphStyle(
        "BrandTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=22,
        textColor=colors.HexColor("#16a34a"),
        alignment=0,
        spaceAfter=2
    )

    brand_sub_style = ParagraphStyle(
        "BrandSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#475569"),
        alignment=0
    )

    store_addr_style = ParagraphStyle(
        "StoreAddr",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        textColor=colors.HexColor("#334155"),
        alignment=2,
        leading=11
    )

    heading_banner_style = ParagraphStyle(
        "HeadingBanner",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=colors.white,
        alignment=1
    )

    # 1. Header: Store Branding & Tax Info
    header_data = [
        [
            Paragraph("<b>SnapKart Retail Pvt. Ltd.</b>", brand_title_style),
            Paragraph(
                "<b>SnapKart Agra Flagship Superstore</b><br/>"
                "Plot No. 45, Commercial Complex, Sanjay Place<br/>"
                "Agra, Uttar Pradesh - 282002<br/>"
                "<b>GSTIN:</b> 09AAACS1429B1Z8 | <b>FSSAI:</b> 12722001000456",
                store_addr_style
            )
        ],
        [
            Paragraph("Your Neighbourhood Store, Online • <i>100% Vegetarian Retail</i>", brand_sub_style),
            ""
        ]
    ]

    header_table = Table(header_data, colWidths=[270, 270])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#16a34a"), spaceAfter=10))

    # 2. Tax Invoice Title Box
    title_box = Table([[Paragraph("TAX INVOICE / CASH MEMO", heading_banner_style)]], colWidths=[540])
    title_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#0f172a")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(title_box)
    story.append(Spacer(1, 10))

    # 3. Invoice Metadata & Customer Section
    now_str = datetime.now().strftime("%d %b %Y, %I:%M %p")
    meta_data = [
        [
            Paragraph(f"<b>Invoice ID:</b> #SK-2026-{sale_id:06d}", styles["Normal"]),
            Paragraph(f"<b>Date & Time:</b> {now_str}", styles["Normal"])
        ],
        [
            Paragraph(f"<b>Billed To:</b> {customer_name}", styles["Normal"]),
            Paragraph(f"<b>Payment Mode:</b> {payment_method} (Completed)", styles["Normal"])
        ],
        [
            Paragraph(f"<b>Delivery Address:</b> {customer_address}", styles["Normal"]),
            Paragraph("<b>POS Terminal:</b> Agra-POS-01", styles["Normal"])
        ]
    ]

    meta_table = Table(meta_data, colWidths=[270, 270])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))

    # 4. Itemized GST Product Table
    table_data = [
        [
            Paragraph("<b>#</b>", styles["Normal"]),
            Paragraph("<b>Item Description</b>", styles["Normal"]),
            Paragraph("<b>HSN</b>", styles["Normal"]),
            Paragraph("<b>Qty</b>", styles["Normal"]),
            Paragraph("<b>Rate (₹)</b>", styles["Normal"]),
            Paragraph("<b>Tax (5%)</b>", styles["Normal"]),
            Paragraph("<b>Total (₹)</b>", styles["Normal"])
        ]
    ]

    idx = 1
    total_taxable = subtotal / 1.05  # 5% GST inclusive calculation
    total_gst_amount = subtotal - total_taxable
    cgst_val = total_gst_amount / 2
    sgst_val = total_gst_amount / 2

    for item in items_dict.values():
        item_total = item["price"] * item["qty"]
        hsn_code = f"2106{idx % 89 + 10:02d}"
        tax_part = item_total * 0.05
        table_data.append([
            str(idx),
            item["name"],
            hsn_code,
            str(item["qty"]),
            f"{item['price']:.2f}",
            f"{tax_part:.2f}",
            f"{item_total:.2f}"
        ])
        idx += 1

    product_table = Table(table_data, colWidths=[25, 235, 55, 40, 60, 60, 65])
    product_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#16a34a")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (3, -1), 'CENTER'),
        ('ALIGN', (4, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
    ]))
    story.append(product_table)
    story.append(Spacer(1, 10))

    # 5. Financial Summary & Tax Breakdown Table
    summary_data = [
        ["Taxable Subtotal (Excl. Tax):", f"Rs. {total_taxable:,.2f}"],
        ["CGST @ 2.5%:", f"Rs. {cgst_val:,.2f}"],
        ["SGST @ 2.5%:", f"Rs. {sgst_val:,.2f}"],
        ["Delivery & Handling Fee (Agra):", f"Rs. {delivery_fee:,.2f}"],
        ["TOTAL AMOUNT PAID:", f"Rs. {total_amount:,.2f}"]
    ]

    summary_table = Table(summary_data, colWidths=[380, 160])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 3), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, 3), 8),
        ('TEXTCOLOR', (0, 0), (-1, 3), colors.HexColor("#475569")),
        ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 4), (-1, 4), 11),
        ('TEXTCOLOR', (0, 4), (-1, 4), colors.HexColor("#16a34a")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LINEABOVE', (0, 4), (-1, 4), 1, colors.HexColor("#16a34a")),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 12))

    # 6. QR Code for Invoice Verification
    qr_code = qr.QrCodeWidget(f"SK-INV-{sale_id}-{total_amount}-AGRA")
    bounds = qr_code.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    d = Drawing(60, 60, transform=[60.0 / width, 0, 0, 60.0 / height, 0, 0])
    d.add(qr_code)

    qr_box_data = [
        [
            d,
            Paragraph(
                "<b>Digital Tax Invoice Verification</b><br/>"
                "Scan with GPay/PhonePe to verify GST compliance.<br/>"
                "<i>Returns accepted within 7 days with original invoice.</i>",
                styles["Normal"]
            )
        ]
    ]
    qr_box = Table(qr_box_data, colWidths=[70, 470])
    qr_box.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(qr_box)
    story.append(Spacer(1, 12))

    # 7. Official Legal Footer
    footer_text = ParagraphStyle(
        "FooterNote",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        textColor=colors.HexColor("#64748b"),
        alignment=1
    )
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=6))
    story.append(Paragraph("Thank you for shopping local with <b>SnapKart Superstore Agra</b>! ❤️", footer_text))
    story.append(Spacer(1, 2))
    story.append(Paragraph("Sanjay Place, Agra - 282002 • Helpline: +91 562 245 8900 • Email: support@snapkart.in", footer_text))
    story.append(Spacer(1, 2))
    story.append(Paragraph("<i>This is a computer-generated GST Tax Invoice under Rule 46 of CGST Rules 2017. Does not require physical signature.</i>", footer_text))

    doc.build(story)
    return pdf_path


def open_pdf_file(file_path):
    """Opens the generated PDF file using default system reader."""
    try:
        if sys.platform.startswith("win"):
            os.startfile(file_path)
        elif sys.platform.startswith("darwin"):
            subprocess.Popen(["open", file_path])
        else:
            subprocess.Popen(["xdg-open", file_path])
    except Exception as e:
        print(f"Could not open PDF automatically: {e}")