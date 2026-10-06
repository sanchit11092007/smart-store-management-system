import math
import tkinter as tk
from tkinter import ttk, messagebox
from database.db_connection import get_db_connection


class InventoryFrame(ttk.Frame):
    """
    High-Performance Inventory & Stock Management Interface for SnapKart Admin.
    Supports Product Management (CRUD), Stock Management (Quick Restock),
    and Low Stock Alerts with high-speed paginated database querying.
    """
    def __init__(self, parent, filter_mode="all"):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.filter_mode = filter_mode  # "all", "low_stock", or "stock_mgmt"
        self.selected_item_id = None
        self.current_page = 1
        self.page_size = 100
        self.total_count = 0
        self.total_pages = 1

        self.create_widgets()
        self.load_categories()
        self.load_inventory()

    def create_widgets(self):
        # 1. Mode Banner
        if self.filter_mode == "low_stock":
            banner = tk.Frame(self, bg="#fef2f2", bd=1, relief=tk.SOLID)
            banner.pack(fill=tk.X, pady=(0, 6), ipady=4)
            tk.Label(
                banner,
                text="⚠️ LOW STOCK ALERTS: Displaying products with inventory <= 25 units. Reorder recommended.",
                font=("Segoe UI", 9, "bold"),
                fg="#dc2626",
                bg="#fef2f2"
            ).pack(side=tk.LEFT, padx=12)
        elif self.filter_mode == "stock_mgmt":
            banner = tk.Frame(self, bg="#eff6ff", bd=1, relief=tk.SOLID)
            banner.pack(fill=tk.X, pady=(0, 6), ipady=4)
            tk.Label(
                banner,
                text="📦 STOCK MANAGEMENT: Track inventory levels, restock fast-moving items, and manage quantities.",
                font=("Segoe UI", 9, "bold"),
                fg="#2563eb",
                bg="#eff6ff"
            ).pack(side=tk.LEFT, padx=12)

        # 2. Search & Filter Bar
        search_frame = ttk.LabelFrame(self, text="Search & Filter Catalog")
        search_frame.pack(fill=tk.X, padx=5, pady=4)

        ttk.Label(search_frame, text="Product Name / ID:").pack(side=tk.LEFT, padx=5, pady=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=22)
        self.search_entry.pack(side=tk.LEFT, padx=5, pady=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.on_search_change())

        ttk.Label(search_frame, text="Category:").pack(side=tk.LEFT, padx=5, pady=5)
        self.category_filter_var = tk.StringVar(value="All")
        self.category_dropdown = ttk.Combobox(
            search_frame,
            textvariable=self.category_filter_var,
            state="readonly",
            width=22
        )
        self.category_dropdown.pack(side=tk.LEFT, padx=5, pady=5)
        self.category_dropdown.bind("<<ComboboxSelected>>", lambda e: self.on_filter_change())

        ttk.Button(search_frame, text="Reset Filters", command=self.reset_filters).pack(side=tk.LEFT, padx=8)

        # Status text
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(search_frame, textvariable=self.status_var, font=("Segoe UI", 8, "bold")).pack(side=tk.RIGHT, padx=10)

        # 3. Main Treeview
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=4)

        columns = ("id", "name", "category", "price", "stock", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("id", text="Item ID")
        self.tree.heading("name", text="Product Name")
        self.tree.heading("category", text="Department / Category")
        self.tree.heading("price", text="Price (₹)")
        self.tree.heading("stock", text="Stock Qty")
        self.tree.heading("status", text="Stock Status")

        self.tree.column("id", width=65, anchor=tk.CENTER)
        self.tree.column("name", width=340, anchor=tk.W)
        self.tree.column("category", width=220, anchor=tk.W)
        self.tree.column("price", width=85, anchor=tk.E)
        self.tree.column("stock", width=85, anchor=tk.CENTER)
        self.tree.column("status", width=110, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.on_item_select)

        # 4. Pagination Controls Bar
        pag_frame = tk.Frame(self, bg="#f8fafc", bd=1, relief=tk.SOLID)
        pag_frame.pack(fill=tk.X, padx=5, pady=4, ipady=3)

        self.btn_prev = ttk.Button(pag_frame, text="◀ Previous 100", command=self.prev_page)
        self.btn_prev.pack(side=tk.LEFT, padx=10)

        self.lbl_pag_info = tk.Label(pag_frame, text="Page 1 of 1", font=("Segoe UI", 9, "bold"), bg="#f8fafc")
        self.lbl_pag_info.pack(side=tk.LEFT, expand=True)

        self.btn_next = ttk.Button(pag_frame, text="Next 100 ▶", command=self.next_page)
        self.btn_next.pack(side=tk.RIGHT, padx=10)

        # 5. Bottom Contextual Control Panels
        if self.filter_mode in ("stock_mgmt", "low_stock"):
            # Quick Restock Bar
            stock_box = ttk.LabelFrame(self, text="⚡ Fast Restock & Inventory Adjustment")
            stock_box.pack(fill=tk.X, padx=5, pady=4)

            tk.Label(stock_box, text="Selected Product:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=8, pady=5)
            self.lbl_selected_stock_item = tk.Label(stock_box, text="None selected", font=("Segoe UI", 9), fg="#2563eb")
            self.lbl_selected_stock_item.pack(side=tk.LEFT, padx=5, pady=5)

            tk.Label(stock_box, text="Quick Add:").pack(side=tk.LEFT, padx=(15, 5))
            for qty in [10, 25, 50, 100]:
                ttk.Button(stock_box, text=f"+{qty}", width=5, command=lambda q=qty: self.quick_adjust_stock(q)).pack(side=tk.LEFT, padx=2)

            tk.Label(stock_box, text="Custom Set:").pack(side=tk.LEFT, padx=(15, 5))
            self.custom_stock_var = tk.StringVar(value="")
            ttk.Entry(stock_box, textvariable=self.custom_stock_var, width=6).pack(side=tk.LEFT, padx=4)
            ttk.Button(stock_box, text="Set Stock", command=self.set_custom_stock).pack(side=tk.LEFT, padx=4)

        # Product Details CRUD Form
        form_frame = ttk.LabelFrame(self, text="Product Details & Inventory Form")
        form_frame.pack(fill=tk.X, padx=5, pady=4)

        # Row 0
        ttk.Label(form_frame, text="Product Name:").grid(row=0, column=0, padx=5, pady=4, sticky=tk.W)
        self.name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.name_var, width=32).grid(row=0, column=1, padx=5, pady=4)

        ttk.Label(form_frame, text="Category:").grid(row=0, column=2, padx=5, pady=4, sticky=tk.W)
        self.item_category_var = tk.StringVar()
        self.form_category_combobox = ttk.Combobox(form_frame, textvariable=self.item_category_var, width=26)
        self.form_category_combobox.grid(row=0, column=3, padx=5, pady=4)

        # Row 1
        ttk.Label(form_frame, text="Price (₹):").grid(row=1, column=0, padx=5, pady=4, sticky=tk.W)
        self.price_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.price_var, width=15).grid(row=1, column=1, padx=5, pady=4, sticky=tk.W)

        ttk.Label(form_frame, text="Stock Available:").grid(row=1, column=2, padx=5, pady=4, sticky=tk.W)
        self.stock_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.stock_var, width=15).grid(row=1, column=3, padx=5, pady=4, sticky=tk.W)

        # Row 2: Action Buttons
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=6)

        ttk.Button(btn_frame, text="➕ Add New Product", command=self.add_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="💾 Update Product Details", command=self.update_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ Delete Product", command=self.delete_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear Form", command=self.clear_form).pack(side=tk.LEFT, padx=5)

    def on_search_change(self):
        self.current_page = 1
        self.load_inventory()

    def on_filter_change(self):
        self.current_page = 1
        self.load_inventory()

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_inventory()

    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_inventory()

    def load_categories(self):
        conn = get_db_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT category FROM inventory ORDER BY category;")
            categories = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
        except Exception:
            categories = []

        self.category_dropdown["values"] = ["All"] + categories
        self.category_dropdown.current(0)
        self.form_category_combobox["values"] = categories

    def load_inventory(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = get_db_connection()
        if not conn:
            self.status_var.set("DB Error")
            return

        try:
            cursor = conn.cursor()
            search_query = self.search_var.get().strip()
            category_filter = self.category_filter_var.get()

            # Base conditions
            where_clauses = ["1=1"]
            params = []

            if self.filter_mode == "low_stock":
                where_clauses.append("stock_quantity <= 25")

            if search_query:
                where_clauses.append("(name LIKE %s OR CAST(item_id AS CHAR) = %s)")
                params.extend([f"%{search_query}%", search_query])

            if category_filter and category_filter != "All":
                where_clauses.append("category = %s")
                params.append(category_filter)

            where_sql = " AND ".join(where_clauses)

            # 1. Count query
            cursor.execute(f"SELECT COUNT(*) FROM inventory WHERE {where_sql};", params)
            self.total_count = cursor.fetchone()[0]
            self.total_pages = max(1, math.ceil(self.total_count / self.page_size))
            self.current_page = max(1, min(self.current_page, self.total_pages))

            # 2. Page query
            offset = (self.current_page - 1) * self.page_size
            data_sql = f"""
                SELECT item_id, name, category, price, stock_quantity
                FROM inventory
                WHERE {where_sql}
                ORDER BY item_id ASC
                LIMIT %s OFFSET %s;
            """
            cursor.execute(data_sql, params + [self.page_size, offset])
            rows = cursor.fetchall()

            for item in rows:
                item_id, name, cat, price, stock = item
                status_str = "⚠️ LOW STOCK" if stock <= 25 else "✅ In Stock"
                self.tree.insert("", tk.END, values=(item_id, name, cat, f"{float(price):.2f}", stock, status_str))

            start_idx = offset + 1 if self.total_count > 0 else 0
            end_idx = min(offset + len(rows), self.total_count)
            self.lbl_pag_info.config(text=f"Page {self.current_page} of {self.total_pages} (Items {start_idx} - {end_idx} of {self.total_count:,})")
            self.status_var.set(f"{self.total_count:,} Products Total")

            self.btn_prev.config(state=tk.NORMAL if self.current_page > 1 else tk.DISABLED)
            self.btn_next.config(state=tk.NORMAL if self.current_page < self.total_pages else tk.DISABLED)

            cursor.close()
            conn.close()
        except Exception as e:
            self.status_var.set(f"Error: {e}")

    def on_item_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        self.selected_item_id = values[0]
        self.name_var.set(values[1])
        self.item_category_var.set(values[2])
        self.price_var.set(values[3])
        self.stock_var.set(values[4])

        if hasattr(self, "lbl_selected_stock_item"):
            self.lbl_selected_stock_item.config(text=f"#{values[0]} {values[1][:25]} (Current Stock: {values[4]})")

    def quick_adjust_stock(self, add_qty):
        if not self.selected_item_id:
            messagebox.showwarning("Select Product", "Please select an item from the list above to restock.")
            return

        conn = get_db_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE inventory SET stock_quantity = stock_quantity + %s WHERE item_id = %s;", (add_qty, self.selected_item_id))
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Stock Updated", f"Added +{add_qty} units to product #{self.selected_item_id}.")
            self.load_inventory()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update stock: {e}")

    def set_custom_stock(self):
        if not self.selected_item_id:
            messagebox.showwarning("Select Product", "Please select an item from the list above.")
            return
        txt = self.custom_stock_var.get().strip()
        if not txt.isdigit():
            messagebox.showerror("Invalid Input", "Please enter a valid positive number for stock.")
            return
        new_val = int(txt)

        conn = get_db_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE inventory SET stock_quantity = %s WHERE item_id = %s;", (new_val, self.selected_item_id))
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Stock Updated", f"Set stock for #{self.selected_item_id} to {new_val} units.")
            self.custom_stock_var.set("")
            self.load_inventory()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set stock: {e}")

    def add_item(self):
        name = self.name_var.get().strip()
        category = self.item_category_var.get().strip()
        price = self.price_var.get().strip()
        stock = self.stock_var.get().strip()

        if not name or not category or not price or not stock:
            messagebox.showwarning("Validation Error", "All fields are required!")
            return

        try:
            price_val = float(price)
            stock_val = int(stock)
            if price_val < 0 or stock_val < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Validation Error", "Price must be a valid number and Stock must be a non-negative integer.")
            return

        conn = get_db_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO inventory (name, category, price, stock_quantity) VALUES (%s, %s, %s, %s)",
                (name, category, price_val, stock_val)
            )
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Success", f"Product '{name}' added successfully!")
            self.clear_form()
            self.load_categories()
            self.load_inventory()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add product: {e}")

    def update_item(self):
        if not self.selected_item_id:
            messagebox.showwarning("Selection Required", "Please select an item from the list to update.")
            return

        name = self.name_var.get().strip()
        category = self.item_category_var.get().strip()
        price = self.price_var.get().strip()
        stock = self.stock_var.get().strip()

        if not name or not category or not price or not stock:
            messagebox.showwarning("Validation Error", "All fields are required!")
            return

        try:
            price_val = float(price)
            stock_val = int(stock)
            if price_val < 0 or stock_val < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Validation Error", "Price and stock must be valid non-negative numbers.")
            return

        conn = get_db_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE inventory SET name = %s, category = %s, price = %s, stock_quantity = %s WHERE item_id = %s",
                (name, category, price_val, stock_val, self.selected_item_id)
            )
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Success", "Product details updated successfully!")
            self.clear_form()
            self.load_inventory()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update product: {e}")

    def delete_item(self):
        if not self.selected_item_id:
            messagebox.showwarning("Selection Required", "Please select an item from the list to delete.")
            return

        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this product?")
        if not confirm:
            return

        conn = get_db_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sale_items WHERE item_id = %s", (self.selected_item_id,))
            cursor.execute("DELETE FROM inventory WHERE item_id = %s", (self.selected_item_id,))
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Deleted", "Product deleted successfully.")
            self.clear_form()
            self.load_inventory()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete product: {e}")

    def reset_filters(self):
        self.search_var.set("")
        self.category_filter_var.set("All")
        self.current_page = 1
        self.load_inventory()

    def clear_form(self):
        self.selected_item_id = None
        self.name_var.set("")
        self.item_category_var.set("")
        self.price_var.set("")
        self.stock_var.set("")
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection()[0])
        if hasattr(self, "lbl_selected_stock_item"):
            self.lbl_selected_stock_item.config(text="None selected")


if __name__ == "__main__":
    root = tk.Tk()
    root.title("SnapKart - Product & Stock Inventory")
    root.geometry("1100x720")
    app = InventoryFrame(root)
    root.mainloop()