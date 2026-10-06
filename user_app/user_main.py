import os
import shutil
import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

from database.db_connection import get_db_connection, ensure_core_schema
from common.store_status import check_store_status
from common.pdf_generator import generate_pdf_receipt, open_pdf_file
from common.image_loader import get_product_image
from user_app.auth_ui import AuthDialog
from user_app.upi_payment_dialog import UPIPaymentDialog

# Popular City Localities for Delivery
CITY_LOCALITIES = [
    "Sanjay Place Commercial Hub",
    "Central Market District",
    "Civil Lines Sector 4",
    "Green Park Residency",
    "Model Town Phase 2",
    "Station Road Plaza",
    "Vasant Vihar Enclave",
    "Trans River Colony",
    "Rajendra Nagar Main",
    "Commercial Complex Tower",
]


class SnapKartCustomerApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # Ensure core schema before running queries
        ensure_core_schema()

        self.title("SnapKart - Your Neighbourhood Superstore")
        self.geometry("1440x900")
        self.minsize(1220, 750)
        self.configure(bg="#f8fafc")

        # Color Palette
        self.COLOR_GREEN = "#16a34a"
        self.COLOR_GREEN_LIGHT = "#dcfce7"
        self.COLOR_DARK = "#0f172a"
        self.COLOR_MUTED = "#64748b"
        self.COLOR_WHITE = "#ffffff"
        self.COLOR_RED = "#dc2626"
        self.COLOR_BLUE = "#2563eb"

        # Application State
        self.current_user = None
        self.cart = {}
        self.active_category = "All Products"
        self.sort_option = tk.StringVar(value="Popularity")
        self.selected_locality = CITY_LOCALITIES[0]
        self.selected_house_address = "Flat 102, Block B"
        self.image_cache = {}
        self.current_page = 1
        self.page_size = 48
        self.total_products = 0
        self.total_pages = 1

        # Build Main UI Components
        self.create_top_navbar()

        self.body_frame = tk.Frame(self, bg="#f8fafc")
        self.body_frame.pack(fill=tk.BOTH, expand=True, padx=18, pady=(8, 8))

        self.create_left_sidebar(self.body_frame)
        self.create_center_catalog(self.body_frame)
        self.create_right_cart_panel(self.body_frame)

        self.create_bottom_footer()

        # Initial Status and Data Fetch
        self.refresh_store_status()
        self.load_products_from_db()

    # =========================================================================
    # 1. TOP NAVIGATION BAR
    # =========================================================================
    def create_top_navbar(self):
        nav = tk.Frame(self, bg=self.COLOR_WHITE, height=64, bd=1, relief=tk.SOLID)
        nav.pack(fill=tk.X, side=tk.TOP)
        nav.pack_propagate(False)

        # Brand Title
        brand_box = tk.Frame(nav, bg=self.COLOR_WHITE, cursor="hand2")
        brand_box.pack(side=tk.LEFT, padx=18)
        brand_box.bind("<Button-1>", lambda e: self.show_home_view())

        lbl_brand = tk.Label(brand_box, text="🛒 SnapKart", font=("Segoe UI", 16, "bold"), fg=self.COLOR_GREEN, bg=self.COLOR_WHITE)
        lbl_brand.pack(anchor="w")
        lbl_brand.bind("<Button-1>", lambda e: self.show_home_view())

        lbl_tag = tk.Label(brand_box, text="Your Neighbourhood Store, Online", font=("Segoe UI", 7), fg=self.COLOR_MUTED, bg=self.COLOR_WHITE)
        lbl_tag.pack(anchor="w")
        lbl_tag.bind("<Button-1>", lambda e: self.show_home_view())

        # Functional Navigation Links
        mid_links = tk.Frame(nav, bg=self.COLOR_WHITE)
        mid_links.pack(side=tk.LEFT, padx=15)

        nav_items = [
            ("🏠 Home", self.show_home_view),
            ("🛍️ Shop", self.open_shop_department_modal),
            ("🏷️ Offers", self.open_special_offers_modal),
            ("📦 My Orders", self.open_customer_orders_modal),
            ("❓ Help & Support", self.open_help_support_modal),
        ]

        for text, cmd in nav_items:
            btn = tk.Label(mid_links, text=text, font=("Segoe UI", 9, "bold"), fg=self.COLOR_DARK, bg=self.COLOR_WHITE, padx=10, cursor="hand2")
            btn.pack(side=tk.LEFT)
            btn.bind("<Button-1>", lambda e, c=cmd: c())

        # Right-side Delivery Location & Account Controls
        right_box = tk.Frame(nav, bg=self.COLOR_WHITE)
        right_box.pack(side=tk.RIGHT, padx=18)

        # Location Selector Button
        self.loc_box = tk.Frame(right_box, bg="#f1f5f9", padx=10, pady=4, bd=1, relief=tk.SOLID, cursor="hand2")
        self.loc_box.pack(side=tk.LEFT, padx=(0, 15))
        self.loc_box.bind("<Button-1>", lambda e: self.open_location_modal())

        self.lbl_location = tk.Label(
            self.loc_box,
            text=f"📍 Delivering to: {self.selected_locality[:22]}... ▾",
            font=("Segoe UI", 8, "bold"),
            bg="#f1f5f9",
            fg=self.COLOR_DARK,
            cursor="hand2"
        )
        self.lbl_location.pack()
        self.lbl_location.bind("<Button-1>", lambda e: self.open_location_modal())

        # User Auth Avatar
        tk.Label(right_box, text="👤", font=("Segoe UI", 13), bg=self.COLOR_WHITE).pack(side=tk.LEFT, padx=(0, 5))
        self.profile_info_frame = tk.Frame(right_box, bg=self.COLOR_WHITE)
        self.profile_info_frame.pack(side=tk.LEFT)

        self.lbl_user_name = tk.Label(self.profile_info_frame, text="Hello, Guest", font=("Segoe UI", 9, "bold"), fg=self.COLOR_DARK, bg=self.COLOR_WHITE)
        self.lbl_user_name.pack(anchor="w")

        self.lbl_user_action = tk.Label(self.profile_info_frame, text="Sign In / Register", font=("Segoe UI", 8), fg=self.COLOR_BLUE, bg=self.COLOR_WHITE, cursor="hand2")
        self.lbl_user_action.pack(anchor="w")
        self.lbl_user_action.bind("<Button-1>", self.handle_user_auth_click)

    # =========================================================================
    # 2. NAVIGATION MODALS & LOCATION SELECTOR
    # =========================================================================
    def show_home_view(self):
        self.active_category = "All Products"
        self.search_entry.delete(0, tk.END)
        self.load_categories()
        self.load_products_from_db()

    def open_location_modal(self):
        win = tk.Toplevel(self)
        win.title("SnapKart - Delivery Location")
        win.geometry("450x380")
        win.resizable(False, False)
        win.configure(bg="#ffffff")
        win.transient(self)
        win.grab_set()

        tk.Label(win, text="📍 Select Delivery Address", font=("Segoe UI", 12, "bold"), fg=self.COLOR_GREEN, bg="#ffffff").pack(pady=(15, 5))
        tk.Label(win, text="Select your delivery location to see available store items", font=("Segoe UI", 8), fg=self.COLOR_MUTED, bg="#ffffff").pack(pady=(0, 12))

        form = tk.Frame(win, bg="#ffffff")
        form.pack(fill=tk.BOTH, expand=True, padx=25)

        tk.Label(form, text="Select Locality / Area:", font=("Segoe UI", 9, "bold"), bg="#ffffff").pack(anchor="w", pady=(5, 2))
        combo_loc = ttk.Combobox(form, values=CITY_LOCALITIES, state="readonly", font=("Segoe UI", 9))
        combo_loc.set(self.selected_locality)
        combo_loc.pack(fill=tk.X, ipady=3, pady=(0, 10))

        tk.Label(form, text="House / Flat / Street Details:", font=("Segoe UI", 9, "bold"), bg="#ffffff").pack(anchor="w", pady=(5, 2))
        entry_house = tk.Entry(form, font=("Segoe UI", 9), bg="#f8fafc", bd=1, relief=tk.SOLID)
        entry_house.insert(0, self.selected_house_address)
        entry_house.pack(fill=tk.X, ipady=4, pady=(0, 15))

        def save_location():
            self.selected_locality = combo_loc.get()
            self.selected_house_address = entry_house.get().strip() or "Flat 102"
            short_loc = self.selected_locality.split(",")[0]
            self.lbl_location.config(text=f"📍 Delivering to: {short_loc} ▾")
            messagebox.showinfo("Address Updated", f"Delivery address updated to:\n{self.selected_house_address}, {self.selected_locality}")
            win.destroy()

        tk.Button(
            form,
            text="Confirm Delivery Location",
            font=("Segoe UI", 10, "bold"),
            bg=self.COLOR_GREEN,
            fg="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            command=save_location
        ).pack(fill=tk.X, ipady=6)

    def open_shop_department_modal(self):
        win = tk.Toplevel(self)
        win.title("SnapKart - Browse Departments")
        win.geometry("520x450")
        win.configure(bg="#ffffff")
        win.transient(self)

        tk.Label(win, text="🏬 All Store Departments", font=("Segoe UI", 13, "bold"), fg=self.COLOR_DARK, bg="#ffffff").pack(pady=12)

        conn = get_db_connection()
        cats = []
        if conn:
            try:
                c = conn.cursor()
                c.execute("SELECT DISTINCT category FROM inventory ORDER BY category;")
                cats = [r[0] for r in c.fetchall()]
                c.close()
                conn.close()
            except Exception:
                pass

        box = tk.Frame(win, bg="#ffffff")
        box.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        for cat in cats:
            btn = tk.Button(
                box,
                text=f"📦 {cat}",
                font=("Segoe UI", 9, "bold"),
                bg="#f1f5f9",
                fg=self.COLOR_DARK,
                anchor="w",
                relief=tk.FLAT,
                cursor="hand2",
                command=lambda c=cat: (self.select_category(c), win.destroy())
            )
            btn.pack(fill=tk.X, pady=2, ipady=3)

    def open_special_offers_modal(self):
        win = tk.Toplevel(self)
        win.title("SnapKart - Special Deals & Offers")
        win.geometry("550x460")
        win.configure(bg="#ffffff")
        win.transient(self)

        tk.Label(win, text="🏷️ Live Store Discount Offers", font=("Segoe UI", 14, "bold"), fg=self.COLOR_GREEN, bg="#ffffff").pack(pady=(14, 4))
        tk.Label(win, text="Exclusive discounts active for shoppers today!", font=("Segoe UI", 8), fg=self.COLOR_MUTED, bg="#ffffff").pack(pady=(0, 10))

        offers = [
            ("🥦 Fresh Produce Discount", "Flat 15% OFF on all fresh fruits & vegetables.", "#dcfce7", "#16a34a"),
            ("🥛 Dairy Products Pack", "Buy 2 Dairy products & get Flat ₹20 Instant Cashback.", "#dbeafe", "#2563eb"),
            ("🚚 Free Home Delivery", "Zero delivery charges on orders above ₹499.", "#fef3c7", "#d97706"),
            ("🌾 Grocery Staples Savings", "Up to 20% OFF on Basmati Rice & Edible Oils.", "#f3e8ff", "#9333ea"),
            ("💳 UPI Instant Cashback", "Extra 5% instant discount on payment via UPI.", "#fee2e2", "#dc2626"),
        ]

        for title, desc, bg, fg in offers:
            card = tk.Frame(win, bg=bg, bd=1, relief=tk.SOLID)
            card.pack(fill=tk.X, padx=20, pady=4, ipady=4)
            tk.Label(card, text=title, font=("Segoe UI", 10, "bold"), fg=fg, bg=bg).pack(anchor="w", padx=10)
            tk.Label(card, text=desc, font=("Segoe UI", 8), fg="#334155", bg=bg).pack(anchor="w", padx=10)

    def open_customer_orders_modal(self):
        win = tk.Toplevel(self)
        win.title("SnapKart - My Orders & Printable Invoices")
        win.geometry("780x520")
        win.configure(bg="#ffffff")
        win.transient(self)

        tk.Label(win, text="📦 Your Recent Order History", font=("Segoe UI", 13, "bold"), fg=self.COLOR_DARK, bg="#ffffff").pack(pady=(12, 4))

        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Error", "Could not connect to database.")
            return

        cursor = conn.cursor(dictionary=True)
        cust_id = self.current_user["customer_id"] if self.current_user else None

        if cust_id:
            cursor.execute("""
                SELECT sale_id, DATE_FORMAT(sale_datetime, '%Y-%m-%d %h:%i %p') AS s_time,
                       total_amount, payment_method
                FROM sales
                WHERE customer_id = %s
                ORDER BY sale_datetime DESC;
            """, (cust_id,))
        else:
            cursor.execute("""
                SELECT sale_id, DATE_FORMAT(sale_datetime, '%Y-%m-%d %h:%i %p') AS s_time,
                       total_amount, payment_method
                FROM sales
                ORDER BY sale_datetime DESC
                LIMIT 10;
            """)

        sales = cursor.fetchall()
        cursor.close()
        conn.close()

        if not sales:
            tk.Label(win, text="No previous orders found.", font=("Segoe UI", 10), fg=self.COLOR_MUTED, bg="#ffffff").pack(pady=40)
            return

        cols = ("id", "date", "amount", "payment")
        tree = ttk.Treeview(win, columns=cols, show="headings", height=8)
        tree.heading("id", text="Sale ID")
        tree.heading("date", text="Order Date & Time")
        tree.heading("amount", text="Total Paid (₹)")
        tree.heading("payment", text="Payment Mode")

        tree.column("id", width=80, anchor="center")
        tree.column("date", width=180, anchor="center")
        tree.column("amount", width=120, anchor="e")
        tree.column("payment", width=120, anchor="center")

        for s in sales:
            tree.insert("", tk.END, values=(
                f"#{s['sale_id']}",
                s["s_time"],
                f"₹ {float(s['total_amount']):.2f}",
                s["payment_method"] or "UPI"
            ))

        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        def reprint_selected():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Select Order", "Please select an order from the list.")
                return
            val = tree.item(selected[0], "values")
            s_id = int(val[0].replace("#", ""))

            # Generate PDF invoice
            conn = get_db_connection()
            if conn:
                c = conn.cursor(dictionary=True)
                c.execute("""
                    SELECT i.name, si.quantity, si.unit_price
                    FROM sale_items si
                    JOIN inventory i ON si.item_id = i.item_id
                    WHERE si.sale_id = %s;
                """, (s_id,))
                rows = c.fetchall()
                c.close()
                conn.close()

                items_dict = {}
                subtotal = 0.0
                for idx, r in enumerate(rows, start=1):
                    qty = int(r["quantity"])
                    price = float(r["unit_price"])
                    subtotal += (qty * price)
                    items_dict[idx] = {"name": r["name"], "price": price, "qty": qty}

                tot_bill = float(val[2].replace("₹", "").strip())
                pdf = generate_pdf_receipt(
                    sale_id=s_id,
                    items_dict=items_dict,
                    subtotal=subtotal,
                    delivery_fee=20.0,
                    total_amount=tot_bill,
                    customer_name=self.current_user["full_name"] if self.current_user else "Guest Customer",
                    customer_address=self.selected_locality,
                    payment_method=val[3]
                )
                open_pdf_file(pdf)

        tk.Button(
            win,
            text="📄 Re-Download / View Tax Invoice PDF",
            font=("Segoe UI", 10, "bold"),
            bg=self.COLOR_GREEN,
            fg="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            command=reprint_selected
        ).pack(fill=tk.X, padx=20, pady=(0, 15), ipady=5)

    def open_help_support_modal(self):
        win = tk.Toplevel(self)
        win.title("SnapKart - Help & Customer Support")
        win.geometry("500x420")
        win.configure(bg="#ffffff")
        win.transient(self)

        tk.Label(win, text="❓ SnapKart Help Center", font=("Segoe UI", 13, "bold"), fg=self.COLOR_GREEN, bg="#ffffff").pack(pady=(15, 4))

        info_text = (
            "📍 Store Headquarters:\n"
            "Plot No. 45, Commercial Complex District\n\n"
            "📞 Customer Helpline: +91 1800 245 8900\n"
            "✉️ Email Support: support@snapkart.in\n"
            "🕒 Operating Hours: 09:00 AM – 10:00 PM (Mon-Sun)\n\n"
            "Frequently Asked Questions:\n"
            "• Delivery Time: Fast 30-45 Minutes home delivery.\n"
            "• Returns Policy: Easy 7-day returns on eligible store goods.\n"
            "• Payment Modes: UPI, GPay, PhonePe, Paytm, Cards, Cash."
        )

        tk.Label(win, text=info_text, font=("Segoe UI", 9), fg="#334155", bg="#f8fafc", justify="left", padx=15, pady=15, bd=1, relief=tk.SOLID).pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    # =========================================================================
    # 3. AUTH LOGIC
    # =========================================================================
    def handle_user_auth_click(self, event=None):
        if self.current_user is None:
            AuthDialog(self, on_login_success=self.on_user_logged_in)
        else:
            if messagebox.askyesno("Log Out", f"Log out from account {self.current_user['full_name']}?"):
                self.current_user = None
                self.lbl_user_name.config(text="Hello, Guest")
                self.lbl_user_action.config(text="Sign In / Register", fg=self.COLOR_BLUE)
                messagebox.showinfo("Logged Out", "You have logged out successfully.")

    def on_user_logged_in(self, user_data):
        self.current_user = user_data
        first_name = user_data["full_name"].split()[0]
        self.lbl_user_name.config(text=f"Hello, {first_name} 👋")
        self.lbl_user_action.config(text="Log Out", fg=self.COLOR_RED)

    # =========================================================================
    # 4. LEFT SIDEBAR: STORE STATUS & CATEGORIES
    # =========================================================================
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

        for perk in ["✨ Quality Assurance", "⚡ 30-Min Fast Delivery", "🔒 Secure Payments", "💰 Best Market Rates"]:
            tk.Label(self.status_card, text=perk, font=("Segoe UI", 7, "bold"), fg=self.COLOR_MUTED, bg=self.COLOR_WHITE, anchor="w").pack(fill=tk.X, padx=14, pady=1)

        # Categories Menu Box
        cat_box = tk.Frame(sidebar, bg=self.COLOR_WHITE, bd=1, relief=tk.SOLID)
        cat_box.pack(fill=tk.BOTH, expand=True)

        tk.Label(cat_box, text="Categories", font=("Segoe UI", 10, "bold"), fg=self.COLOR_DARK, bg=self.COLOR_WHITE).pack(anchor="w", padx=10, pady=(8, 4))

        self.cat_canvas = tk.Canvas(cat_box, bg=self.COLOR_WHITE, bd=0, highlightthickness=0)
        cat_scroll = ttk.Scrollbar(cat_box, orient="vertical", command=self.cat_canvas.yview)
        self.cat_inner = tk.Frame(self.cat_canvas, bg=self.COLOR_WHITE)

        self.cat_canvas.create_window((0, 0), window=self.cat_inner, anchor="nw")
        self.cat_inner.bind("<Configure>", lambda e: self.cat_canvas.configure(scrollregion=self.cat_canvas.bbox("all")))

        self.cat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(2, 0))
        cat_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.cat_canvas.configure(yscrollcommand=cat_scroll.set)

        self.cat_canvas.bind("<Enter>", lambda e: self._bind_mousewheel(self.cat_canvas))
        self.cat_canvas.bind("<Leave>", lambda e: self._unbind_mousewheel())

        self.load_categories()

    def load_categories(self):
        for w in self.cat_inner.winfo_children():
            w.destroy()

        conn = get_db_connection()
        categories = ["All Products"]
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT category FROM inventory ORDER BY category;")
                categories += [row[0] for row in cursor.fetchall()]
                cursor.close()
            except Exception:
                pass
            finally:
                if conn.is_connected():
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
        self.current_page = 1
        self.load_categories()
        self.load_products_from_db()

    # =========================================================================
    # 5. CENTER CATALOG: BANNER, SEARCH, SORT & PRODUCT GRID
    # =========================================================================
    def create_center_catalog(self, parent):
        center = tk.Frame(parent, bg="#f8fafc")
        center.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Promotional Banner
        banner = tk.Frame(center, bg="#e0f2fe", bd=1, relief=tk.SOLID)
        banner.pack(fill=tk.X, pady=(0, 8), ipady=6)

        b_text = tk.Frame(banner, bg="#e0f2fe")
        b_text.pack(side=tk.LEFT, padx=16)
        tk.Label(b_text, text="SNAPKART ONLINE SUPERMARKET", font=("Segoe UI", 7, "bold"), fg="#0284c7", bg="#e0f2fe").pack(anchor="w")
        tk.Label(b_text, text="10,000+ Fresh Products at Best Daily Market Prices!", font=("Segoe UI", 12, "bold"), fg="#0f172a", bg="#e0f2fe").pack(anchor="w")

        # Search Bar and Sort Options
        top_filter_row = tk.Frame(center, bg="#f8fafc")
        top_filter_row.pack(fill=tk.X, pady=(0, 8))

        search_box = tk.Frame(top_filter_row, bg=self.COLOR_WHITE, bd=1, relief=tk.SOLID)
        search_box.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)

        tk.Label(search_box, text=" 🔍 ", bg=self.COLOR_WHITE, fg=self.COLOR_MUTED).pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_box, font=("Segoe UI", 9), bg=self.COLOR_WHITE, bd=0, fg=self.COLOR_DARK)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        self.search_entry.bind("<KeyRelease>", lambda e: self.on_search_query())

        tk.Button(search_box, text="Clear", font=("Segoe UI", 7), bg="#e2e8f0", bd=0, command=self.clear_search).pack(side=tk.RIGHT, padx=4)

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
        sort_cb.bind("<<ComboboxSelected>>", lambda e: self.on_sort_changed())

        # Scrollable Product Cards Frame
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

        self.grid_canvas.bind("<Enter>", lambda e: self._bind_mousewheel(self.grid_canvas))
        self.grid_canvas.bind("<Leave>", lambda e: self._unbind_mousewheel())

        # Pagination Bar
        self.pagination_frame = tk.Frame(center, bg="#f8fafc", pady=4)
        self.pagination_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.btn_prev_page = tk.Button(
            self.pagination_frame,
            text="◀ Previous Page",
            font=("Segoe UI", 9, "bold"),
            bg=self.COLOR_WHITE,
            fg=self.COLOR_DARK,
            bd=1,
            relief=tk.SOLID,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.prev_catalog_page
        )
        self.btn_prev_page.pack(side=tk.LEFT, padx=10)

        self.lbl_page_info = tk.Label(
            self.pagination_frame,
            text="Showing 0 products",
            font=("Segoe UI", 9, "bold"),
            bg="#f8fafc",
            fg=self.COLOR_DARK
        )
        self.lbl_page_info.pack(side=tk.LEFT, expand=True)

        self.btn_next_page = tk.Button(
            self.pagination_frame,
            text="Next Page ▶",
            font=("Segoe UI", 9, "bold"),
            bg=self.COLOR_GREEN,
            fg="#ffffff",
            bd=0,
            padx=14,
            pady=4,
            cursor="hand2",
            command=self.next_catalog_page
        )
        self.btn_next_page.pack(side=tk.RIGHT, padx=10)

    def on_search_query(self):
        self.current_page = 1
        self.load_products_from_db()

    def on_sort_changed(self):
        self.current_page = 1
        self.load_products_from_db()

    def prev_catalog_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_products_from_db()
            self.grid_canvas.yview_moveto(0)

    def next_catalog_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_products_from_db()
            self.grid_canvas.yview_moveto(0)

    def clear_search(self):
        self.search_entry.delete(0, tk.END)
        self.current_page = 1
        self.load_products_from_db()

    def load_products_from_db(self):
        for w in self.cards_frame.winfo_children():
            w.destroy()

        conn = get_db_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor(dictionary=True)
            search_txt = self.search_entry.get().strip()

            # 1. Total Count for Pagination
            count_sql = "SELECT COUNT(*) AS total FROM inventory WHERE stock_quantity > 0"
            count_params = []
            if self.active_category != "All Products":
                count_sql += " AND category = %s"
                count_params.append(self.active_category)
            if search_txt:
                count_sql += " AND name LIKE %s"
                count_params.append(f"%{search_txt}%")

            cursor.execute(count_sql, count_params)
            count_row = cursor.fetchone()
            self.total_products = count_row["total"] if count_row else 0
            self.total_pages = max(1, math.ceil(self.total_products / self.page_size))
            self.current_page = max(1, min(self.current_page, self.total_pages))
            offset = (self.current_page - 1) * self.page_size

            # 2. Main Paginated Catalog Query
            query = "SELECT item_id, name, category, price, stock_quantity FROM inventory WHERE stock_quantity > 0"
            params = []

            if self.active_category != "All Products":
                query += " AND category = %s"
                params.append(self.active_category)

            if search_txt:
                query += " AND name LIKE %s"
                params.append(f"%{search_txt}%")

            sort_mode = self.sort_option.get()
            if sort_mode == "Price: Low to High":
                query += " ORDER BY price ASC, item_id ASC"
            elif sort_mode == "Price: High to Low":
                query += " ORDER BY price DESC, item_id ASC"
            else:
                if self.active_category == "All Products":
                    query += """ ORDER BY 
                        CASE 
                            WHEN category = 'Fresh Fruits & Berries' THEN 1
                            WHEN category = 'Dairy, Milk & Paneer' THEN 2
                            WHEN category = 'Fresh Vegetables & Greens' THEN 3
                            WHEN category = 'Bakery & Breakfast' THEN 4
                            WHEN category = 'Snacks, Chips & Namkeen' THEN 5
                            WHEN category = 'Chocolates, Sweets & Biscuits' THEN 6
                            WHEN category = 'Tea, Coffee & Beverages' THEN 7
                            WHEN category = 'Grocery & Staples' THEN 8
                            WHEN category = 'Ready to Eat' THEN 9
                            WHEN category = 'Personal Care & Grooming' THEN 10
                            WHEN category = 'Health, Wellness & Supplements' THEN 11
                            WHEN category = 'Household & Cleaning' THEN 12
                            WHEN category = 'Home & Kitchenware' THEN 13
                            WHEN category = 'Sports & Fitness' THEN 14
                            WHEN category = 'Stationery & Office Supplies' THEN 15
                            WHEN category = 'Clothing & Fashion' THEN 16
                            WHEN category = 'Girls Accessories & Makeup' THEN 17
                            WHEN category = 'Tech & Mobile Accessories' THEN 18
                            WHEN category = 'Seasonal, Pooja & Festival' THEN 19
                            WHEN category = 'All Medicines & First Aid' THEN 20
                            ELSE 21
                        END ASC, item_id ASC"""
                else:
                    query += " ORDER BY item_id ASC"

            query += " LIMIT %s OFFSET %s;"
            params.extend([self.page_size, offset])

            cursor.execute(query, params)
            products = cursor.fetchall()
            cursor.close()

            # Update pagination display
            start_num = offset + 1 if self.total_products > 0 else 0
            end_num = min(offset + len(products), self.total_products)
            self.lbl_page_info.config(
                text=f"Page {self.current_page} of {self.total_pages}  (Showing {start_num} - {end_num} of {self.total_products:,} items)"
            )
            self.btn_prev_page.config(state=tk.NORMAL if self.current_page > 1 else tk.DISABLED)
            self.btn_next_page.config(state=tk.NORMAL if self.current_page < self.total_pages else tk.DISABLED)

        except Exception as e:
            print(f"Error loading products: {e}")
            products = []
        finally:
            if conn.is_connected():
                conn.close()

        # Render 3 Cards Per Row
        for idx, prod in enumerate(products):
            r = idx // 3
            c = idx % 3
            self.create_single_product_card(self.cards_frame, prod, r, c)

    def create_single_product_card(self, parent, prod, r, c):
        card = tk.Frame(parent, bg=self.COLOR_WHITE, bd=1, relief=tk.SOLID, width=225, height=275)
        card.grid(row=r, column=c, padx=6, pady=6, sticky="nsew")
        card.grid_propagate(False)

        # 1. Product Image Rendering
        p_id = prod["item_id"]
        photo = get_product_image(p_id, prod["name"], prod["category"], size=(210, 110))
        self.image_cache[p_id] = photo

        img_label = tk.Label(card, image=photo, bg=self.COLOR_WHITE)
        img_label.pack(fill=tk.X, padx=5, pady=(5, 3))

        # 2. Tag and Stock Indicator
        tag_row = tk.Frame(card, bg=self.COLOR_WHITE)
        tag_row.pack(fill=tk.X, padx=8, pady=(2, 2))

        stock_qty = prod['stock_quantity']
        if stock_qty < 20:
            stock_fg = self.COLOR_RED
            stock_text = f"Low Stock: {stock_qty}"
        else:
            stock_fg = self.COLOR_MUTED
            stock_text = f"Stock: {stock_qty}"

        tk.Label(tag_row, text="Bestseller", font=("Segoe UI", 7, "bold"), bg="#dcfce7", fg=self.COLOR_GREEN, padx=4).pack(side=tk.LEFT)
        tk.Label(tag_row, text=stock_text, font=("Segoe UI", 7), fg=stock_fg, bg=self.COLOR_WHITE).pack(side=tk.RIGHT)

        # 3. Product Details
        name_lbl = tk.Label(card, text=prod["name"], font=("Segoe UI", 9, "bold"), fg=self.COLOR_DARK, bg=self.COLOR_WHITE, wraplength=205, justify="left")
        name_lbl.pack(anchor="w", padx=8, pady=(4, 0))

        cat_lbl = tk.Label(card, text=prod["category"], font=("Segoe UI", 7), fg=self.COLOR_MUTED, bg=self.COLOR_WHITE)
        cat_lbl.pack(anchor="w", padx=8)

        # 4. Pricing and Add to Cart Button
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
    # 6. RIGHT SIDEBAR: CART CONTAINER
    # =========================================================================
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

        self.cart_canvas.bind("<Enter>", lambda e: self._bind_mousewheel(self.cart_canvas))
        self.cart_canvas.bind("<Leave>", lambda e: self._unbind_mousewheel())

        summary_box = tk.Frame(self.cart_panel, bg="#f8fafc", bd=1, relief=tk.SOLID)
        summary_box.pack(fill=tk.X, padx=10, pady=(4, 6), ipady=4)

        self.lbl_subtotal = self.make_summary_row(summary_box, "Subtotal", "₹ 0.00")
        self.lbl_delivery = self.make_summary_row(summary_box, "Delivery Fee", "₹ 20.00")
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

    # =========================================================================
    # 7. CART HANDLERS
    # =========================================================================
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

    # =========================================================================
    # 8. BUSINESS HOURS & CHECKOUT FLOW
    # =========================================================================
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

        if self.current_user is None:
            if messagebox.askyesno("Sign In Recommended", "You are checking out as Guest.\n\nWould you like to Log In or Sign Up first?"):
                AuthDialog(self, on_login_success=self.on_user_logged_in)
                return

        subtotal = sum(i["price"] * i["qty"] for i in self.cart.values())
        total_bill = subtotal + 20.0
        cust_name = self.current_user["full_name"] if self.current_user else "Guest Customer"

        # Open Simulated UPI Gateway
        UPIPaymentDialog(
            parent=self,
            total_amount=total_bill,
            customer_name=cust_name,
            on_payment_success=lambda: self.complete_order_and_download(subtotal, total_bill, cust_name)
        )

    def complete_order_and_download(self, subtotal, total_bill, cust_name):
        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Error", "Could not connect to MySQL database.")
            return

        cursor = None
        try:
            cursor = conn.cursor()
            now = datetime.now()
            cust_id = self.current_user["customer_id"] if self.current_user else None

            # Insert Sale Record
            cursor.execute(
                "INSERT INTO sales (sale_datetime, total_amount, payment_method, customer_id) VALUES (%s, %s, %s, %s)",
                (now, total_bill, "UPI", cust_id)
            )
            sale_id = cursor.lastrowid

            # Insert Sale Items & Deduct Stock
            for p_id, item in self.cart.items():
                item_sub = item["price"] * item["qty"]
                cursor.execute(
                    "INSERT INTO sale_items (sale_id, item_id, quantity, unit_price, subtotal) VALUES (%s, %s, %s, %s, %s)",
                    (sale_id, p_id, item["qty"], item["price"], item_sub)
                )
                cursor.execute(
                    "UPDATE inventory SET stock_quantity = GREATEST(stock_quantity - %s, 0) WHERE item_id = %s",
                    (item["qty"], p_id)
                )

            conn.commit()

            full_addr = f"{self.selected_house_address}, {self.selected_locality}"

            # Generate Official GST Tax Invoice PDF
            default_pdf = generate_pdf_receipt(
                sale_id=sale_id,
                items_dict=self.cart,
                subtotal=subtotal,
                delivery_fee=20.0,
                total_amount=total_bill,
                customer_name=cust_name,
                customer_address=full_addr,
                payment_method="UPI"
            )

            ask_download = messagebox.askyesno(
                "Payment Successful! 🎉",
                f"UPI Payment of ₹ {total_bill:,.2f} was successful!\n\n"
                f"GST Tax Invoice ID: #SK-2026-{sale_id:06d}\n"
                f"Delivering to: {full_addr}\n\n"
                "Would you like to download your official Tax Invoice bill now?"
            )

            if ask_download:
                chosen_file_path = filedialog.asksaveasfilename(
                    initialfile=f"SnapKart_TaxInvoice_{sale_id}.pdf",
                    defaultextension=".pdf",
                    filetypes=[("PDF Document", "*.pdf"), ("All Files", "*.*")],
                    title="Download Your SnapKart Tax Invoice"
                )

                if chosen_file_path:
                    shutil.copyfile(default_pdf, chosen_file_path)
                    messagebox.showinfo("Download Complete", f"Your tax invoice has been saved to:\n{chosen_file_path}")
                    open_pdf_file(chosen_file_path)
                else:
                    open_pdf_file(default_pdf)
            else:
                open_pdf_file(default_pdf)

            self.clear_cart()
            self.load_products_from_db()

        except Exception as e:
            messagebox.showerror("Checkout Error", f"Transaction failed: {e}")
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass
            if conn and conn.is_connected():
                conn.close()

    # =========================================================================
    # 9. MOUSEWHEEL & FOOTER
    # =========================================================================
    def _bind_mousewheel(self, canvas):
        self._active_canvas = canvas
        self.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self):
        self.unbind_all("<MouseWheel>")
        self._active_canvas = None

    def _on_mousewheel(self, event):
        if hasattr(self, '_active_canvas') and self._active_canvas:
            self._active_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def create_bottom_footer(self):
        footer = tk.Frame(self, bg=self.COLOR_WHITE, height=34, bd=1, relief=tk.SOLID)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)

        perks = "✨ Quality Products • 🚚 30-Min Fast Delivery • 💳 Instant UPI • 📍 SnapKart Superstore"
        tk.Label(footer, text=perks, font=("Segoe UI", 8), fg=self.COLOR_MUTED, bg=self.COLOR_WHITE).pack(side=tk.LEFT, padx=18)
        tk.Label(footer, text="Thank you for shopping with SnapKart! ❤️", font=("Segoe UI", 8, "italic"), fg=self.COLOR_MUTED, bg=self.COLOR_WHITE).pack(side=tk.RIGHT, padx=18)


if __name__ == "__main__":
    app = SnapKartCustomerApp()
    app.mainloop()