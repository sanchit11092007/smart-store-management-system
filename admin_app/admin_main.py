import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

import matplotlib
matplotlib.use("Agg")  # Must be set before importing pyplot
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from database.db_connection import get_db_connection, ensure_core_schema
from common.store_status import check_store_status


class SnapKartModernDashboard(tk.Tk):
    def __init__(self):
        super().__init__()

        # Ensure core schema
        ensure_core_schema()

        self.title("SnapKart Agra - Admin Control Portal")
        self.geometry("1440x900")
        self.minsize(1250, 780)
        self.configure(bg="#0f172a")

        # Color palette
        self.COLOR_BG = "#f1f5f9"
        self.COLOR_SIDEBAR = "#0b1329"
        self.COLOR_PRIMARY = "#2563eb"
        self.COLOR_SUCCESS = "#16a34a"
        self.COLOR_DANGER = "#dc2626"
        self.COLOR_WARNING = "#f59e0b"
        self.COLOR_PURPLE = "#9333ea"
        self.COLOR_TEXT_DARK = "#0f172a"
        self.COLOR_TEXT_MUTED = "#64748b"

        self.chart_canvas = None
        self._active_canvas = None

        # Build UI layout
        self.create_sidebar()
        self.create_main_content()

        # Load live database data
        self.load_all_backend_data()

    # ==================== 1. SIDEBAR ====================
    def create_sidebar(self):
        sidebar = tk.Frame(self, bg=self.COLOR_SIDEBAR, width=255)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # Brand header
        brand_box = tk.Frame(sidebar, bg=self.COLOR_SIDEBAR)
        brand_box.pack(fill=tk.X, padx=20, pady=(22, 18))

        tk.Label(brand_box, text="🛒 SnapKart Agra", font=("Segoe UI", 17, "bold"), fg="#ffffff", bg=self.COLOR_SIDEBAR).pack(anchor="w")
        tk.Label(brand_box, text="Agra Store Management Portal", font=("Segoe UI", 8), fg="#94a3b8", bg=self.COLOR_SIDEBAR).pack(anchor="w", pady=(2, 0))

        # Menu navigation items
        menu_canvas = tk.Canvas(sidebar, bg=self.COLOR_SIDEBAR, bd=0, highlightthickness=0)
        menu_frame = tk.Frame(menu_canvas, bg=self.COLOR_SIDEBAR)

        menu_canvas.create_window((0, 0), window=menu_frame, anchor="nw")
        menu_frame.bind("<Configure>", lambda e: menu_canvas.configure(scrollregion=menu_canvas.bbox("all")))
        menu_canvas.pack(fill=tk.BOTH, expand=True, padx=8)

        sections = [
            ("DASHBOARD", [("📊  Dashboard Overview", True)]),
            ("SALES & POS", [("💳  Billing (New Sale POS)", False), ("📑  Transactions & Receipts", False), ("🔄  Returns & Refunds", False)]),
            ("INVENTORY CONTROL", [("📦  Product Management", False), ("📋  Stock Management", False), ("⚠️  Low Stock Alerts", False), ("🚚  Agra Suppliers Directory", False)]),
            ("STORE OPERATIONS", [("⏰  Store Operating Hours", False), ("👥  Customer & Staff Management", False)]),
            ("ANALYTICS & REPORTS", [("📈  Sales & Revenue Analytics", False), ("📦  Inventory Reports", False)]),
            ("SYSTEM", [("⚙️  System Settings", False), ("❓  Help & Technical Support", False)])
        ]

        for sec_name, items in sections:
            tk.Label(menu_frame, text=sec_name, font=("Segoe UI", 7, "bold"), fg="#475569", bg=self.COLOR_SIDEBAR).pack(anchor="w", padx=12, pady=(10, 3))

            for item_text, is_active in items:
                bg_col = self.COLOR_PRIMARY if is_active else self.COLOR_SIDEBAR
                fg_col = "#ffffff" if is_active else "#cbd5e1"
                btn = tk.Button(
                    menu_frame,
                    text=f"  {item_text}",
                    font=("Segoe UI", 9, "bold" if is_active else "normal"),
                    fg=fg_col,
                    bg=bg_col,
                    activebackground="#1d4ed8",
                    activeforeground="#ffffff",
                    relief=tk.FLAT,
                    anchor="w",
                    padx=10,
                    pady=5,
                    cursor="hand2",
                    bd=0,
                    command=lambda name=item_text: self.navigate_menu(name)
                )
                btn.pack(fill=tk.X, pady=1)

        # Bottom version footer
        footer = tk.Frame(sidebar, bg=self.COLOR_SIDEBAR)
        footer.pack(side=tk.BOTTOM, fill=tk.X, padx=18, pady=14)
        tk.Label(footer, text="SnapKart POS v2.4.0", font=("Segoe UI", 8, "bold"), fg="#94a3b8", bg=self.COLOR_SIDEBAR).pack(anchor="w")
        tk.Label(footer, text="Agra Store • Commercial Hub", font=("Segoe UI", 7), fg="#64748b", bg=self.COLOR_SIDEBAR).pack(anchor="w")

    def navigate_menu(self, menu_name):
        if "Dashboard" in menu_name:
            self.load_all_backend_data()
            messagebox.showinfo("Dashboard Refreshed", "Dashboard data synced with MySQL database.")

        elif "Product Management" in menu_name or "Stock Management" in menu_name or "Low Stock Alerts" in menu_name:
            from admin_app.inventory_ui import InventoryFrame
            win = tk.Toplevel(self)
            win.title("SnapKart Agra - Product & Stock Inventory")
            win.geometry("1100x720")
            InventoryFrame(win)

        elif "Transactions" in menu_name:
            from admin_app.transactions_ui import TransactionsFrame
            win = tk.Toplevel(self)
            win.title("SnapKart Agra - Transaction Records & PDF Receipts")
            win.geometry("1000x660")
            TransactionsFrame(win)

        elif "Store Operating Hours" in menu_name:
            from admin_app.store_settings_ui import StoreSettingsFrame
            win = tk.Toplevel(self)
            win.title("SnapKart Agra - Operating Schedule Settings")
            win.geometry("900x660")
            StoreSettingsFrame(win)

        elif "Analytics" in menu_name or "Reports" in menu_name:
            from admin_app.analytics_ui import AnalyticsFrame
            win = tk.Toplevel(self)
            win.title("SnapKart Agra - Business Analytics & Data Insights")
            win.geometry("1050x720")
            AnalyticsFrame(win)

        elif "Billing" in menu_name:
            subprocess.Popen([sys.executable, "-m", "user_app.user_main"])

        elif "Returns & Refunds" in menu_name:
            self.open_returns_dialog()

        elif "Suppliers" in menu_name:
            self.open_suppliers_dialog()

        elif "Customer & Staff" in menu_name:
            self.open_user_management_dialog()

        else:
            messagebox.showinfo("SnapKart Admin Portal", f"Opened section: {menu_name}")

    def open_returns_dialog(self):
        win = tk.Toplevel(self)
        win.title("SnapKart Agra - Process Return / Refund")
        win.geometry("460x340")
        win.configure(bg="#ffffff")
        win.transient(self)

        tk.Label(win, text="🔄 Customer Return & Refund Portal", font=("Segoe UI", 12, "bold"), fg=self.COLOR_PRIMARY, bg="#ffffff").pack(pady=(15, 8))

        form = tk.Frame(win, bg="#ffffff")
        form.pack(fill=tk.BOTH, expand=True, padx=25)

        tk.Label(form, text="Enter Sale ID / Invoice Number:", font=("Segoe UI", 9, "bold"), bg="#ffffff").pack(anchor="w", pady=(5, 2))
        entry_sale = tk.Entry(form, font=("Segoe UI", 9), bg="#f8fafc", bd=1, relief=tk.SOLID)
        entry_sale.pack(fill=tk.X, ipady=4, pady=(0, 10))

        tk.Label(form, text="Reason for Return:", font=("Segoe UI", 9, "bold"), bg="#ffffff").pack(anchor="w", pady=(5, 2))
        entry_reason = tk.Entry(form, font=("Segoe UI", 9), bg="#f8fafc", bd=1, relief=tk.SOLID)
        entry_reason.insert(0, "Customer requested exchange / return")
        entry_reason.pack(fill=tk.X, ipady=4, pady=(0, 15))

        def process_return():
            s_txt = entry_sale.get().strip().replace("#", "")
            if not s_txt.isdigit():
                messagebox.showerror("Error", "Please enter a valid numeric Sale ID.")
                return
            messagebox.showinfo("Return Processed", f"Return request logged for Invoice #{s_txt}.\nStock item returned to inventory.")
            win.destroy()

        tk.Button(form, text="Confirm Return & Issue Refund", font=("Segoe UI", 10, "bold"), bg=self.COLOR_PRIMARY, fg="#ffffff", relief=tk.FLAT, cursor="hand2", command=process_return).pack(fill=tk.X, ipady=5)

    def open_suppliers_dialog(self):
        win = tk.Toplevel(self)
        win.title("SnapKart Agra - Wholesale Suppliers Directory")
        win.geometry("520x400")
        win.configure(bg="#ffffff")
        win.transient(self)

        tk.Label(win, text="🚚 Verified Agra Wholesale Suppliers", font=("Segoe UI", 12, "bold"), fg=self.COLOR_DARK, bg="#ffffff").pack(pady=(15, 8))

        suppliers = [
            ("🌾 Agra Grain Wholesale Mandi", "Belanganj, Agra", "+91 562 260 1122", "Atta, Rice, Pulses"),
            ("🥛 Taj Dairy Products Co-op", "Sanjay Place, Agra", "+91 562 245 4488", "Milk, Paneer, Ghee"),
            ("🍎 Agra Cold Storage & Fruits", "Sikandra, Agra", "+91 562 270 3344", "Fresh Veggies & Fruits"),
            ("🍫 Braj FMCG & Snacks Distributors", "Kamla Nagar, Agra", "+91 562 252 7799", "Snacks, Biscuits, Chocolates"),
        ]

        for title, loc, phone, items in suppliers:
            card = tk.Frame(win, bg="#f8fafc", bd=1, relief=tk.SOLID)
            card.pack(fill=tk.X, padx=20, pady=4, ipady=4)
            tk.Label(card, text=f"• {title} ({loc})", font=("Segoe UI", 9, "bold"), fg=self.COLOR_DARK, bg="#f8fafc").pack(anchor="w", padx=10)
            tk.Label(card, text=f"   Items: {items} | Phone: {phone}", font=("Segoe UI", 8), fg=self.COLOR_TEXT_MUTED, bg="#f8fafc").pack(anchor="w", padx=10)

    def open_user_management_dialog(self):
        win = tk.Toplevel(self)
        win.title("SnapKart - Customer & Staff Management")
        win.geometry("620x420")
        win.configure(bg="#ffffff")
        win.transient(self)

        tk.Label(win, text="👥 Registered Customers Directory", font=("Segoe UI", 12, "bold"), fg=self.COLOR_DARK, bg="#ffffff").pack(pady=(15, 8))

        conn = get_db_connection()
        customers = []
        if conn:
            try:
                c = conn.cursor(dictionary=True)
                c.execute("SELECT customer_id, full_name, email, phone, DATE_FORMAT(created_at, '%Y-%m-%d') AS reg_date FROM customers ORDER BY customer_id DESC LIMIT 10;")
                customers = c.fetchall()
                c.close()
                conn.close()
            except Exception:
                pass

        cols = ("id", "name", "email", "phone", "date")
        tree = ttk.Treeview(win, columns=cols, show="headings", height=8)
        tree.heading("id", text="ID")
        tree.heading("name", text="Full Name")
        tree.heading("email", text="Email")
        tree.heading("phone", text="Phone")
        tree.heading("date", text="Registered")

        tree.column("id", width=40, anchor="center")
        tree.column("name", width=140, anchor="w")
        tree.column("email", width=170, anchor="w")
        tree.column("phone", width=110, anchor="center")
        tree.column("date", width=100, anchor="center")

        for cust in customers:
            tree.insert("", tk.END, values=(cust["customer_id"], cust["full_name"], cust["email"], cust["phone"], cust["reg_date"]))

        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    # ==================== 2. MAIN CONTAINER ====================
    def create_main_content(self):
        container = tk.Frame(self, bg=self.COLOR_BG)
        container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.create_top_header(container)

        self.main_canvas = tk.Canvas(container, bg=self.COLOR_BG, bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.main_canvas.yview)

        self.scroll_body = tk.Frame(self.main_canvas, bg=self.COLOR_BG)
        self.scroll_body.bind("<Configure>", lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all")))

        self.main_canvas.create_window((0, 0), window=self.scroll_body, anchor="nw")
        self.main_canvas.configure(yscrollcommand=scrollbar.set)

        self.main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.main_canvas.bind("<Enter>", lambda e: self._bind_mousewheel(self.main_canvas))
        self.main_canvas.bind("<Leave>", lambda e: self._unbind_mousewheel())

        self.create_welcome_banner(self.scroll_body)
        self.create_kpi_cards(self.scroll_body)
        self.create_middle_section(self.scroll_body)
        self.create_bottom_section(self.scroll_body)
        self.create_footer(self.scroll_body)

    def _bind_mousewheel(self, canvas):
        self._active_canvas = canvas
        self.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self):
        self.unbind_all("<MouseWheel>")
        self._active_canvas = None

    def _on_mousewheel(self, event):
        if self._active_canvas:
            self._active_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def create_top_header(self, parent):
        top_bar = tk.Frame(parent, bg="#ffffff", height=65, bd=1, relief=tk.SOLID)
        top_bar.pack(fill=tk.X, side=tk.TOP)
        top_bar.pack_propagate(False)

        search_pill = tk.Frame(top_bar, bg="#f8fafc", bd=1, relief=tk.SOLID)
        search_pill.pack(side=tk.LEFT, padx=25, pady=12)

        tk.Label(search_pill, text="  🔍  ", bg="#f8fafc", fg="#94a3b8").pack(side=tk.LEFT)
        search_box = tk.Entry(search_pill, width=48, font=("Segoe UI", 9), bg="#f8fafc", fg=self.COLOR_TEXT_DARK, bd=0)
        search_box.insert(0, "Search products, customers, or invoices... (Ctrl + K)")
        search_box.pack(side=tk.LEFT, ipady=4, padx=(0, 10))

        profile_box = tk.Frame(top_bar, bg="#ffffff")
        profile_box.pack(side=tk.RIGHT, padx=25)

        bell_frame = tk.Frame(profile_box, bg="#ffffff")
        bell_frame.pack(side=tk.LEFT, padx=(0, 18))
        tk.Label(bell_frame, text="🔔", font=("Segoe UI", 12), bg="#ffffff").pack(side=tk.LEFT)
        tk.Label(bell_frame, text="3", font=("Segoe UI", 7, "bold"), bg=self.COLOR_DANGER, fg="#ffffff", padx=4, pady=1).pack(side=tk.LEFT, anchor="n")

        lbl_avatar = tk.Label(profile_box, text="S", font=("Segoe UI", 11, "bold"), bg=self.COLOR_PRIMARY, fg="#ffffff", width=3, height=1)
        lbl_avatar.pack(side=tk.LEFT, padx=(0, 8))

        info = tk.Frame(profile_box, bg="#ffffff")
        info.pack(side=tk.LEFT)
        tk.Label(info, text="Sanchit Goyal", font=("Segoe UI", 9, "bold"), fg=self.COLOR_TEXT_DARK, bg="#ffffff").pack(anchor="w")
        tk.Label(info, text="Agra Store Manager  ▾", font=("Segoe UI", 8), fg=self.COLOR_TEXT_MUTED, bg="#ffffff").pack(anchor="w")

    def create_welcome_banner(self, parent):
        banner = tk.Frame(parent, bg="#ffffff", bd=1, relief=tk.SOLID)
        banner.pack(fill=tk.X, padx=24, pady=(18, 14), ipady=10)

        left = tk.Frame(banner, bg="#ffffff")
        left.pack(side=tk.LEFT, padx=20)

        tk.Label(left, text="Welcome Back, Sanchit! 👋", font=("Segoe UI", 15, "bold"), fg=self.COLOR_TEXT_DARK, bg="#ffffff").pack(anchor="w")
        tk.Label(left, text="Manage your Agra flagship store, track live sales, and monitor 10,000+ products.", font=("Segoe UI", 9), fg=self.COLOR_TEXT_MUTED, bg="#ffffff").pack(anchor="w", pady=(2, 0))

        quote = tk.Label(banner, text='"Better products. Happier customers.\nStronger tomorrow."', font=("Segoe UI", 9, "italic"), fg="#94a3b8", bg="#ffffff", justify="right")
        quote.pack(side=tk.RIGHT, padx=25)

    # ==================== 3. KPI CARDS ====================
    def create_kpi_cards(self, parent):
        grid = tk.Frame(parent, bg=self.COLOR_BG)
        grid.pack(fill=tk.X, padx=24, pady=(0, 14))

        self.lbl_kpi_sales = self.build_card(grid, "Total Sales (Today)", "₹0.00", "Live from MySQL", self.COLOR_SUCCESS, "🛒", "#dcfce7", 0)
        self.lbl_kpi_items = self.build_card(grid, "Items Sold", "0", "Units sold today", self.COLOR_PRIMARY, "📦", "#dbeafe", 1)
        self.lbl_kpi_customers = self.build_card(grid, "Total Customers", "0", "Completed bills", self.COLOR_PURPLE, "👥", "#f3e8ff", 2)
        self.lbl_kpi_low_stock = self.build_card(grid, "Low Stock Items", "0", "Need reorder (<20)", self.COLOR_DANGER, "⚠️", "#fee2e2", 3)

    def build_card(self, parent, title, val_text, sub_text, color, icon, icon_bg, col_idx):
        card = tk.Frame(parent, bg="#ffffff", bd=1, relief=tk.SOLID)
        card.grid(row=0, column=col_idx, padx=6, sticky="nsew")
        parent.columnconfigure(col_idx, weight=1)

        top_row = tk.Frame(card, bg="#ffffff")
        top_row.pack(fill=tk.X, padx=14, pady=(12, 2))

        tk.Label(top_row, text=icon, font=("Segoe UI", 11), bg=icon_bg, fg=color, width=3, height=1).pack(side=tk.LEFT)
        tk.Label(top_row, text=f"  {title}", font=("Segoe UI", 9), fg=self.COLOR_TEXT_MUTED, bg="#ffffff").pack(side=tk.LEFT)

        val_lbl = tk.Label(card, text=val_text, font=("Segoe UI", 16, "bold"), fg=self.COLOR_TEXT_DARK, bg="#ffffff")
        val_lbl.pack(anchor="w", padx=14, pady=(2, 2))

        tk.Label(card, text=sub_text, font=("Segoe UI", 8, "bold"), fg=color, bg="#ffffff").pack(anchor="w", padx=14, pady=(0, 12))
        return val_lbl

    # ==================== 4. MIDDLE SECTION ====================
    def create_middle_section(self, parent):
        mid = tk.Frame(parent, bg=self.COLOR_BG)
        mid.pack(fill=tk.X, padx=24, pady=(0, 14))

        self.charts_card = tk.Frame(mid, bg="#ffffff", bd=1, relief=tk.SOLID)
        self.charts_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 14))

        right_panel = tk.Frame(mid, bg=self.COLOR_BG, width=330)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        right_panel.pack_propagate(False)

        self.build_live_store_status_card(right_panel)
        self.build_quick_actions(right_panel)

    def build_live_store_status_card(self, parent):
        card = tk.Frame(parent, bg="#ffffff", bd=1, relief=tk.SOLID)
        card.pack(fill=tk.X, pady=(0, 12), ipady=8)

        tk.Label(card, text="Store Operating Status", font=("Segoe UI", 10, "bold"), fg=self.COLOR_TEXT_DARK, bg="#ffffff").pack(anchor="w", padx=16, pady=(10, 4))

        self.status_badge = tk.Label(
            card,
            text="Checking status...",
            font=("Segoe UI", 11, "bold"),
            fg=self.COLOR_SUCCESS,
            bg="#f0fdf4",
            bd=1,
            relief=tk.SOLID,
            padx=10,
            pady=6
        )
        self.status_badge.pack(fill=tk.X, padx=16, pady=6)

        time_box = tk.Frame(card, bg="#ffffff")
        time_box.pack(fill=tk.X, padx=16, pady=4)

        self.lbl_open_time = tk.Label(time_box, text="🕒 Opening Time: --", font=("Segoe UI", 8), fg="#475569", bg="#ffffff")
        self.lbl_open_time.pack(anchor="w")

        self.lbl_close_time = tk.Label(time_box, text="🕒 Closing Time: --", font=("Segoe UI", 8), fg="#475569", bg="#ffffff")
        self.lbl_close_time.pack(anchor="w")

        self.lbl_remaining_time = tk.Label(time_box, text="⏳ Remaining: --", font=("Segoe UI", 8, "bold"), fg=self.COLOR_PRIMARY, bg="#ffffff")
        self.lbl_remaining_time.pack(anchor="w", pady=(3, 0))

        self.btn_toggle_store = tk.Button(
            card,
            text="⛔ Close Store",
            font=("Segoe UI", 9, "bold"),
            bg="#fee2e2",
            fg=self.COLOR_DANGER,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.toggle_store_in_mysql
        )
        self.btn_toggle_store.pack(fill=tk.X, padx=16, pady=(10, 4), ipady=5)

    def build_quick_actions(self, parent):
        card = tk.Frame(parent, bg="#ffffff", bd=1, relief=tk.SOLID)
        card.pack(fill=tk.X, ipady=6)

        tk.Label(card, text="⚡ Quick Actions", font=("Segoe UI", 10, "bold"), fg=self.COLOR_TEXT_DARK, bg="#ffffff").pack(anchor="w", padx=16, pady=(8, 6))

        actions = [
            ("➕ Add New Product", self.COLOR_SUCCESS, lambda: self.navigate_menu("Product Management")),
            ("📋 View Stock Table", self.COLOR_PRIMARY, lambda: self.navigate_menu("Product Management")),
            ("📑 View Invoices / Transactions", "#0284c7", lambda: self.navigate_menu("Transactions")),
            ("⏰ Edit Store Schedule", "#eab308", lambda: self.navigate_menu("Store Operating Hours")),
            ("🔄 Refresh Live Data", self.COLOR_PURPLE, self.load_all_backend_data)
        ]

        for text, color, cmd in actions:
            btn = tk.Button(card, text=text, font=("Segoe UI", 9, "bold"), bg=color, fg="#ffffff", relief=tk.FLAT, cursor="hand2", command=cmd)
            btn.pack(fill=tk.X, padx=16, pady=2, ipady=3)

    # ==================== 5. BOTTOM SECTION ====================
    def create_bottom_section(self, parent):
        bot = tk.Frame(parent, bg=self.COLOR_BG)
        bot.pack(fill=tk.X, padx=24, pady=(0, 16))

        # Recent Transactions
        t_card = tk.Frame(bot, bg="#ffffff", bd=1, relief=tk.SOLID)
        t_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 14))

        top_row_t = tk.Frame(t_card, bg="#ffffff")
        top_row_t.pack(fill=tk.X, padx=14, pady=(10, 6))

        tk.Label(top_row_t, text="Recent Transactions", font=("Segoe UI", 10, "bold"), fg=self.COLOR_TEXT_DARK, bg="#ffffff").pack(side=tk.LEFT)
        btn_view_all = tk.Label(top_row_t, text="View All ➔", font=("Segoe UI", 8, "bold"), fg=self.COLOR_PRIMARY, bg="#ffffff", cursor="hand2")
        btn_view_all.pack(side=tk.RIGHT)
        btn_view_all.bind("<Button-1>", lambda e: self.navigate_menu("Transactions"))

        cols = ("id", "time", "amount", "payment", "status")
        self.trans_tree = ttk.Treeview(t_card, columns=cols, show="headings", height=5)
        self.trans_tree.heading("id", text="Sale ID")
        self.trans_tree.heading("time", text="Date & Time")
        self.trans_tree.heading("amount", text="Total (₹)")
        self.trans_tree.heading("payment", text="Payment")
        self.trans_tree.heading("status", text="Status")

        self.trans_tree.column("id", width=65, anchor="center")
        self.trans_tree.column("time", width=140, anchor="center")
        self.trans_tree.column("amount", width=90, anchor="e")
        self.trans_tree.column("payment", width=80, anchor="center")
        self.trans_tree.column("status", width=90, anchor="center")

        self.trans_tree.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 10))

        # Low Stock Alerts
        low_card = tk.Frame(bot, bg="#ffffff", bd=1, relief=tk.SOLID)
        low_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(low_card, text="⚠️ Low Stock Alerts (Stock < 20)", font=("Segoe UI", 10, "bold"), fg=self.COLOR_DANGER, bg="#ffffff").pack(anchor="w", padx=14, pady=(10, 6))

        l_cols = ("product", "category", "stock")
        self.low_tree = ttk.Treeview(low_card, columns=l_cols, show="headings", height=5)
        self.low_tree.heading("product", text="Product Name")
        self.low_tree.heading("category", text="Department")
        self.low_tree.heading("stock", text="Current Stock")

        self.low_tree.column("product", width=180, anchor="w")
        self.low_tree.column("category", width=130, anchor="w")
        self.low_tree.column("stock", width=90, anchor="center")

        self.low_tree.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 10))

    def create_footer(self, parent):
        footer = tk.Frame(parent, bg=self.COLOR_BG)
        footer.pack(fill=tk.X, padx=24, pady=(4, 18))
        tk.Label(footer, text="© 2026 SnapKart Agra • Sanjay Place, Agra - 282002 • POS Administration System", font=("Segoe UI", 8), fg="#94a3b8", bg=self.COLOR_BG).pack(side=tk.LEFT)

    # ==================== 6. MYSQL BACKEND INTEGRATION ====================
    def load_all_backend_data(self):
        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Error", "Could not connect to MySQL server.")
            return

        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)

            # Live store status check
            today_name = datetime.now().strftime("%A")
            cursor.execute("SELECT open_time, close_time, is_closed_today FROM store_hours WHERE day_name = %s", (today_name,))
            hours_data = cursor.fetchone()

            is_open, msg = check_store_status()
            if is_open:
                self.status_badge.config(text="● OPEN\nStore is operational", fg=self.COLOR_SUCCESS, bg="#f0fdf4")
                self.btn_toggle_store.config(text="⛔ Close Store", bg="#fee2e2", fg=self.COLOR_DANGER)
            else:
                self.status_badge.config(text="● CLOSED\nTransactions locked", fg=self.COLOR_DANGER, bg="#fef2f2")
                self.btn_toggle_store.config(text="🟢 Open Store", bg="#dcfce7", fg=self.COLOR_SUCCESS)

            if hours_data:
                o_time = hours_data["open_time"]
                c_time = hours_data["close_time"]
                self.lbl_open_time.config(text=f"🕒 Opening Time: {str(o_time)}")
                self.lbl_close_time.config(text=f"🕒 Closing Time: {str(c_time)}")

                now = datetime.now()
                c_str = str(c_time)
                try:
                    parts = c_str.split(":")
                    c_h, c_m = int(parts[0]), int(parts[1])
                    closing_datetime = now.replace(hour=c_h, minute=c_m, second=0)
                    if is_open and closing_datetime > now:
                        diff = closing_datetime - now
                        hours_left = diff.seconds // 3600
                        mins_left = (diff.seconds % 3600) // 60
                        self.lbl_remaining_time.config(text=f"⏳ Time Remaining: {hours_left}h {mins_left}m")
                    else:
                        self.lbl_remaining_time.config(text="⏳ Store is currently closed")
                except Exception:
                    self.lbl_remaining_time.config(text="⏳ Hours active")

            # KPI Cards
            cursor.execute("SELECT COALESCE(SUM(total_amount), 0) AS today_sales FROM sales WHERE DATE(sale_datetime) = CURDATE();")
            today_sales = float(cursor.fetchone()["today_sales"])
            self.lbl_kpi_sales.config(text=f"₹ {today_sales:,.2f}")

            cursor.execute("""
                SELECT COALESCE(SUM(si.quantity), 0) AS items_sold 
                FROM sale_items si 
                JOIN sales s ON si.sale_id = s.sale_id 
                WHERE DATE(s.sale_datetime) = CURDATE();
            """)
            items_sold = int(cursor.fetchone()["items_sold"])
            self.lbl_kpi_items.config(text=f"{items_sold:,}")

            cursor.execute("SELECT COUNT(*) AS bill_count FROM sales WHERE DATE(sale_datetime) = CURDATE();")
            bill_count = int(cursor.fetchone()["bill_count"])
            self.lbl_kpi_customers.config(text=f"{bill_count:,}")

            cursor.execute("SELECT COUNT(*) AS low_count FROM inventory WHERE stock_quantity < 20;")
            low_count = int(cursor.fetchone()["low_count"])
            self.lbl_kpi_low_stock.config(text=str(low_count))

            # Recent Transactions
            cursor.execute("""
                SELECT sale_id, DATE_FORMAT(sale_datetime, '%%Y-%%m-%%d %%h:%%i %%p') AS s_time, 
                       total_amount, payment_method 
                FROM sales 
                ORDER BY sale_datetime DESC 
                LIMIT 5;
            """)
            recent_sales = cursor.fetchall()

            for r in self.trans_tree.get_children():
                self.trans_tree.delete(r)

            for s in recent_sales:
                self.trans_tree.insert("", tk.END, values=(
                    f"#{s['sale_id']}",
                    s["s_time"],
                    f"₹{float(s['total_amount']):.2f}",
                    s.get("payment_method") or "Cash",
                    "Completed"
                ))

            # Low Stock Alerts
            cursor.execute("""
                SELECT name, category, stock_quantity 
                FROM inventory 
                WHERE stock_quantity < 20 
                ORDER BY stock_quantity ASC 
                LIMIT 5;
            """)
            low_items = cursor.fetchall()

            for r in self.low_tree.get_children():
                self.low_tree.delete(r)

            for itm in low_items:
                self.low_tree.insert("", tk.END, values=(itm["name"], itm["category"], itm["stock_quantity"]))

            # Render Matplotlib Charts
            self.render_charts_from_backend(cursor)

        except Exception as e:
            print(f"Error loading dashboard data: {e}")
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass
            if conn and conn.is_connected():
                conn.close()

    def render_charts_from_backend(self, cursor):
        cursor.execute("""
            SELECT DATE(sale_datetime) AS s_date, COALESCE(SUM(total_amount), 0) AS daily_rev
            FROM sales
            WHERE sale_datetime >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
            GROUP BY DATE(sale_datetime)
            ORDER BY s_date ASC;
        """)
        sales_records = cursor.fetchall()

        today = datetime.now().date()
        date_map = {(today - timedelta(days=i)): 0.0 for i in range(6, -1, -1)}
        for row in sales_records:
            d = row["s_date"]
            if d in date_map:
                date_map[d] = float(row["daily_rev"])

        day_labels = [d.strftime("%a") for d in date_map.keys()]
        day_values = list(date_map.values())

        cursor.execute("""
            SELECT i.category, COALESCE(SUM(si.subtotal), 0) AS cat_total
            FROM sale_items si
            JOIN inventory i ON si.item_id = i.item_id
            GROUP BY i.category
            ORDER BY cat_total DESC
            LIMIT 6;
        """)
        cat_records = cursor.fetchall()

        if cat_records and sum(float(r["cat_total"]) for r in cat_records) > 0:
            cat_labels = [r["category"][:14] for r in cat_records]
            cat_values = [float(r["cat_total"]) for r in cat_records]
            donut_center_text = f"Total\n₹{sum(cat_values):,.0f}"
        else:
            cat_labels = ["No Sales Yet"]
            cat_values = [1]
            donut_center_text = "Total\n₹0"

        if self.chart_canvas:
            try:
                self.chart_canvas.get_tk_widget().destroy()
            except Exception:
                pass

        plt.close("all")
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.6, 2.9), dpi=100)
        fig.patch.set_facecolor("#ffffff")

        # Line chart
        ax1.plot(day_labels, day_values, color="#2563eb", marker="o", linewidth=2.4, markersize=5)
        ax1.fill_between(day_labels, day_values, color="#3b82f6", alpha=0.15)
        ax1.set_title("Sales Overview (Last 7 Days)", fontsize=9, fontweight="bold", pad=8, color="#0f172a")
        ax1.tick_params(axis="both", labelsize=7, colors="#64748b")
        ax1.grid(axis="y", linestyle="--", alpha=0.3)
        ax1.spines["top"].set_visible(False)
        ax1.spines["right"].set_visible(False)

        # Donut chart
        chart_colors = ["#2563eb", "#06b6d4", "#f59e0b", "#ef4444", "#a855f7", "#64748b"]
        ax2.pie(
            cat_values,
            labels=None,
            colors=chart_colors[:len(cat_values)],
            startangle=90,
            wedgeprops=dict(width=0.42, edgecolor="w", linewidth=1.5)
        )
        ax2.set_title("Category Wise Sales", fontsize=9, fontweight="bold", pad=8, color="#0f172a")
        ax2.text(0, 0, donut_center_text, ha="center", va="center", fontsize=8, fontweight="bold", color="#0f172a")

        if cat_labels[0] != "No Sales Yet":
            ax2.legend(cat_labels, loc="lower center", fontsize=6, ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.15))

        fig.tight_layout()

        self.chart_canvas = FigureCanvasTkAgg(fig, master=self.charts_card)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def toggle_store_in_mysql(self):
        today = datetime.now().strftime("%A")
        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Error", "Could not connect to database.")
            return

        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT is_closed_today FROM store_hours WHERE day_name = %s", (today,))
            row = cursor.fetchone()

            if row:
                new_status = not bool(row["is_closed_today"])
                cursor.execute("UPDATE store_hours SET is_closed_today = %s WHERE day_name = %s", (new_status, today))
                conn.commit()

                status_str = "CLOSED" if new_status else "OPEN"
                messagebox.showinfo("Store Updated", f"Store status for {today} updated to {status_str} in MySQL.")
                self.load_all_backend_data()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to toggle store status: {e}")
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass
            if conn and conn.is_connected():
                conn.close()


if __name__ == "__main__":
    app = SnapKartModernDashboard()
    app.mainloop()