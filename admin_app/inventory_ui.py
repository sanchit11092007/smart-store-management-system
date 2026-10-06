import tkinter as tk
from tkinter import ttk, messagebox
from database.db_connection import get_db_connection


class InventoryFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.selected_item_id = None
        self.create_widgets()
        self.load_categories()
        self.load_inventory()

    def create_widgets(self):
        # 1. Top Search and Filter Bar
        search_frame = ttk.LabelFrame(self, text="Search & Filter Products")
        search_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(search_frame, text="Product Name:").pack(side=tk.LEFT, padx=5, pady=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=25)
        self.search_entry.pack(side=tk.LEFT, padx=5, pady=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_inventory())

        ttk.Label(search_frame, text="Category:").pack(side=tk.LEFT, padx=5, pady=5)
        self.category_filter_var = tk.StringVar(value="All")
        self.category_dropdown = ttk.Combobox(
            search_frame, 
            textvariable=self.category_filter_var, 
            state="readonly", 
            width=25
        )
        self.category_dropdown.pack(side=tk.LEFT, padx=5, pady=5)
        self.category_dropdown.bind("<<ComboboxSelected>>", lambda e: self.load_inventory())

        ttk.Button(search_frame, text="Reset Filters", command=self.reset_filters).pack(side=tk.LEFT, padx=10)

        # Status bar showing item count
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(search_frame, textvariable=self.status_var, font=("Segoe UI", 8))
        status_bar.pack(side=tk.RIGHT, padx=10)

        # 2. Main Inventory Table (Treeview)
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("id", "name", "category", "price", "stock")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("id", text="Item ID")
        self.tree.heading("name", text="Product Name")
        self.tree.heading("category", text="Department / Category")
        self.tree.heading("price", text="Price (₹)")
        self.tree.heading("stock", text="Stock Available")

        self.tree.column("id", width=60, anchor=tk.CENTER)
        self.tree.column("name", width=320, anchor=tk.W)
        self.tree.column("category", width=220, anchor=tk.W)
        self.tree.column("price", width=90, anchor=tk.E)
        self.tree.column("stock", width=100, anchor=tk.CENTER)

        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.on_item_select)

        # 3. Bottom Form for Add / Update / Delete
        form_frame = ttk.LabelFrame(self, text="Manage Product Details")
        form_frame.pack(fill=tk.X, padx=5, pady=5)

        # Row 0
        ttk.Label(form_frame, text="Product Name:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.name_var, width=35).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Category:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.item_category_var = tk.StringVar()
        self.form_category_combobox = ttk.Combobox(form_frame, textvariable=self.item_category_var, width=28)
        self.form_category_combobox.grid(row=0, column=3, padx=5, pady=5)

        # Row 1
        ttk.Label(form_frame, text="Price (₹):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.price_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.price_var, width=15).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(form_frame, text="Stock Quantity:").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.stock_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.stock_var, width=15).grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)

        # Buttons
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=10)

        ttk.Button(btn_frame, text="Add New Item", command=self.add_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Update Selected", command=self.update_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Selected", command=self.delete_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear Inputs", command=self.clear_form).pack(side=tk.LEFT, padx=5)

    def load_categories(self):
        conn = get_db_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT category FROM inventory ORDER BY category;")
            categories = [row[0] for row in cursor.fetchall()]
            cursor.close()
        except Exception:
            categories = []
        finally:
            if conn.is_connected():
                conn.close()

        self.category_dropdown["values"] = ["All"] + categories
        self.category_dropdown.current(0)
        self.form_category_combobox["values"] = categories

    def load_inventory(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = get_db_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor()

            search_query = self.search_var.get().strip()
            category_filter = self.category_filter_var.get()

            sql = "SELECT item_id, name, category, price, stock_quantity FROM inventory WHERE 1=1"
            params = []

            if search_query:
                sql += " AND name LIKE %s"
                params.append(f"%{search_query}%")

            if category_filter and category_filter != "All":
                sql += " AND category = %s"
                params.append(category_filter)

            sql += " ORDER BY item_id ASC"
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            for item in rows:
                self.tree.insert("", tk.END, values=(item[0], item[1], item[2], f"{item[3]:.2f}", item[4]))

            self.status_var.set(f"Showing {len(rows)} products")
            cursor.close()
        except Exception as e:
            self.status_var.set(f"Error: {e}")
        finally:
            if conn.is_connected():
                conn.close()

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
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add product: {e}")
            return
        finally:
            if conn.is_connected():
                conn.close()

        messagebox.showinfo("Success", f"Product '{name}' added successfully!")
        self.clear_form()
        self.load_categories()
        self.load_inventory()

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
            messagebox.showerror("Validation Error", "Price and stock must be valid positive numbers.")
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
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update product: {e}")
            return
        finally:
            if conn.is_connected():
                conn.close()

        messagebox.showinfo("Success", "Product details updated successfully!")
        self.clear_form()
        self.load_inventory()

    def delete_item(self):
        if not self.selected_item_id:
            messagebox.showwarning("Selection Required", "Please select an item from the list to delete.")
            return

        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to remove this product permanently?\n\nNote: Any past sale records referencing this item may be affected.")
        if not confirm:
            return

        conn = get_db_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            # Delete associated sale_items first to avoid FK constraint violation
            cursor.execute("DELETE FROM sale_items WHERE item_id = %s", (self.selected_item_id,))
            cursor.execute("DELETE FROM inventory WHERE item_id = %s", (self.selected_item_id,))
            conn.commit()
            cursor.close()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete product: {e}")
            return
        finally:
            if conn.is_connected():
                conn.close()

        messagebox.showinfo("Deleted", "Product removed from inventory.")
        self.clear_form()
        self.load_inventory()

    def reset_filters(self):
        self.search_var.set("")
        self.category_filter_var.set("All")
        self.load_inventory()

    def clear_form(self):
        self.selected_item_id = None
        self.name_var.set("")
        self.item_category_var.set("")
        self.price_var.set("")
        self.stock_var.set("")
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection()[0])


# Independent run test
if __name__ == "__main__":
    root = tk.Tk()
    root.title("SnapKart - Inventory Management Panel")
    root.geometry("900x650")
    app = InventoryFrame(root)
    root.mainloop()