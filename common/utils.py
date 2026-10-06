import os
from datetime import datetime


def format_receipt(sale_id, items_dict, subtotal, delivery_fee, total_amount, payment_method="UPI"):
    """
    Creates a clean, formatted receipt text for a completed order.
    The address is set to Sanjay Place, Agra - 282002.
    """
    now_str = datetime.now().strftime("%d-%b-%Y  %I:%M:%S %p")
    line = "=" * 48
    dash = "-" * 48

    receipt_lines = [
        line,
        "                 SNAPKART RETAIL                ",
        "        Your Neighbourhood Store, Online        ",
        "         Sanjay Place, Agra - 282002            ",
        "            Uttar Pradesh, India                ",
        line,
        f"Invoice ID : #{sale_id}",
        f"Date & Time: {now_str}",
        f"Payment    : {payment_method}",
        dash,
        f"{'Item':<24}{'Qty':>4}   {'Price':>7}   {'Total':>7}",
        dash
    ]

    for item in items_dict.values():
        name = item["name"]
        # Shorten very long product names so alignment stays neat
        if len(name) > 22:
            name = name[:20] + ".."
        qty = item["qty"]
        price = item["price"]
        sub = price * qty
        receipt_lines.append(f"{name:<24}{qty:>4}   {price:>7.2f}   {sub:>7.2f}")

    receipt_lines.extend([
        dash,
        f"{'Subtotal:':<36}₹ {subtotal:>8.2f}",
        f"{'Delivery Charge:':<36}₹ {delivery_fee:>8.2f}",
        line,
        f"{'TOTAL AMOUNT PAID:':<36}₹ {total_amount:>8.2f}",
        line,
        "          Thank you for shopping with us!       ",
        "        Please visit again: SnapKart.in         ",
        line
    ])

    return "\n".join(receipt_lines)


def save_receipt_file(sale_id, receipt_text, output_dir="receipts"):
    """
    Saves the receipt text to a .txt file inside the receipts folder.

    Returns:
        str: The path where the receipt file was saved.
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"receipt_{sale_id}.txt")

    with open(filename, "w", encoding="utf-8") as f:
        f.write(receipt_text)

    return filename


# Test block to verify receipt generation
if __name__ == "__main__":
    sample_cart = {
        1: {"name": "Amul Full Cream Milk 1L", "price": 66.0, "qty": 2},
        2: {"name": "Lays Classic Chips (Family Pack)", "price": 40.0, "qty": 1},
        3: {"name": "Aashirvaad Sharbati Atta 5kg", "price": 280.0, "qty": 1}
    }
    sample_subtotal = (66.0 * 2) + 40.0 + 280.0
    sample_delivery = 20.0
    sample_total = sample_subtotal + sample_delivery

    test_receipt = format_receipt(
        sale_id=1001,
        items_dict=sample_cart,
        subtotal=sample_subtotal,
        delivery_fee=sample_delivery,
        total_amount=sample_total,
        payment_method="UPI"
    )

    print(test_receipt)
    saved_file = save_receipt_file(1001, test_receipt)
    print(f"\n[+] Test receipt saved successfully to: {saved_file}")