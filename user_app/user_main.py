import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from database.db_connection import get_db_connection
from common.store_status import check_store_status


class SnapKartCustomerApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("SnapKart - Your Neighbourhood Store, Online")
        self.geometry("1420x880")
        self.minsize(1220, 750)
        self.configure(bg="#f8fafc")

        # Color Palette
        self.COLOR_GREEN = "#16a34a"        # Primary green
        self.COLOR_GREEN_LIGHT = "#dcfce7"  # Soft green background
        self.COLOR_DARK = "#0f172a"         # Deep navy text
        self.COLOR_MUTED = "#64748b"        # Gray text
        self.COLOR_BORDER = "#e2e8f0"       # Border gray
        self.COLOR_WHITE = "#ffffff"        # Card background
        self.COLOR_RED = "#dc2626"          # Close status red

        # Cart state dictionary: {item_id: {"name": ..., "price": ..., "qty": ..., "max_stock": ...}}
        self.cart = {}
        self.active_category = "All Products"

        # Main Layout Structure
        self.create_top_navbar()
        
        # 3-Column Body Frame
        self.body_frame = tk.Frame(self, bg="#f8fafc")
        self.body_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 10))

        self.create_left_sidebar(self.body_frame)
        self.create_center_catalog(self.body_frame)
        self.create_right_cart_panel(self.body_frame)

        self.create_bottom_footer()

        # Load initial data from MySQL
        self.refresh_store_status()
        self.load_products_from_db()

    # =========================================================================
    # 1. TOP NAVBAR
    # =========================================================================
    def create_top_navbar(self):
        nav = tk.Frame(self, bg=self.COLOR_WHITE, height=65, bd=1, relief=tk.SOLID)
        nav.pack(fill=tk.X, side=tk.TOP)
        nav.pack_propagate(False)

        # Brand Logo on Left
        brand_box = tk.Frame(nav, bg=self.COLOR_WHITE)
        brand_box.pack(side=tk.LEFT, padx=20)

        tk.Label(brand_box, text="🛒 SnapKart", font=("Segoe UI", 16, "bold"), fg=self.COLOR_GREEN, bg=self.COLOR_WHITE).pack(anchor="w")
        tk.Label(brand_box, text="Your Neighbourhood Store, Online", font=("Segoe UI", 7), fg=self.COLOR_MUTED, bg=self.COLOR_WHITE).pack(anchor="w")

        # Middle Navigation Links
        mid_links = tk.Frame(nav, bg=self.COLOR_WHITE)
        mid_links.pack(side=tk.LEFT, padx=30)

        links = ["🏠 Home", "🛍️ Shop", "🏷️ Offers", "📦 Track Order", "❓ Help"]
        for idx, text in enumerate(links):
            fg_col = self.COLOR_GREEN if idx == 0 else self.COLOR_DARK
            font_w = "bold" if idx == 0 else "normal"
            btn = tk.Label(mid_links, text=text, font=("Segoe UI", 9, font_w), fg=fg_col, bg=self.COLOR_WHITE, padx=10, cursor="hand2")
            btn.pack(side=tk.LEFT)

        # Right Side: Location & User Profile
        right_box = tk.Frame(nav, bg=self.COLOR_WHITE)
        right_box.pack(side=tk.RIGHT, padx=20)

        # Location Pill
        loc_box = tk.Frame(right_box, bg="#f1f5f9", padx=10, pady=4, bd=1, relief=tk.SOLID)
        loc_box.pack(side=tk.LEFT, padx=(0, 15))
        tk.Label(loc_box, text="📍 Delivering to LPU, Phagwara ▾", font=("Segoe UI", 8, "bold"), bg="#f1f5f9", fg=self.COLOR_DARK).pack()

        # User Avatar & Name
        tk.Label(right_box, text="👤", font=("Segoe UI", 12), bg=self.COLOR_WHITE).pack(side=tk.LEFT, padx=(0, 5))
        u_info = tk.Frame(right_box, bg=self.COLOR_WHITE)
        u_info.pack(side=tk.LEFT)
        tk.Label(u_info, text="Hello, Guest", font=("Segoe UI", 9, "bold"), fg=self.COLOR_DARK, bg=self.COLOR_WHITE).pack(anchor="w")
        tk.Label(u_info, text="Sign In / Register", font=("Segoe UI", 7), fg=self.COLOR_MUTED, bg=self.COLOR_WHITE).pack(anchor="w")

    # =========================================================================
    # 2. LEFT SIDEBAR: STORE STATUS & CATEGORIES
    # =========================================================================
    def create_left_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg="#f8fafc", width=240)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))
        sidebar.pack_propagate(False)

        # A. Live Store Status Banner
        self.status_card = tk.Frame(sidebar, bg=self.COLOR_WHITE, bd=1, relief=tk.SOLID)
        self.status_card.pack(fill=tk.X, pady=(0, 10), ipady=8)

        self.lbl_store_badge = tk.Label(
            self.status_card, 
            text="🟢 STORE OPEN\nWe are now accepting orders!", 
            font=("Segoe UI", 9, "bold"), 
            bg=self.COLOR_GREEN_LIGHT, 
            fg=self.COLOR_GREEN, 
            padx=10, 
            pady=6, 
            bd=1, 
            relief=tk.SOLID
        )
        self.lbl_store_badge.pack(fill=tk.X, padx=12, pady=(8, 6))

        self.lbl_hours_info = tk.Label(self.status_card, text="🕒 Operating Hours\n09:00 AM – 10:00 PM", font=("Segoe UI", 8), fg=self.COLOR_MUTED, bg=self.COLOR_WHITE)
        self.lbl_hours_info.pack(padx=12, pady=(0, 6))

        # Store Perks
        perks = ["✨ Fresh Products", "⚡ Quick Delivery / Pickup", "🔒 Secure Payments", "💰 Better Prices Everyday"]
        for p in perks:
            tk.Label(self.status_card, text=p, font=("Segoe UI", 7), fg=self.COLOR_MUTED, bg=self.COLOR_WHITE, anchor="w").pack(fill=tk.X, padx=16, pady=1)

        # B. Categories Menu
        cat_box = tk.Frame(sidebar, bg=self.COLOR_WHITE, bd=1, relief=tk.SOLID)
        cat_box.pack(fill=tk.BOTH, expand=True)

        tk.Label(cat_box, text="Categories", font=("Segoe UI", 10, "bold"), fg=self.COLOR_DARK, bg=self.COLOR_WHITE).pack(anchor="w", padx=12, pady=(10, 6))

        # Scrollable categories list
        cat_canvas = tk.Canvas(cat_box, bg=self.COLOR_WHITE, bd=0, highlightthickness=0)
        cat_scroll = ttk.Scrollbar(cat_box, orient="vertical", command=cat_canvas.yview)
        self.cat_inner_frame = tk.Frame(cat_canvas, bg=self.COLOR_WHITE)

        cat_canvas.create_window((0, 0), window=self.cat_inner_frame, anchor="nw")
        self.cat_inner_frame.bind("<Configure>", lambda e: cat_canvas.configure(scrollregion=cat_canvas.bbox("all")))

        cat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))
        cat_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        cat_canvas.configure(yscrollcommand=cat_scroll.set)

        self.load_categories_buttons()

    def load_categories_buttons(self):
        conn = get_db_connection()
        categories = ["All Products"]
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT category FROM inventory ORDER BY category;")
            categories += [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()

        for cat in categories:
            is_active = (cat == self.active_category)
            bg_col = self.COLOR_GREEN_LIGHT if is_active else self.COLOR_WHITE
            fg_col = self.COLOR_GREEN if is_active else self.COLOR_DARK

            btn = tk.Button(
                self.cat_inner_frame,
                text=f"  {cat}",
                font=("Segoe UI", 8, "bold" if is_active else "normal"),
                fg=fg_col,
                bg=bg_col,
                activebackground=self.COLOR_GREEN_LIGHT,
                relief=tk.FLAT,
                anchor="w",
                padx=8,
                pady=5,
                bd=0,
                cursor="hand2",
                command=lambda c=cat: self.select_category(c)
            )
            btn.pack(fill=tk.X, pady=1)

    def select_category(self, category_name):
        self.active_category = category_name
        for widget in self.cat_inner_frame.winfo_children():
            widget.destroy()
        self.load_categories_buttons()
        self.load_products_from_db()

    # =========================================================================
    # 3. CENTER: PROMO BANNER, SEARCH & PRODUCTS GRID
    # =========================================================================
    def create_center_catalog(self, parent):
        center_frame = tk.Frame(parent, bg="#f8fafc")
        center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12))

        # A. Promotional Banner
        banner = tk.Frame(center_frame, bg="#e0f2fe", bd=1, relief=tk.SOLID)
        banner.pack(fill=tk.X, pady=(0, 10), ipady=10)

        b_text_box = tk.Frame(banner, bg="#e0f2fe")
        b_text_box.pack(side=tk.LEFT, padx=20)

        tk.Label(b_text_box, text="FRESHER. FASTER. CLOSER TO YOU.", font=("Segoe UI", 7, "bold"), fg="#0284c7", bg="#e0f2fe").pack(anchor="w")
        tk.Label(b_text_box, text="Everything You Need, Just a Few Clicks Away!", font=("Segoe UI", 14, "bold"), fg="#0f172a", bg="#e0f2fe").pack(anchor="w", pady=(2, 2))
        tk.Label(b_text_box, text="Groceries | Dairy | Snacks | Beverages | Health | Tech & Essentials", font=("Segoe UI", 8), fg="#475569", bg="#e0f2fe").pack(anchor="w")

        # B. Search Bar
        search_box = tk.Frame(center_frame, bg=self.COLOR_WHITE, bd=1, relief=tk.SOLID)
        search_box.pack(fill=tk.X, pady=(0, 10), ipady=4)

        tk.Label(search_box, text="  🔍  ", bg=self.COLOR_WHITE, fg=self.COLOR_MUTED).pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_box, font=("Segoe UI", 9), bg=self.COLOR_WHITE, bd=0, fg=self.COLOR_DARK)
        self.search_entry.insert(0, "Search for products (e.g. milk, bread, rice, coffee...)")
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_products_from_db())

        btn_search = tk.Button(
            search_box, 
            text="Search", 
            font=("Segoe UI", 8, "bold"), 
            bg=self.COLOR_GREEN, 
            fg="#ffffff", 
            relief=tk.FLAT, 
            padx=16, 
            command=self.load_products_from_db
        )
        btn_search.pack(side=tk.RIGHT, padx=5)

        # C. Products Grid (Scrollable)
        grid_container = tk.Frame(center_frame, bg="#f8fafc")
        grid_container.pack(fill=tk.BOTH, expand=True)

        self.grid_canvas = tk.Canvas(grid_container, bg="#f8fafc", bd=0, highlightthickness=0)
        grid_scroll = ttk.Scrollbar(grid_container, orient="vertical", command=self.grid_canvas.yview)

        self.cards_frame = tk.Frame(self.grid_canvas, bg="#f8fafc")
        self.cards_frame.bind("<Configure>", lambda e: self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox("all")))

        self.grid_canvas.create_window((0, 0), window=self.cards_frame, anchor="nw")
        self.grid_canvas.configure(yscrollcommand=grid_scroll.set)

        self.grid_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        grid_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def load_products_from_db(self):
        # Clear existing cards
        for w in self.cards_frame.winfo_children():
            w.destroy()

        conn = get_db_connection()
        if not conn:
            return

        cursor = conn.cursor(dictionary=True)
        search_txt = self.search_entry.get().strip()
        if search_txt == "Search for products (e.g. milk, bread, rice, coffee...)":
            search_txt = ""

        query = "SELECT item_id, name, category, price, stock_quantity FROM inventory WHERE stock_quantity > 0"
        params = []

        if self.active_category != "All Products":
            query += " AND category = %s"
            params.append(self.active_category)

        if search_txt:
            query += " AND name LIKE %s"
            params.append(f"%{search_txt}%")

        query += " ORDER BY item_id ASC LIMIT 24;"
        cursor.execute(query, params)
        products = cursor.fetchall()
        cursor.close()
        conn.close()

        # Render cards in 3 columns
        num_cols = 3
        for idx, prod in enumerate(products):
            row = idx // num_cols
            col = idx % num_cols
            self.create_single_product_card(self.cards_frame, prod, row, col)

    def create_single_product_card(self, parent, prod, r, c):
        card = tk.Frame(parent, bg=self.COLOR_WHITE, bd=1, relief=tk.SOLID, width=220, height=210)
        card.grid(row=r, column=c, padx=6, pady=6, sticky="nsew")
        card.grid_propagate(False)

        # Top Badge & Category
        top_row = tk.Frame(card, bg=self.COLOR_WHITE)
        top_row.pack(fill=tk.X, padx=8, pady=(6, 2))

        tk.Label(top_row, text="Bestseller", font=("Segoe UI", 7, "bold"), bg="#fee2e2", fg="#dc2626", padx=4, pady=1).pack(side=tk.LEFT)
        tk.Label(top_row, text=f"Stock: {prod['stock_quantity']}", font=("Segoe UI", 7), fg=self.COLOR_MUTED, bg=self.COLOR_WHITE).pack(side=tk.RIGHT)

        # Product Title
        name_lbl = tk.Label(
            card, 
            text=prod["name"], 
            font=("Segoe UI", 9, "bold"), 
            fg=self.COLOR_DARK, 
            bg=self.COLOR_WHITE, 
            wraplength=200, 
            justify="left"
        )
        name_lbl.pack(anchor="w", padx=8, pady=(8, 2))

        # Category
        tk.Label(card, text=prod["category"], font=("Segoe UI", 7), fg=self.COLOR_MUTED, bg=self.COLOR_WHITE).pack(anchor="w", padx=8)

        # Price and Add Button at Bottom
        bot_row = tk.Frame(card, bg=self.COLOR_WHITE)
        bot_row.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=8)

        tk.Label(bot_row, text=f"₹ {float(prod['price']):.2f}", font=("Segoe UI", 11, "bold"), fg=self.COLOR_DARK, bg=self.COLOR_WHITE).pack(side=tk.LEFT)

        btn_add = tk.Button(
            bot_row,
            text="🛒 Add",
            font=("Segoe UI", 8, "bold"),
            bg=self.COLOR_GREEN_LIGHT,
            fg=self.COLOR_GREEN,
            activebackground=self.COLOR_GREEN,
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=10,
            cursor="hand2",
            command=lambda p=prod: self.add_to_cart(p)
        )
        btn_add.pack(side=tk.RIGHT)

    # =========================================================================
    # 4. RIGHT SIDEBAR: INTERACTIVE CART & CHECKOUT
    # =========================================================================
    def create_right_cart_panel(self, parent):
        self.cart_panel = tk.Frame(parent, bg=self.COLOR_WHITE, width=320, bd=1, relief=tk.SOLID)
        self.cart_panel.pack(side=tk.RIGHT, fill=tk.Y)
        self.cart_panel.pack_propagate(False)

        # Cart Header
        head = tk.Frame(self.cart_panel, bg=self.COLOR_WHITE)
        head.pack(fill=tk.X, padx=14, pady=(12, 8))

        self.lbl_cart_title = tk.Label(head, text="Your Cart (0)", font=("Segoe UI", 11, "bold"), fg=self.COLOR_DARK, bg=self.COLOR_WHITE)
        self.lbl_cart_title.pack(side=tk.LEFT)

        tk.Button(head, text="Clear All", font=("Segoe UI", 8), fg="#dc2626", bg=self.COLOR_WHITE, bd=0, cursor="hand2", command=self.clear_cart).pack(side=tk.RIGHT)

        # Cart Items List (Scrollable)
        items_box = tk.Frame(self.cart_panel, bg=self.COLOR_WHITE)
        items_box.pack(fill=tk.BOTH, expand=True, padx=8)

        self.cart_canvas = tk.Canvas(items_box, bg=self.COLOR_WHITE, bd=0, highlightthickness=0)
        c_scroll = ttk.Scrollbar(items_box, orient="vertical", command=self.cart_canvas.yview)

        self.cart_items_frame = tk.Frame(self.cart_canvas, bg=self.COLOR_WHITE)
        self.cart_items_frame.bind("<Configure>", lambda e: self.cart_canvas.configure(scrollregion=self.cart_canvas.bbox("all")))

        self.cart_canvas.create_window((0, 0), window=self.cart_items_frame, anchor="nw")
        self.cart_canvas.configure(yscrollcommand=c_scroll.set)

        self.cart_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        c_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Bill Summary Box
        summary_box = tk.Frame(self.cart_panel, bg="#f8fafc", bd=1, relief=tk.SOLID)
        summary_box.pack(fill=tk.X, padx=12, pady=(4, 8), ipady=6)

        self.lbl_subtotal = self.make_summary_row(summary_box, "Subtotal", "₹ 0.00")
        self.lbl_delivery = self.make_summary_row(summary_box, "Delivery Charge", "₹ 20.00")
        self.lbl_total = self.make_summary_row(summary_box, "Total Amount", "₹ 0.00", is_total=True)

        # Proceed to Checkout Button
        self.btn_checkout = tk.Button(
            self.cart_panel,
            text="Proceed to Checkout ➔",
            font=("Segoe UI", 10, "bold"),
            bg=self.COLOR_GREEN,
            fg="#ffffff",
            activebackground="#15803d",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.process_order_checkout
        )
        self.btn_checkout.pack(fill=tk.X, padx=14, pady=(0, 10), ipady=6)

    def make_summary_row(self, parent, label_text, val_text, is_total=False):
        row = tk.Frame(parent, bg="#f8fafc")
        row.pack(fill=tk.X, padx=10, pady=2)

        font_w = "bold" if is_total else "normal"
        size = 10 if is_total else 8
        fg_col = self.COLOR_GREEN if is_total else self.COLOR_DARK

        tk.Label(row, text=label_text, font=("Segoe UI", size, font_w), bg="#f8fafc", fg=self.COLOR_DARK).pack(side=tk.LEFT)
        val_lbl = tk.Label(row, text=val_text, font=("Segoe UI", size, "bold"), bg="#f8fafc", fg=fg_col)
        val_lbl.pack(side=tk.RIGHT)
        return val_lbl

    # =========================================================================
    # 5. CART INTERACTION LOGIC
    # =========================================================================
    def add_to_cart(self, prod):
        p_id = prod["item_id"]
        if p_id in self.cart:
            if self.cart[p_id]["qty"] < prod["stock_quantity"]:
                self.cart[p_id]["qty"] += 1
            else:
                messagebox.showwarning("Stock Limit", f"Only {prod['stock_quantity']} units available!")
                return
        else:
            self.cart[p_id] = {
                "name": prod["name"],
                "price": float(prod["price"]),
                "qty": 1,
                "max_stock": prod["stock_quantity"]
            }
        self.render_cart()

    def update_cart_qty(self, p_id, change):
        if p_id in self.cart:
            new_qty = self.cart[p_id]["qty"] + change
            if new_qty <= 0:
                del self.cart[p_id]
            elif new_qty > self.cart[p_id]["max_stock"]:
                messagebox.showwarning("Limit Reached", "Cannot exceed available warehouse stock.")
                return
            else:
                self.cart[p_id]["qty"] = new_qty
        self.render_cart()

    def remove_from_cart(self, p_id):
        if p_id in self.cart:
            del self.cart[p_id]
        self.render_cart()

    def clear_cart(self):
        self.cart.clear()
        self.render_cart()

    def render_cart(self):
        for w in self.cart_items_frame.winfo_children():
            w.destroy()

        subtotal = 0.0
        total_items_count = 0

        for p_id, item in self.cart.items():
            total_items_count += item["qty"]
            item_sub = item["price"] * item["qty"]
            subtotal += item_sub

            # Cart Item Card
            c_row = tk.Frame(self.cart_items_frame, bg="#f8fafc", bd=1, relief=tk.SOLID)
            c_row.pack(fill=tk.X, pady=3, padx=2, ipady=4)

            # Title & Price
            info_box = tk.Frame(c_row, bg="#f8fafc")
            info_box.pack(fill=tk.X, padx=6, pady=2)

            tk.Label(info_box, text=item["name"], font=("Segoe UI", 8, "bold"), fg=self.COLOR_DARK, bg="#f8fafc", wraplength=180, justify="left").pack(anchor="w")
            tk.Label(info_box, text=f"₹{item['price']:.2f} × {item['qty']} = ₹{item_sub:.2f}", font=("Segoe UI", 7), fg=self.COLOR_MUTED, bg="#f8fafc").pack(anchor="w")

            # Controls: [-] [qty] [+] [delete]
            ctrl_box = tk.Frame(c_row, bg="#f8fafc")
            ctrl_box.pack(fill=tk.X, padx=6, pady=2)

            tk.Button(ctrl_box, text=" - ", font=("Segoe UI", 7, "bold"), bg="#e2e8f0", bd=0, command=lambda pid=p_id: self.update_cart_qty(pid, -1)).pack(side=tk.LEFT)
            tk.Label(ctrl_box, text=f" {item['qty']} ", font=("Segoe UI", 8, "bold"), bg="#f8fafc").pack(side=tk.LEFT)
            tk.Button(ctrl_box, text=" + ", font=("Segoe UI", 7, "bold"), bg="#e2e8f0", bd=0, command=lambda pid=p_id: self.update_cart_qty(pid, 1)).pack(side=tk.LEFT)

            tk.Button(ctrl_box, text="🗑️", font=("Segoe UI", 8), fg="#dc2626", bg="#f8fafc", bd=0, cursor="hand2", command=lambda pid=p_id: self.remove_from_cart(pid)).pack(side=tk.RIGHT)

        delivery_fee = 20.0 if self.cart else 0.0
        total_bill = subtotal + delivery_fee

        self.lbl_cart_title.config(text=f"Your Cart ({total_items_count})")
        self.lbl_subtotal.config(text=f"₹ {subtotal:,.2f}")
        self.lbl_delivery.config(text=f"₹ {delivery_fee:.2f}")
        self.lbl_total.config(text=f"₹ {total_bill:,.2f}")

    # =========================================================================
    # 6. BUSINESS-HOURS-AWARE CHECKOUT ENGINE
    # =========================================================================
    def refresh_store_status(self):
        is_open, msg = check_store_status()
        if is_open:
            self.lbl_store_badge.config(
                text="🟢 STORE OPEN\nWe are now accepting orders!", 
                fg=self.COLOR_GREEN, 
                bg=self.COLOR_GREEN_LIGHT
            )
            self.btn_checkout.config(state=tk.NORMAL, bg=self.COLOR_GREEN, text="Proceed to Checkout ➔")
        else:
            self.lbl_store_badge.config(
                text="🔴 STORE CLOSED\nTransactions locked outside hours!", 
                fg=self.COLOR_RED, 
                bg="#fee2e2"
            )
            self.btn_checkout.config(state=tk.DISABLED, bg="#94a3b8", text="⛔ Store is Closed")

    def process_order_checkout(self):
        # 1. Real-time Gatekeeper Check
        is_open, status_msg = check_store_status()
        if not is_open:
            messagebox.showerror(
                "Transaction Locked", 
                f"Order cannot be placed!\n\n{status_msg}\nTransactions are restricted to business hours only."
            )
            self.refresh_store_status()
            return

        if not self.cart:
            messagebox.showwarning("Empty Cart", "Your cart is empty. Add products before checkout!")
            return

        # 2. Confirm checkout with total
        subtotal = sum(i["price"] * i["qty"] for i in self.cart.values())
        total_bill = subtotal + 20.0

        confirm = messagebox.askyesno(
            "Confirm Order", 
            f"Total Payable Amount: ₹ {total_bill:,.2f}\n(Includes ₹20 Delivery/Packaging Fee)\n\nDo you want to confirm this order?"
        )
        if not confirm:
            return

        # 3. Deduct stock and write to MySQL
        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Error", "Could not connect to MySQL database.")
            return

        try:
            cursor = conn.cursor()

            # Insert Sale
            now = datetime.now()
            cursor.execute(
                "INSERT INTO sales (sale_datetime, total_amount, payment_method) VALUES (%s, %s, %s)",
                (now, total_bill, "UPI")
            )
            sale_id = cursor.lastrowid

            # Insert Sale Items & Deduct Inventory
            for p_id, item in self.cart.items():
                item_subtotal = item["price"] * item["qty"]
                cursor.execute(
                    "INSERT INTO sale_items (sale_id, item_id, quantity, unit_price, subtotal) VALUES (%s, %s, %s, %s, %s)",
                    (sale_id, p_id, item["qty"], item["price"], item_subtotal)
                )
                cursor.execute(
                    "UPDATE inventory SET stock_quantity = stock_quantity - %s WHERE item_id = %s",
                    (item["qty"], p_id)
                )

            conn.commit()
            cursor.close()
            conn.close()

            messagebox.showinfo(
                "Order Successful! 🎉", 
                f"Thank you for shopping with SnapKart!\n\nInvoice Number: #{sale_id}\nAmount Paid: ₹ {total_bill:,.2f}\n\nEstimated Delivery: 20-30 mins"
            )

            # Clear cart and refresh product stock numbers
            self.clear_cart()
            self.load_products_from_db()

        except Exception as e:
            messagebox.showerror("Checkout Error", f"Failed to complete transaction: {e}")

    # =========================================================================
    # 7. FOOTER
    # =========================================================================
    def create_bottom_footer(self):
        footer = tk.Frame(self, bg=self.COLOR_WHITE, height=36, bd=1, relief=tk.SOLID)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)

        perks_text = "🛡️ Quality Products • 🚚 On-Time Delivery • 💳 Secure Payments • 🎧 24/7 Support"
        tk.Label(footer, text=perks_text, font=("Segoe UI", 8), fg=self.COLOR_MUTED, bg=self.COLOR_WHITE).pack(side=tk.LEFT, padx=20)
        tk.Label(footer, text="Thank you for supporting local! ❤️", font=("Segoe UI", 8, "italic"), fg=self.COLOR_MUTED, bg=self.COLOR_WHITE).pack(side=tk.RIGHT, padx=20)


if __name__ == "__main__":
    app = SnapKartCustomerApp()
    app.mainloop()