import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from database.db_connection import get_db_connection
from common.pdf_generator import generate_pdf_receipt, open_pdf_file


class BillingPOSFrame(ttk.Frame):
    """
    Dedicated High-Speed Point of Sale (POS) Billing Terminal for SnapKart Cashiers and Store Admins.
    Allows rapid product lookup, line-item management, tax computation, multi-mode payment,
    instant inventory deduction, and automated PDF invoice generation.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        self.bill_items = {}  # {item_id: {"name": str, "price": float, "qty": int, "max_stock": int}}
        self.last_sale_id = None

        self.create_ui()
        self.load_quick_catalog()

    def create_ui(self):
        # 1. Header Terminal Info
        header = tk.Frame(self, bg="#0f172a", height=50)
        header.pack(fill=tk.X, pady=(0, 10))
        header.pack_propagate(False)

        tk.Label(
            header,
            text="🛒 SnapKart POS - Billing & Checkout Terminal",
            font=("Segoe UI", 13, "bold"),
            fg="#38bdf8",
            bg="#0f172a"
        ).pack(side=tk.LEFT, padx=15)

        self.lbl_time = tk.Label(
            header,
            text=f"Terminal: POS-01 | {datetime.now().strftime('%d-%b-%Y %I:%M %p')}",
            font=("Segoe UI", 9),
            fg="#94a3b8",
            bg="#0f172a"
        )
        self.lbl_time.pack(side=tk.RIGHT, padx=15)

        # 2. Main Work Area (Split Left: Search & Inventory, Right: Active Bill & Checkout)
        main_split = tk.Frame(self)
        main_split.pack(fill=tk.BOTH, expand=True)

        # --- LEFT PANEL: Product Search & Quick Add ---
        left_panel = ttk.LabelFrame(main_split, text="Product Catalog & Barcode Scanner")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        # Search bar
        search_box = tk.Frame(left_panel)
        search_box.pack(fill=tk.X, padx=8, pady=6)

        ttk.Label(search_box, text="Search / Scan:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_box, textvariable=self.search_var, font=("Segoe UI", 10))
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.search_entry.bind("<KeyRelease>", lambda e: self.filter_products())
        self.search_entry.focus_set()

        ttk.Button(search_box, text="Clear", command=self.clear_search).pack(side=tk.RIGHT)

        # Catalog Table
        cols = ("id", "name", "category", "price", "stock")
        self.catalog_tree = ttk.Treeview(left_panel, columns=cols, show="headings", height=14, selectmode="browse")
        self.catalog_tree.heading("id", text="ID")
        self.catalog_tree.heading("name", text="Product Name")
        self.catalog_tree.heading("category", text="Department")
        self.catalog_tree.heading("price", text="Price (₹)")
        self.catalog_tree.heading("stock", text="In Stock")

        self.catalog_tree.column("id", width=55, anchor=tk.CENTER)
        self.catalog_tree.column("name", width=220, anchor=tk.W)
        self.catalog_tree.column("category", width=140, anchor=tk.W)
        self.catalog_tree.column("price", width=75, anchor=tk.E)
        self.catalog_tree.column("stock", width=65, anchor=tk.CENTER)

        c_scroll = ttk.Scrollbar(left_panel, orient=tk.VERTICAL, command=self.catalog_tree.yview)
        self.catalog_tree.configure(yscrollcommand=c_scroll.set)
        self.catalog_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=6)
        c_scroll.pack(side=tk.LEFT, fill=tk.Y, pady=6)

        # Quick Add controls under catalog
        add_ctrl = tk.Frame(left_panel)
        add_ctrl.pack(fill=tk.X, side=tk.BOTTOM, padx=8, pady=8)

        ttk.Label(add_ctrl, text="Quantity:").pack(side=tk.LEFT, padx=(0, 5))
        self.qty_var = tk.StringVar(value="1")
        self.qty_spin = ttk.Spinbox(add_ctrl, from_=1, to=999, textvariable=self.qty_var, width=5)
        self.qty_spin.pack(side=tk.LEFT, padx=(0, 10))

        btn_add = tk.Button(
            add_ctrl,
            text="➕ Add to Invoice Bill",
            font=("Segoe UI", 9, "bold"),
            bg="#16a34a",
            fg="#ffffff",
            relief=tk.FLAT,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.add_selected_to_bill
        )
        btn_add.pack(side=tk.LEFT)

        self.catalog_tree.bind("<Double-1>", lambda e: self.add_selected_to_bill())

        # --- RIGHT PANEL: Active Invoice & Checkout Details ---
        right_panel = ttk.LabelFrame(main_split, text="Current Invoice Bill & Checkout")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))

        # Customer Details
        cust_box = tk.Frame(right_panel, bg="#f8fafc", bd=1, relief=tk.SOLID)
        cust_box.pack(fill=tk.X, padx=8, pady=6, ipady=4)

        c_row1 = tk.Frame(cust_box, bg="#f8fafc")
        c_row1.pack(fill=tk.X, padx=8, pady=2)
        tk.Label(c_row1, text="Customer Name:", font=("Segoe UI", 8, "bold"), bg="#f8fafc").pack(side=tk.LEFT)
        self.entry_cust_name = tk.Entry(c_row1, font=("Segoe UI", 9), width=22)
        self.entry_cust_name.insert(0, "Walk-in Customer")
        self.entry_cust_name.pack(side=tk.LEFT, padx=(5, 15))

        tk.Label(c_row1, text="Phone / Mobile:", font=("Segoe UI", 8, "bold"), bg="#f8fafc").pack(side=tk.LEFT)
        self.entry_cust_phone = tk.Entry(c_row1, font=("Segoe UI", 9), width=15)
        self.entry_cust_phone.insert(0, "+91 ")
        self.entry_cust_phone.pack(side=tk.LEFT, padx=5)

        # Active Bill Items Treeview
        bill_cols = ("id", "name", "price", "qty", "total")
        self.bill_tree = ttk.Treeview(right_panel, columns=bill_cols, show="headings", height=8, selectmode="browse")
        self.bill_tree.heading("id", text="ID")
        self.bill_tree.heading("name", text="Item")
        self.bill_tree.heading("price", text="Price (₹)")
        self.bill_tree.heading("qty", text="Qty")
        self.bill_tree.heading("total", text="Total (₹)")

        self.bill_tree.column("id", width=45, anchor=tk.CENTER)
        self.bill_tree.column("name", width=180, anchor=tk.W)
        self.bill_tree.column("price", width=70, anchor=tk.E)
        self.bill_tree.column("qty", width=50, anchor=tk.CENTER)
        self.bill_tree.column("total", width=75, anchor=tk.E)

        b_scroll = ttk.Scrollbar(right_panel, orient=tk.VERTICAL, command=self.bill_tree.yview)
        self.bill_tree.configure(yscrollcommand=b_scroll.set)
        self.bill_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 0))
        b_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Item Modifier Buttons (+ / - / Remove)
        item_mods = tk.Frame(right_panel)
        item_mods.pack(fill=tk.X, padx=8, pady=4)

        tk.Button(item_mods, text="➕ Inc Qty", font=("Segoe UI", 8), command=self.increase_qty, cursor="hand2").pack(side=tk.LEFT, padx=2)
        tk.Button(item_mods, text="➖ Dec Qty", font=("Segoe UI", 8), command=self.decrease_qty, cursor="hand2").pack(side=tk.LEFT, padx=2)
        tk.Button(item_mods, text="🗑️ Remove Item", font=("Segoe UI", 8), fg="#dc2626", command=self.remove_item, cursor="hand2").pack(side=tk.LEFT, padx=2)
        tk.Button(item_mods, text="Clear All", font=("Segoe UI", 8), command=self.clear_bill, cursor="hand2").pack(side=tk.RIGHT, padx=2)

        # Checkout Calculations & Tender Frame
        calc_box = tk.Frame(right_panel, bg="#f1f5f9", bd=1, relief=tk.SOLID)
        calc_box.pack(fill=tk.X, padx=8, pady=6, ipady=6)

        # Row: Subtotal & Tax
        r_sum = tk.Frame(calc_box, bg="#f1f5f9")
        r_sum.pack(fill=tk.X, padx=12, pady=2)
        self.lbl_subtotal = tk.Label(r_sum, text="Subtotal: ₹ 0.00", font=("Segoe UI", 9), bg="#f1f5f9")
        self.lbl_subtotal.pack(side=tk.LEFT)
        self.lbl_tax = tk.Label(r_sum, text="GST (5% incl): ₹ 0.00", font=("Segoe UI", 9), bg="#f1f5f9", fg="#64748b")
        self.lbl_tax.pack(side=tk.RIGHT)

        # Row: Discount & Grand Total
        r_tot = tk.Frame(calc_box, bg="#f1f5f9")
        r_tot.pack(fill=tk.X, padx=12, pady=4)

        tk.Label(r_tot, text="Discount (₹):", font=("Segoe UI", 9), bg="#f1f5f9").pack(side=tk.LEFT)
        self.discount_var = tk.StringVar(value="0.00")
        self.entry_discount = tk.Entry(r_tot, textvariable=self.discount_var, width=7, font=("Segoe UI", 9))
        self.entry_discount.pack(side=tk.LEFT, padx=(4, 15))
        self.entry_discount.bind("<KeyRelease>", lambda e: self.recalculate_totals())

        self.lbl_grand_total = tk.Label(
            r_tot,
            text="Grand Total: ₹ 0.00",
            font=("Segoe UI", 12, "bold"),
            bg="#f1f5f9",
            fg="#16a34a"
        )
        self.lbl_grand_total.pack(side=tk.RIGHT)

        # Payment Mode Selection
        r_pay = tk.Frame(calc_box, bg="#f1f5f9")
        r_pay.pack(fill=tk.X, padx=12, pady=4)

        tk.Label(r_pay, text="Payment Mode:", font=("Segoe UI", 9, "bold"), bg="#f1f5f9").pack(side=tk.LEFT)
        self.pay_mode_var = tk.StringVar(value="Cash")
        pay_cb = ttk.Combobox(r_pay, textvariable=self.pay_mode_var, values=["Cash", "UPI QR", "Debit / Credit Card"], state="readonly", width=16)
        pay_cb.pack(side=tk.LEFT, padx=8)

        # Final Action Button: Complete Sale
        btn_complete = tk.Button(
            right_panel,
            text="✅ Complete Sale & Print Tax Invoice PDF",
            font=("Segoe UI", 11, "bold"),
            bg="#16a34a",
            fg="#ffffff",
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor="hand2",
            command=self.complete_sale_and_print
        )
        btn_complete.pack(fill=tk.X, padx=8, pady=(4, 6))

    # --- Catalog Loading & Filtering ---
    def load_quick_catalog(self):
        for row in self.catalog_tree.get_children():
            self.catalog_tree.delete(row)

        conn = get_db_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor(dictionary=True)
            search_txt = self.search_var.get().strip()
            query = "SELECT item_id, name, category, price, stock_quantity FROM inventory WHERE stock_quantity > 0"
            params = []
            if search_txt:
                query += " AND (name LIKE %s OR CAST(item_id AS CHAR) = %s)"
                params.extend([f"%{search_txt}%", search_txt])
            query += " ORDER BY item_id ASC LIMIT 100;"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            for r in rows:
                self.catalog_tree.insert("", tk.END, values=(r["item_id"], r["name"], r["category"], f"{float(r['price']):.2f}", r["stock_quantity"]))
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"POS Catalog error: {e}")

    def filter_products(self):
        self.load_quick_catalog()

    def clear_search(self):
        self.search_var.set("")
        self.load_quick_catalog()

    # --- Active Bill Management ---
    def add_selected_to_bill(self):
        selected = self.catalog_tree.selection()
        if not selected:
            messagebox.showwarning("Select Product", "Please select a product from the catalog list to add.")
            return

        values = self.catalog_tree.item(selected[0], "values")
        item_id = int(values[0])
        name = values[1]
        price = float(values[3])
        stock = int(values[4])

        try:
            qty_to_add = int(self.qty_var.get())
            if qty_to_add <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Quantity", "Please enter a valid positive quantity.")
            return

        current_qty = self.bill_items.get(item_id, {}).get("qty", 0)
        if current_qty + qty_to_add > stock:
            messagebox.showwarning("Stock Limit", f"Only {stock} units available in inventory for '{name}'.")
            return

        if item_id in self.bill_items:
            self.bill_items[item_id]["qty"] += qty_to_add
        else:
            self.bill_items[item_id] = {
                "name": name,
                "price": price,
                "qty": qty_to_add,
                "max_stock": stock
            }

        self.refresh_bill_display()
        self.search_entry.focus_set()

    def increase_qty(self):
        selected = self.bill_tree.selection()
        if not selected:
            return
        item_id = int(self.bill_tree.item(selected[0], "values")[0])
        item = self.bill_items.get(item_id)
        if item and item["qty"] < item["max_stock"]:
            item["qty"] += 1
            self.refresh_bill_display()
        elif item:
            messagebox.showinfo("Max Stock", f"Cannot exceed available stock of {item['max_stock']} units.")

    def decrease_qty(self):
        selected = self.bill_tree.selection()
        if not selected:
            return
        item_id = int(self.bill_tree.item(selected[0], "values")[0])
        if item_id in self.bill_items:
            if self.bill_items[item_id]["qty"] > 1:
                self.bill_items[item_id]["qty"] -= 1
            else:
                del self.bill_items[item_id]
            self.refresh_bill_display()

    def remove_item(self):
        selected = self.bill_tree.selection()
        if not selected:
            return
        item_id = int(self.bill_tree.item(selected[0], "values")[0])
        if item_id in self.bill_items:
            del self.bill_items[item_id]
            self.refresh_bill_display()

    def clear_bill(self):
        self.bill_items.clear()
        self.refresh_bill_display()

    def refresh_bill_display(self):
        for r in self.bill_tree.get_children():
            self.bill_tree.delete(r)

        subtotal = 0.0
        for i_id, data in self.bill_items.items():
            tot = data["price"] * data["qty"]
            subtotal += tot
            self.bill_tree.insert("", tk.END, values=(i_id, data["name"], f"{data['price']:.2f}", data["qty"], f"{tot:.2f}"))

        self.recalculate_totals()

    def recalculate_totals(self):
        subtotal = sum(d["price"] * d["qty"] for d in self.bill_items.values())
        gst = round(subtotal * 0.05 / 1.05, 2)

        try:
            discount = float(self.discount_var.get())
            if discount < 0:
                discount = 0.0
        except ValueError:
            discount = 0.0

        grand_total = max(0.0, subtotal - discount)
        self.lbl_subtotal.config(text=f"Subtotal: ₹ {subtotal:.2f}")
        self.lbl_tax.config(text=f"GST (5% incl): ₹ {gst:.2f}")
        self.lbl_grand_total.config(text=f"Grand Total: ₹ {grand_total:.2f}")

    # --- Sale Execution & Invoice Generation ---
    def complete_sale_and_print(self):
        if not self.bill_items:
            messagebox.showwarning("Empty Bill", "Please add at least one item to the invoice bill before completing.")
            return

        cust_name = self.entry_cust_name.get().strip() or "Walk-in Customer"
        cust_phone = self.entry_cust_phone.get().strip()
        pay_mode = self.pay_mode_var.get()

        subtotal = sum(d["price"] * d["qty"] for d in self.bill_items.values())
        try:
            discount = float(self.discount_var.get())
        except ValueError:
            discount = 0.0
        grand_total = max(0.0, subtotal - discount)

        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Database Error", "Failed to connect to MySQL database.")
            return

        try:
            cursor = conn.cursor()

            # 1. Insert into sales table
            cursor.execute("""
                INSERT INTO sales (customer_id, total_amount, payment_method, sale_datetime)
                VALUES (NULL, %s, %s, NOW());
            """, (grand_total, pay_mode))
            sale_id = cursor.lastrowid

            # 2. Insert items into sale_items and update inventory stock
            for item_id, item in self.bill_items.items():
                cursor.execute("""
                    INSERT INTO sale_items (sale_id, item_id, quantity, unit_price)
                    VALUES (%s, %s, %s, %s);
                """, (sale_id, item_id, item["qty"], item["price"]))

                cursor.execute("""
                    UPDATE inventory
                    SET stock_quantity = stock_quantity - %s
                    WHERE item_id = %s;
                """, (item["qty"], item_id))

            conn.commit()
            cursor.close()
            conn.close()

            self.last_sale_id = sale_id

            # 3. Generate Tax Invoice PDF
            pdf_path = generate_pdf_receipt(
                sale_id=sale_id,
                items_dict=self.bill_items,
                subtotal=subtotal,
                delivery_fee=0.0,
                total_amount=grand_total,
                customer_name=cust_name,
                customer_address="SnapKart In-Store Retail Counter",
                payment_method=pay_mode
            )

            messagebox.showinfo(
                "Sale Completed Successfully",
                f"✅ Invoice #{sale_id} generated successfully!\n\n"
                f"Customer: {cust_name}\n"
                f"Total Amount: ₹ {grand_total:.2f}\n"
                f"Payment Mode: {pay_mode}\n\n"
                f"Receipt saved to:\n{pdf_path}"
            )

            # Auto-open PDF receipt
            open_pdf_file(pdf_path)

            # Reset Terminal for Next Sale
            self.clear_bill()
            self.entry_cust_name.delete(0, tk.END)
            self.entry_cust_name.insert(0, "Walk-in Customer")
            self.entry_cust_phone.delete(0, tk.END)
            self.entry_cust_phone.insert(0, "+91 ")
            self.discount_var.set("0.00")
            self.load_quick_catalog()

        except Exception as e:
            if conn and conn.is_connected():
                conn.rollback()
                conn.close()
            messagebox.showerror("Transaction Failed", f"Error recording sale: {e}")
