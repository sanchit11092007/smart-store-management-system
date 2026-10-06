import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from database.db_connection import get_db_connection
from common.store_status import check_store_status
from common.utils import format_receipt, save_receipt_file
from common.image_loader import get_product_image
from user_app.auth_ui import AuthDialog


class SnapKartCustomerApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("SnapKart - Your Neighbourhood Store, Online")
        self.geometry("1420x890")
        self.minsize(1220, 750)
        self.configure(bg="#f8fafc")

        # Color theme
        self.COLOR_GREEN = "#16a34a"
        self.COLOR_GREEN_LIGHT = "#dcfce7"
        self.COLOR_DARK = "#0f172a"
        self.COLOR_MUTED = "#64748b"
        self.COLOR_WHITE = "#ffffff"
        self.COLOR_RED = "#dc2626"

        # App State
        self.current_user = None
        self.cart = {}
        self.active_category = "All Products"
        self.sort_option = tk.StringVar(value="Popularity")
        self.image_cache = {}  # Keeps image references alive in memory

        # Build UI
        self.create_top_navbar()

        self.body_frame = tk.Frame(self, bg="#f8fafc")
        self.body_frame.pack(fill=tk.BOTH, expand=True, padx=18, pady=(8, 8))

        self.create_left_sidebar(self.body_frame)
        self.create_center_catalog(self.body_frame)
        self.create_right_cart_panel(self.body_frame)

        self.create_bottom_footer()

        # Start live checks
        self.refresh_store_status()
        self.load_products_from_db()

    # ==================== 1. TOP NAVBAR ====================
    def create_top_navbar(self):
        nav = tk.Frame(self, bg=self.COLOR_WHITE, height=64, bd=1, relief=tk.SOLID)
        nav.pack(fill=tk.X, side=tk.TOP)
        nav.pack_propagate(False)

        brand_box = tk.Frame(nav, bg=self.COLOR_WHITE)
        brand_box.pack(side=tk.LEFT, padx=18)
        tk.Label(brand_box, text="🛒 SnapKart", font=("Segoe UI", 16, "bold"), fg=self.COLOR_GREEN, bg=self.COLOR_WHITE).pack(anchor="w")
        tk.Label(brand_box, text="Your Neighbourhood Store, Online", font=("Segoe UI", 7), fg=self.COLOR_MUTED, bg=self.COLOR_WHITE).pack(anchor="w")

        mid_links = tk.Frame(nav, bg=self.COLOR_WHITE)
        mid_links.pack(side=tk.LEFT, padx=25)
        for idx, text in enumerate(["🏠 Home", "🛍️ Shop", "🏷️ Offers", "📦 Track Order", "❓ Help"]):
            fg_col = self.COLOR_GREEN if idx == 0 else self.COLOR_DARK
            tk.Label(mid_links, text=text, font=("Segoe UI", 9, "bold" if idx == 0 else "normal"), fg=fg_col, bg=self.COLOR_WHITE, padx=8, cursor="hand2").pack(side=tk.LEFT)

        right_box = tk.Frame(nav, bg=self.COLOR_WHITE)
        right_box.pack(side=tk.RIGHT, padx=18)

        loc_box = tk.Frame(right_box, bg="#f1f5f9", padx=10, pady=4, bd=1, relief=tk.SOLID)
        loc_box.pack(side=tk.LEFT, padx=(0, 15))
        tk.Label(loc_box, text="📍 Delivering to Sanjay Place, Agra ▾", font=("Segoe UI", 8, "bold"), bg="#f1f5f9", fg=self.COLOR_DARK).pack()

        tk.Label(right_box, text="👤", font=("Segoe UI", 13), bg=self.COLOR_WHITE).pack(side=tk.LEFT, padx=(0, 5))
        self.profile_info_frame = tk.Frame(right_box, bg=self.COLOR_WHITE)
        self.profile_info_frame.pack(side=tk.LEFT)

        self.lbl_user_name = tk.Label(self.profile_info_frame, text="Hello, Guest", font=("Segoe UI", 9, "bold"), fg=self.COLOR_DARK, bg=self.COLOR_WHITE)
        self.lbl_user_name.pack(anchor="w")

        self.lbl_user_action = tk.Label(self.profile_info_frame, text="Sign In / Register", font=("Segoe UI", 8), fg="#2563eb", bg=self.COLOR_WHITE, cursor="hand2")
        self.lbl_user_action.pack(anchor="w")
        self.lbl_user_action.bind("<Button-1>", self.handle_user_auth_click)

    def handle_user_auth_click(self, event=None):
        if self.current_user is None:
            AuthDialog(self, on_login_success=self.on_user_logged_in)
        else:
            if messagebox.askyesno("Log Out", f"Log out from account {self.current_user['full_name']}?"):
                self.current_user = None
                self.lbl_user_name.config(text="Hello, Guest")
                self.lbl_user_action.config(text="Sign In / Register", fg="#2563eb")
                messagebox.showinfo("Logged Out", "You have logged out successfully.")

    def on_user_logged_in(self, user_data):
        self.current_user = user_data
        first_name = user_data["full_name"].split()[0]
        self.lbl_user_name.config(text=f"Hello, {first_name} 👋")
        self.lbl_user_action.config(text="Log Out", fg=self.COLOR_RED)

    # ==================== 2. LEFT SIDEBAR ====================
    def create_left_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg="#f8fafc", width=235)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        sidebar.pack_propagate(False)

        # Store Status Card
        self.status_card = tk.Frame(sidebar, bg=self.COLOR_WHITE, bd=1, relief=tk.SOLID)
        self.status_card.pack(fill=tk.X, pady=(0, 10), ipady=6)

        self.lbl_store_badge = tk.Label(
            self.status_card,
            text="🟢 STORE OPEN\nAccepting orders now!",
            font=("Segoe UI", 9, "bold"),
            bg=self.COLOR_GREEN_LIGHT,
            fg=self.COLOR_GREEN,
            padx=8,
            pady=6,
            bd=1,
            relief=tk.SOLID
        )
        self.lbl_store_badge.pack(fill=tk.X, padx=10, pady=(6, 4))

        self.lbl_hours_info = tk.Label(self.status_card, text="🕒 Operating Hours\n09:00 AM – 10:00 PM", font=("Segoe UI", 8), fg=self.COLOR_MUTED, bg=self.COLOR_WHITE)
        self.lbl_hours_info.pack(padx=10, pady=(0, 4))

        for perk in ["✨ Fresh Products", "⚡ Quick Delivery", "🔒 Secure Payments", "💰 Best Daily Prices"]:
            tk.Label(self.status_card, text=perk, font=("Segoe UI", 7), fg=self.COLOR_MUTED, bg=self.COLOR_WHITE, anchor="w").pack(fill=tk.X, padx=14, pady=1)

        # Categories Card
        cat_box = tk.Frame(sidebar, bg=self.COLOR_WHITE, bd=1, relief=tk.SOLID)
        cat_box.pack(fill=tk.BOTH, expand=True)

        tk.Label(cat_box, text="Categories", font=("Segoe UI", 10, "bold"), fg=self.COLOR_DARK, bg=self.COLOR_WHITE).pack(anchor="w", padx=10, pady=(8, 4))

        cat_canvas = tk.Canvas(cat_box, bg=self.COLOR_WHITE, bd=0, highlightthickness=0)
        cat_scroll = ttk.Scrollbar(cat_box, orient="vertical", command=cat_canvas.yview)
        self.cat_inner = tk.Frame(cat_canvas, bg=self.COLOR_WHITE)

        cat_canvas.create_window((0, 0), window=self.cat_inner, anchor="nw")
        self.cat_inner.bind("<Configure>", lambda e: cat_canvas.configure(scrollregion=cat_canvas.bbox("all")))

        cat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(2, 0))
        cat_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        cat_canvas.configure(yscrollcommand=cat_scroll.set)

        self.load_categories()

    def load_categories(self):
        for w in self.cat_inner.winfo_children():
            w.destroy()

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
                self.cat_inner,
                text=f"  {cat}",
                font=("Segoe UI", 8, "bold" if is_active else "normal"),
                fg=fg_col,
                bg=bg_col,
                relief=tk.FLAT,
                anchor="w",
                padx=8,
                pady=4,
                cursor="hand2",
                command=lambda c=cat: self.select_category(c)
            )
            btn.pack(fill=tk.X, pady=1)

    def select_category(self, cat):
        self.active_category = cat
        self.load_categories()
        self.load_products_from_db()

    # ==================== 3. CENTER CATALOG ====================
    def create_center_catalog(self, parent):
        center = tk.Frame(parent, bg="#f8fafc")
        center.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Promo Banner
        banner = tk.Frame(center, bg="#e0f2fe", bd=1, relief=tk.SOLID)
        banner.pack(fill=tk.X, pady=(0, 8), ipady=6)

        b_text = tk.Frame(banner, bg="#e0f2fe")
        b_text.pack(side=tk.LEFT, padx=16)
        tk.Label(b_text, text="FRESHER. FASTER. CLOSER TO YOU.", font=("Segoe UI", 7, "bold"), fg="#0284c7", bg="#e0f2fe").pack(anchor="w")
        tk.Label(b_text, text="Everything You Need, Just a Few Clicks Away!", font=("Segoe UI", 12, "bold"), fg="#0f172a", bg="#e0f2fe").pack(anchor="w")

        # Search Bar + Sort Dropdown Row
        top_filter_row = tk.Frame(center, bg="#f8fafc")
        top_filter_row.pack(fill=tk.X, pady=(0, 8))

        # Search box
        search_box = tk.Frame(top_filter_row, bg=self.COLOR_WHITE, bd=1, relief=tk.SOLID)
        search_box.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)

        tk.Label(search_box, text=" 🔍 ", bg=self.COLOR_WHITE, fg=self.COLOR_MUTED).pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_box, font=("Segoe UI", 9), bg=self.COLOR_WHITE, bd=0, fg=self.COLOR_DARK)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_products_from_db())

        tk.Button(search_box, text="Clear", font=("Segoe UI", 7), bg="#e2e8f0", bd=0, command=self.clear_search).pack(side=tk.RIGHT, padx=4)

        # Sort Dropdown
        sort_frame = tk.Frame(top_filter_row, bg="#f8fafc")
        sort_frame.pack(side=tk.RIGHT, padx=(10, 0))
        tk.Label(sort_frame, text="Sort by: ", font=("Segoe UI", 8), bg="#f8fafc", fg=self.COLOR_MUTED).pack(side=tk.LEFT)

        sort_cb = ttk.Combobox(
            sort_frame,
            textvariable=self.sort_option,
            values=["Popularity", "Price: Low to High", "Price: High to Low"],
            state="readonly",
            width=16
        )
        sort_cb.pack(side=tk.LEFT)
        sort_cb.bind("<<ComboboxSelected>>", lambda e: self.load_products_from_db())

        # Scrollable Product Cards
        grid_container = tk.Frame(center, bg="#f8fafc")
        grid_container.pack(fill=tk.BOTH, expand=True)

        self.grid_canvas = tk.Canvas(grid_container, bg="#f8fafc", bd=0, highlightthickness=0)
        grid_scroll = ttk.Scrollbar(grid_container, orient="vertical", command=self.grid_canvas.yview)

        self.cards_frame = tk.Frame(self.grid_canvas, bg="#f8fafc")
        self.cards_frame.bind("<Configure>", lambda e: self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox("all")))

        self.grid_canvas.create_window((0, 0), window=self.cards_frame, anchor="nw")
        self.grid_canvas.configure(yscrollcommand=grid_scroll.set)

        self.grid_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        grid_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def clear_search(self):
        self.search_entry.delete(0, tk.END)
        self.load_products_from_db()

    def load_products_from_db(self):
        for w in self.cards_frame.winfo_children():
            w.destroy()

        conn = get_db_connection()
        if not conn:
            return

        cursor = conn.cursor(dictionary=True)
        search_txt = self.search_entry.get().strip()

        query = "SELECT item_id, name, category, price, stock_quantity FROM inventory WHERE stock_quantity > 0"
        params = []

        if self.active_category != "All Products":
            query += " AND category = %s"
            params.append(self.active_category)

        if search_txt:
            query += " AND name LIKE %s"
            params.append(f"%{search_txt}%")

        # Sorting
        sort_mode = self.sort_option.get()
        if sort_mode == "Price: Low to High":
            query += " ORDER BY price ASC"
        elif sort_mode == "Price: High to Low":
            query += " ORDER BY price DESC"
        else:
            query += " ORDER BY item_id ASC"

        query += " LIMIT 30;"
        cursor.execute(query, params)
        products = cursor.fetchall()
        cursor.close()
        conn.close()

        # Render 3 items per row
        for idx, prod in enumerate(products):
            r = idx // 3
            c = idx % 3
            self.create_single_product_card(self.cards_frame, prod, r, c)

    def create_single_product_card(self, parent, prod, r, c):
        card = tk.Frame(parent, bg=self.COLOR_WHITE, bd=1, relief=tk.SOLID, width=225, height=265)
        card.grid(row=r, column=c, padx=6, pady=6, sticky="nsew")
        card.grid_propagate(False)

        # 1. Product Image at Top
        p_id = prod["item_id"]
        # Save image to self.image_cache so Python does NOT delete it
        photo = get_product_image(p_id, prod["name"], prod["category"], size=(210, 105))
        self.image_cache[p_id] = photo

        img_label = tk.Label(card, image=photo, bg=self.COLOR_WHITE)
        img_label.pack(fill=tk.X, padx=5, pady=(5, 3))

        # 2. Tag and Stock Row
        tag_row = tk.Frame(card, bg=self.COLOR_WHITE)
        tag_row.pack(fill=tk.X, padx=8, pady=(2, 2))
        tk.Label(tag_row, text="Bestseller", font=("Segoe UI", 7, "bold"), bg="#fee2e2", fg="#dc2626", padx=4).pack(side=tk.LEFT)
        tk.Label(tag_row, text=f"Stock: {prod['stock_quantity']}", font=("Segoe UI", 7), fg=self.COLOR_MUTED, bg=self.COLOR_WHITE).pack(side=tk.RIGHT)

        # 3. Product Name & Category
        name_lbl = tk.Label(card, text=prod["name"], font=("Segoe UI", 9, "bold"), fg=self.COLOR_DARK, bg=self.COLOR_WHITE, wraplength=205, justify="left")
        name_lbl.pack(anchor="w", padx=8, pady=(4, 0))

        cat_lbl = tk.Label(card, text=prod["category"], font=("Segoe UI", 7), fg=self.COLOR_MUTED, bg=self.COLOR_WHITE)
        cat_lbl.pack(anchor="w", padx=8)

        # 4. Price & Add to Cart Button
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

    # ==================== 4. RIGHT CART PANEL ====================
    def create_right_cart_panel(self, parent):
        self.cart_panel = tk.Frame(parent, bg=self.COLOR_WHITE, width=320, bd=1, relief=tk.SOLID)
        self.cart_panel.pack(side=tk.RIGHT, fill=tk.Y)
        self.cart_panel.pack_propagate(False)

        head = tk.Frame(self.cart_panel, bg=self.COLOR_WHITE)
        head.pack(fill=tk.X, padx=12, pady=(10, 6))

        self.lbl_cart_title = tk.Label(head, text="Your Cart (0)", font=("Segoe UI", 11, "bold"), fg=self.COLOR_DARK, bg=self.COLOR_WHITE)
        self.lbl_cart_title.pack(side=tk.LEFT)

        tk.Button(head, text="Clear All", font=("Segoe UI", 8), fg="#dc2626", bg=self.COLOR_WHITE, bd=0, cursor="hand2", command=self.clear_cart).pack(side=tk.RIGHT)

        items_box = tk.Frame(self.cart_panel, bg=self.COLOR_WHITE)
        items_box.pack(fill=tk.BOTH, expand=True, padx=6)

        self.cart_canvas = tk.Canvas(items_box, bg=self.COLOR_WHITE, bd=0, highlightthickness=0)
        c_scroll = ttk.Scrollbar(items_box, orient="vertical", command=self.cart_canvas.yview)

        self.cart_items_frame = tk.Frame(self.cart_canvas, bg=self.COLOR_WHITE)
        self.cart_items_frame.bind("<Configure>", lambda e: self.cart_canvas.configure(scrollregion=self.cart_canvas.bbox("all")))

        self.cart_canvas.create_window((0, 0), window=self.cart_items_frame, anchor="nw")
        self.cart_canvas.configure(yscrollcommand=c_scroll.set)

        self.cart_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        c_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        summary_box = tk.Frame(self.cart_panel, bg="#f8fafc", bd=1, relief=tk.SOLID)
        summary_box.pack(fill=tk.X, padx=10, pady=(4, 6), ipady=4)

        self.lbl_subtotal = self.make_summary_row(summary_box, "Subtotal", "₹ 0.00")
        self.lbl_delivery = self.make_summary_row(summary_box, "Delivery Charge", "₹ 20.00")
        self.lbl_total = self.make_summary_row(summary_box, "Total Amount", "₹ 0.00", is_total=True)

        self.btn_checkout = tk.Button(
            self.cart_panel,
            text="Proceed to Checkout ➔",
            font=("Segoe UI", 10, "bold"),
            bg=self.COLOR_GREEN,
            fg="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.process_order_checkout
        )
        self.btn_checkout.pack(fill=tk.X, padx=12, pady=(0, 8), ipady=6)

    def make_summary_row(self, parent, label_text, val_text, is_total=False):
        row = tk.Frame(parent, bg="#f8fafc")
        row.pack(fill=tk.X, padx=8, pady=1)
        font_w = "bold" if is_total else "normal"
        size = 10 if is_total else 8
        fg_col = self.COLOR_GREEN if is_total else self.COLOR_DARK
        tk.Label(row, text=label_text, font=("Segoe UI", size, font_w), bg="#f8fafc", fg=self.COLOR_DARK).pack(side=tk.LEFT)
        val_lbl = tk.Label(row, text=val_text, font=("Segoe UI", size, "bold"), bg="#f8fafc", fg=fg_col)
        val_lbl.pack(side=tk.RIGHT)
        return val_lbl

    def add_to_cart(self, prod):
        p_id = prod["item_id"]
        if p_id in self.cart:
            if self.cart[p_id]["qty"] < prod["stock_quantity"]:
                self.cart[p_id]["qty"] += 1
            else:
                messagebox.showwarning("Stock Limit", f"Only {prod['stock_quantity']} units in store!")
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
                messagebox.showwarning("Stock Limit", "Cannot order more than available stock.")
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

            c_row = tk.Frame(self.cart_items_frame, bg="#f8fafc", bd=1, relief=tk.SOLID)
            c_row.pack(fill=tk.X, pady=2, padx=2, ipady=3)

            info_box = tk.Frame(c_row, bg="#f8fafc")
            info_box.pack(fill=tk.X, padx=5, pady=1)
            tk.Label(info_box, text=item["name"], font=("Segoe UI", 8, "bold"), fg=self.COLOR_DARK, bg="#f8fafc", wraplength=180, justify="left").pack(anchor="w")
            tk.Label(info_box, text=f"₹{item['price']:.2f} × {item['qty']} = ₹{item_sub:.2f}", font=("Segoe UI", 7), fg=self.COLOR_MUTED, bg="#f8fafc").pack(anchor="w")

            ctrl_box = tk.Frame(c_row, bg="#f8fafc")
            ctrl_box.pack(fill=tk.X, padx=5, pady=2)
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

    # ==================== 5. CHECKOUT ENGINE ====================
    def refresh_store_status(self):
        is_open, msg = check_store_status()
        if is_open:
            self.lbl_store_badge.config(text="🟢 STORE OPEN\nAccepting orders now!", fg=self.COLOR_GREEN, bg=self.COLOR_GREEN_LIGHT)
            self.btn_checkout.config(state=tk.NORMAL, bg=self.COLOR_GREEN, text="Proceed to Checkout ➔")
        else:
            self.lbl_store_badge.config(text="🔴 STORE CLOSED\nTransactions locked!", fg=self.COLOR_RED, bg="#fee2e2")
            self.btn_checkout.config(state=tk.DISABLED, bg="#94a3b8", text="⛔ Store is Closed")

    def process_order_checkout(self):
        is_open, status_msg = check_store_status()
        if not is_open:
            messagebox.showerror("Transaction Locked", f"Store is currently closed!\n\n{status_msg}")
            self.refresh_store_status()
            return

        if not self.cart:
            messagebox.showwarning("Empty Cart", "Your cart is empty!")
            return

        # Recommend Login for guests
        if self.current_user is None:
            if messagebox.askyesno("Sign In Recommended", "You are checking out as Guest.\n\nWould you like to Log In or Sign Up first?"):
                AuthDialog(self, on_login_success=self.on_user_logged_in)
                return

        subtotal = sum(i["price"] * i["qty"] for i in self.cart.values())
        total_bill = subtotal + 20.0
        cust_name = self.current_user["full_name"] if self.current_user else "Guest Customer"

        if not messagebox.askyesno("Confirm Order", f"Customer: {cust_name}\nTotal: ₹ {total_bill:,.2f}\n\nConfirm purchase?"):
            return

        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Error", "Could not connect to MySQL database.")
            return

        try:
            cursor = conn.cursor()
            now = datetime.now()
            cust_id = self.current_user["customer_id"] if self.current_user else None

            # 1. Insert Sale into MySQL
            cursor.execute(
                "INSERT INTO sales (sale_datetime, total_amount, payment_method, customer_id) VALUES (%s, %s, %s, %s)",
                (now, total_bill, "UPI", cust_id)
            )
            sale_id = cursor.lastrowid

            # 2. Insert items and reduce stock in MySQL
            for p_id, item in self.cart.items():
                item_sub = item["price"] * item["qty"]
                cursor.execute(
                    "INSERT INTO sale_items (sale_id, item_id, quantity, unit_price, subtotal) VALUES (%s, %s, %s, %s, %s)",
                    (sale_id, p_id, item["qty"], item["price"], item_sub)
                )
                cursor.execute(
                    "UPDATE inventory SET stock_quantity = stock_quantity - %s WHERE item_id = %s",
                    (item["qty"], p_id)
                )

            conn.commit()
            cursor.close()
            conn.close()

            # 3. Format and save receipt
            receipt_str = format_receipt(
                sale_id=sale_id,
                items_dict=self.cart,
                subtotal=subtotal,
                delivery_fee=20.0,
                total_amount=total_bill,
                payment_method="UPI"
            )
            saved_file = save_receipt_file(sale_id, receipt_str)

            messagebox.showinfo(
                "Order Successful! 🎉",
                f"Thank you, {cust_name}!\n\nInvoice: #{sale_id}\nSaved to: {saved_file}\nAmount: ₹ {total_bill:,.2f}"
            )

            self.clear_cart()
            self.load_products_from_db()

        except Exception as e:
            messagebox.showerror("Checkout Error", f"Transaction failed: {e}")

    # ==================== 6. FOOTER ====================
    def create_bottom_footer(self):
        footer = tk.Frame(self, bg=self.COLOR_WHITE, height=34, bd=1, relief=tk.SOLID)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)

        perks = "🛡️ Quality Products • 🚚 Fast Delivery • 💳 Secure Payments • 📍 Sanjay Place, Agra - 282002"
        tk.Label(footer, text=perks, font=("Segoe UI", 8), fg=self.COLOR_MUTED, bg=self.COLOR_WHITE).pack(side=tk.LEFT, padx=18)
        tk.Label(footer, text="Thank you for shopping local! ❤️", font=("Segoe UI", 8, "italic"), fg=self.COLOR_MUTED, bg=self.COLOR_WHITE).pack(side=tk.RIGHT, padx=18)


if __name__ == "__main__":
    app = SnapKartCustomerApp()
    app.mainloop()