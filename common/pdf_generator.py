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

from database.db_connection import get_db_connection


def generate_pdf_receipt(sale_id, items_dict, subtotal, delivery_fee, total_amount, customer_name="Guest Customer", payment_method="UPI", output_dir="receipts"):
    """
    Generates a professional PDF invoice slip using real order data.
    Saves it in the 'receipts' folder and returns the file path.
    """
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"SnapKart_Invoice_{sale_id}.pdf")

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "BrandTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        textColor=colors.HexColor("#16a34a"),
        alignment=0,
        spaceAfter=2
    )

    tagline_style = ParagraphStyle(
        "BrandTagline",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#64748b"),
        alignment=0,
        spaceAfter=15
    )

    address_style = ParagraphStyle(
        "StoreAddress",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#334155"),
        alignment=2,
        leading=12
    )

    # 1. Header: Store branding and address
    header_data = [
        [
            Paragraph("<b>SnapKart Retail</b>", title_style),
            Paragraph(
                "<b>SnapKart Superstore</b><br/>"
                "Sanjay Place, Agra - 282002<br/>"
                "Uttar Pradesh, India<br/>"
                "GSTIN: 09AAACS1429B1Z8",
                address_style
            )
        ],
        [
            Paragraph("Your Neighbourhood Store, Online", tagline_style),
            ""
        ]
    ]

    header_table = Table(header_data, colWidths=[260, 260])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#16a34a"), spaceAfter=12))

    # 2. Invoice Metadata
    now_str = datetime.now().strftime("%d %b %Y, %I:%M %p")
    meta_data = [
        [
            Paragraph(f"<b>Invoice ID:</b> #{sale_id}", styles["Normal"]),
            Paragraph(f"<b>Date:</b> {now_str}", styles["Normal"])
        ],
        [
            Paragraph(f"<b>Billed To:</b> {customer_name}", styles["Normal"]),
            Paragraph(f"<b>Payment Mode:</b> {payment_method}", styles["Normal"])
        ]
    ]

    meta_table = Table(meta_data, colWidths=[260, 260])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))

    # 3. Items Table
    table_data = [
        [
            Paragraph("<b>#</b>", styles["Normal"]),
            Paragraph("<b>Item Description</b>", styles["Normal"]),
            Paragraph("<b>Qty</b>", styles["Normal"]),
            Paragraph("<b>Unit Price (Rs)</b>", styles["Normal"]),
            Paragraph("<b>Total (Rs)</b>", styles["Normal"])
        ]
    ]

    idx = 1
    for item in items_dict.values():
        item_total = item["price"] * item["qty"]
        table_data.append([
            str(idx),
            item["name"],
            str(item["qty"]),
            f"{item['price']:.2f}",
            f"{item_total:.2f}"
        ])
        idx += 1

    product_table = Table(table_data, colWidths=[30, 260, 50, 90, 90])
    product_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#16a34a")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
    ]))
    story.append(product_table)
    story.append(Spacer(1, 10))

    # 4. Summary Table
    summary_data = [
        ["Subtotal:", f"Rs. {subtotal:,.2f}"],
        ["Delivery / Handling Fee:", f"Rs. {delivery_fee:,.2f}"],
        ["TOTAL AMOUNT PAID:", f"Rs. {total_amount:,.2f}"]
    ]

    summary_table = Table(summary_data, colWidths=[380, 140])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, 1), 9),
        ('TEXTCOLOR', (0, 0), (-1, 1), colors.HexColor("#475569")),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 2), (-1, 2), 12),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.HexColor("#16a34a")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEABOVE', (0, 2), (-1, 2), 1, colors.HexColor("#16a34a")),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 25))

    # 5. Footer Notes
    footer_text = ParagraphStyle(
        "FooterNote",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        textColor=colors.HexColor("#64748b"),
        alignment=1
    )
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=10))
    story.append(Paragraph("Thank you for shopping local with <b>SnapKart</b>!", footer_text))
    story.append(Spacer(1, 2))
    story.append(Paragraph("For support or inquiries, visit our store at Sanjay Place, Agra or email support@snapkart.in", footer_text))
    story.append(Spacer(1, 2))
    story.append(Paragraph("<i>This is a computer-generated tax invoice and does not require a physical signature.</i>", footer_text))

    doc.build(story)
    return pdf_path


def open_pdf_file(file_path):
    """Opens the generated PDF file using the default system reader."""
    try:
        if sys.platform.startswith("win"):
            os.startfile(file_path)
        elif sys.platform.startswith("darwin"):
            subprocess.Popen(["open", file_path])
        else:
            subprocess.Popen(["xdg-open", file_path])
    except Exception as e:
        print(f"Could not open PDF automatically: {e}")


# =====================================================================
# TEST BLOCK: DIRECT MYSQL QUERY ONLY (NO HARDCODED SAMPLES)
# =====================================================================
if __name__ == "__main__":
    conn = get_db_connection()
    if not conn:
        print("Cannot test PDF generator: Failed to connect to MySQL database.")
        sys.exit(1)

    cursor = conn.cursor(dictionary=True)

    # 1. Check if an actual sale exists in the database
    cursor.execute("""
        SELECT s.sale_id, s.total_amount, s.payment_method, 
               COALESCE(c.full_name, 'Guest Customer') AS customer_name
        FROM sales s
        LEFT JOIN customers c ON s.customer_id = c.customer_id
        ORDER BY s.sale_id DESC
        LIMIT 1;
    """)
    last_sale = cursor.fetchone()

    items_dict = {}
    delivery_fee = 20.0

    if last_sale:
        sale_id = last_sale["sale_id"]
        total_amount = float(last_sale["total_amount"])
        subtotal = total_amount - delivery_fee
        cust_name = last_sale["customer_name"]
        pay_mode = last_sale["payment_method"] or "UPI"

        # Fetch actual items belonging to this sale
        cursor.execute("""
            SELECT i.name, si.quantity, si.unit_price
            FROM sale_items si
            JOIN inventory i ON si.item_id = i.item_id
            WHERE si.sale_id = %s;
        """, (sale_id,))
        rows = cursor.fetchall()

        for idx, r in enumerate(rows, start=1):
            items_dict[idx] = {
                "name": r["name"],
                "price": float(r["unit_price"]),
                "qty": int(r["quantity"])
            }
        print(f"Testing with actual sale #{sale_id} from database...")

    else:
        # If no sales have occurred yet, pull the first 3 actual products from your inventory table
        print("No sales in database yet. Querying real products from 'inventory' table...")
        cursor.execute("SELECT item_id, name, price FROM inventory LIMIT 3;")
        real_products = cursor.fetchall()

        if not real_products:
            print("The inventory table is empty. Run 'python -m database.populate_inventory' first.")
            sys.exit(1)

        sale_id = 1
        subtotal = 0.0
        cust_name = "Database Test"
        pay_mode = "Cash"

        for p in real_products:
            p_price = float(p["price"])
            items_dict[p["item_id"]] = {
                "name": p["name"],
                "price": p_price,
                "qty": 1
            }
            subtotal += p_price

        total_amount = subtotal + delivery_fee

    cursor.close()
    conn.close()

    # Generate and open PDF using real database records
    pdf = generate_pdf_receipt(
        sale_id=sale_id,
        items_dict=items_dict,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        total_amount=total_amount,
        customer_name=cust_name,
        payment_method=pay_mode
    )

    print(f"PDF successfully generated from database: {pdf}")
    open_pdf_file(pdf)