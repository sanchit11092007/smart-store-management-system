import tkinter as tk
from tkinter import ttk, messagebox

from database.db_connection import get_db_connection
from common.pdf_generator import generate_pdf_receipt, open_pdf_file


class TransactionsFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True, padx=15, pady=12)

        self.selected_sale_id = None
        self.selected_sale_meta = {}

        self.create_top_search_bar()
        self.create_split_layout()
        self.load_all_transactions()

    # 1. Search Bar at Top
    def create_top_search_bar(self):
        search_frame = ttk.LabelFrame(self, text="Search Orders")
        search_frame.pack(fill=tk.X, pady=(0, 10), padx=5)

        ttk.Label(search_frame, text="Search (Sale ID or Customer Name):").pack(side=tk.LEFT, padx=10, pady=8)

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5, pady=8)
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_all_transactions())

        ttk.Button(search_frame, text="Refresh", command=self.load_all_transactions).pack(side=tk.LEFT, padx=8)

    # 2. Main Area: Left (All Sales) + Right (Items in Selected Sale)
    def create_split_layout(self):
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left Side: Sales List
        left_frame = ttk.LabelFrame(paned, text="All Invoices (Click to view details)")
        paned.add(left_frame, weight=3)

        cols = ("id", "datetime", "customer", "amount", "payment")
        self.sales_tree = ttk.Treeview(left_frame, columns=cols, show="headings", selectmode="browse")

        self.sales_tree.heading("id", text="Sale ID")
        self.sales_tree.heading("datetime", text="Date & Time")
        self.sales_tree.heading("customer", text="Customer")
        self.sales_tree.heading("amount", text="Total (₹)")
        self.sales_tree.heading("payment", text="Payment")

        self.sales_tree.column("id", width=65, anchor="center")
        self.sales_tree.column("datetime", width=145, anchor="center")
        self.sales_tree.column("customer", width=130, anchor="w")
        self.sales_tree.column("amount", width=90, anchor="e")
        self.sales_tree.column("payment", width=75, anchor="center")

        sales_scroll = ttk.Scrollbar(left_frame, orient="vertical", command=self.sales_tree.yview)
        self.sales_tree.configure(yscrollcommand=sales_scroll.set)

        self.sales_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        sales_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        self.sales_tree.bind("<<TreeviewSelect>>", self.on_sale_select)

        # Right Side: Order Items & Actions
        right_frame = ttk.LabelFrame(paned, text="Invoice Items & Actions")
        paned.add(right_frame, weight=2)

        item_cols = ("name", "qty", "price", "subtotal")
        self.items_tree = ttk.Treeview(right_frame, columns=item_cols, show="headings", selectmode="browse")

        self.items_tree.heading("name", text="Product")
        self.items_tree.heading("qty", text="Qty")
        self.items_tree.heading("price", text="Price")
        self.items_tree.heading("subtotal", text="Subtotal")

        self.items_tree.column("name", width=140, anchor="w")
        self.items_tree.column("qty", width=45, anchor="center")
        self.items_tree.column("price", width=60, anchor="e")
        self.items_tree.column("subtotal", width=70, anchor="e")

        items_scroll = ttk.Scrollbar(right_frame, orient="vertical", command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=items_scroll.set)

        self.items_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        items_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Reprint PDF Button
        btn_box = tk.Frame(right_frame, bg="#ffffff")
        btn_box.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        self.btn_reprint_pdf = tk.Button(
            btn_box,
            text="📄 Open / Reprint PDF Receipt",
            font=("Segoe UI", 9, "bold"),
            bg="#16a34a",
            fg="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.reprint_pdf_receipt
        )
        self.btn_reprint_pdf.pack(fill=tk.X, ipady=6)

    # 3. Load Sales from MySQL
    def load_all_transactions(self):
        for row in self.sales_tree.get_children():
            self.sales_tree.delete(row)
        for row in self.items_tree.get_children():
            self.items_tree.delete(row)

        self.selected_sale_id = None

        conn = get_db_connection()
        if not conn:
            return

        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            search_txt = self.search_var.get().strip()

            query = """
                SELECT s.sale_id, DATE_FORMAT(s.sale_datetime, '%Y-%m-%d %h:%i %p') AS s_time,
                       s.total_amount, s.payment_method,
                       COALESCE(c.full_name, 'Guest Customer') AS customer_name
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.customer_id
                WHERE 1=1
            """
            params = []

            if search_txt:
                query += " AND (CAST(s.sale_id AS CHAR) LIKE %s OR c.full_name LIKE %s)"
                params.extend([f"%{search_txt}%", f"%{search_txt}%"])

            query += " ORDER BY s.sale_datetime DESC;"
            cursor.execute(query, params)
            sales = cursor.fetchall()
            
            for s in sales:
                self.sales_tree.insert("", tk.END, values=(
                    s["sale_id"],
                    s["s_time"],
                    s["customer_name"],
                    f"₹ {float(s['total_amount']):.2f}",
                    s["payment_method"] or "UPI"
                ))
        except Exception as e:
            print(f"Error loading transactions: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    # 4. When Admin Clicks a Sale in the List
    def on_sale_select(self, event):
        selected = self.sales_tree.selection()
        if not selected:
            return

        values = self.sales_tree.item(selected[0], "values")
        self.selected_sale_id = int(values[0])

        self.selected_sale_meta = {
            "sale_id": self.selected_sale_id,
            "customer_name": values[2],
            "total_amount": float(values[3].replace("₹", "").replace(",", "").strip()),
            "payment_method": values[4]
        }

        # Clear items list
        for row in self.items_tree.get_children():
            self.items_tree.delete(row)

        conn = get_db_connection()
        if not conn:
            return

        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT i.name, si.quantity, si.unit_price, si.subtotal
                FROM sale_items si
                JOIN inventory i ON si.item_id = i.item_id
                WHERE si.sale_id = %s;
            """, (self.selected_sale_id,))
            items = cursor.fetchall()

            for itm in items:
                self.items_tree.insert("", tk.END, values=(
                    itm["name"],
                    itm["quantity"],
                    f"₹{float(itm['unit_price']):.2f}",
                    f"₹{float(itm['subtotal']):.2f}"
                ))
        except Exception as e:
            print(f"Error loading sale items: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    # 5. Reprint or View PDF
    def reprint_pdf_receipt(self):
        if not self.selected_sale_id:
            messagebox.showwarning("Select Invoice", "Please select an invoice from the list first.")
            return

        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Error", "Could not connect to database.")
            return

        cursor = None
        rows = []
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT i.name, si.quantity, si.unit_price
                FROM sale_items si
                JOIN inventory i ON si.item_id = i.item_id
                WHERE si.sale_id = %s;
            """, (self.selected_sale_id,))
            rows = cursor.fetchall()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch sale items: {e}")
            return
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

        if not rows:
            messagebox.showwarning("No Items", "No items found for this invoice.")
            return

        # Prepare items dictionary for PDF
        items_dict = {}
        subtotal = 0.0
        for idx, r in enumerate(rows, start=1):
            qty = int(r["quantity"])
            price = float(r["unit_price"])
            subtotal += (qty * price)
            items_dict[idx] = {
                "name": r["name"],
                "price": price,
                "qty": qty
            }

        delivery_fee = 20.0
        total_amount = self.selected_sale_meta["total_amount"]

        # Generate and open PDF
        pdf_path = generate_pdf_receipt(
            sale_id=self.selected_sale_id,
            items_dict=items_dict,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            total_amount=total_amount,
            customer_name=self.selected_sale_meta["customer_name"],
            payment_method=self.selected_sale_meta["payment_method"]
        )

        open_pdf_file(pdf_path)


# Quick Standalone Test
if __name__ == "__main__":
    root = tk.Tk()
    root.title("SnapKart - Transactions History")
    root.geometry("950x620")
    app = TransactionsFrame(root)
    root.mainloop()