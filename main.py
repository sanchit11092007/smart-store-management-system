import subprocess
import sys
import tkinter as tk
from tkinter import messagebox
from common.store_status import check_store_status


class SnapKartLauncher(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("SnapKart - Retail Application Launcher")
        self.geometry("680x540")
        self.resizable(False, False)
        self.configure(bg="#0f172a")

        self.create_ui()
        self.update_live_badge()

    def create_ui(self):
        # 1. Header & Branding
        header_frame = tk.Frame(self, bg="#0f172a")
        header_frame.pack(fill=tk.X, pady=(35, 10))

        tk.Label(
            header_frame,
            text="🛒 SnapKart",
            font=("Segoe UI", 24, "bold"),
            fg="#38bdf8",
            bg="#0f172a"
        ).pack()

        tk.Label(
            header_frame,
            text="Business Hours Aware Billing & Inventory Management System",
            font=("Segoe UI", 10),
            fg="#94a3b8",
            bg="#0f172a"
        ).pack(pady=(4, 0))

        # 2. Live Store Status Badge
        self.status_badge = tk.Label(
            self,
            text="Checking Store Hours...",
            font=("Segoe UI", 10, "bold"),
            bg="#1e293b",
            fg="#cbd5e1",
            padx=14,
            pady=6,
            relief=tk.SOLID,
            bd=1
        )
        self.status_badge.pack(pady=15)

        # 3. Action Cards Frame
        card_container = tk.Frame(self, bg="#0f172a")
        card_container.pack(fill=tk.BOTH, expand=True, padx=40, pady=10)

        # Button 1: Launch Customer App
        self.create_launch_button(
            parent=card_container,
            icon="🛍️",
            title="Launch Customer Storefront",
            subtitle="Shop products, manage cart, and real-time checkout",
            btn_color="#16a34a",
            command=self.open_customer_app
        )

        # Button 2: Launch Admin Dashboard
        self.create_launch_button(
            parent=card_container,
            icon="📊",
            title="Launch Admin Portal",
            subtitle="Inventory tracking, operating hours control, and sales charts",
            btn_color="#2563eb",
            command=self.open_admin_app
        )

        # Button 3: Generate CSV Reports
        self.create_launch_button(
            parent=card_container,
            icon="📈",
            title="Generate Business Reports (CSV)",
            subtitle="Export daily sales breakdown & restock alert spreadsheets",
            btn_color="#7c3aed",
            command=self.run_reports_script
        )

        # 4. Footer
        footer = tk.Label(
            self,
            text="Sanjay Place, Agra - 282002 • Python + Tkinter + MySQL",
            font=("Segoe UI", 8),
            fg="#64748b",
            bg="#0f172a"
        )
        footer.pack(side=tk.BOTTOM, pady=15)

    def create_launch_button(self, parent, icon, title, subtitle, btn_color, command):
        frame = tk.Frame(parent, bg="#1e293b", bd=1, relief=tk.SOLID)
        frame.pack(fill=tk.X, pady=6, ipady=4)

        text_box = tk.Frame(frame, bg="#1e293b")
        text_box.pack(side=tk.LEFT, padx=15, pady=8)

        tk.Label(
            text_box,
            text=f"{icon}  {title}",
            font=("Segoe UI", 11, "bold"),
            fg="#ffffff",
            bg="#1e293b"
        ).pack(anchor="w")

        tk.Label(
            text_box,
            text=subtitle,
            font=("Segoe UI", 8),
            fg="#94a3b8",
            bg="#1e293b"
        ).pack(anchor="w")

        launch_btn = tk.Button(
            frame,
            text="Open ➔",
            font=("Segoe UI", 9, "bold"),
            bg=btn_color,
            fg="#ffffff",
            activebackground="#ffffff",
            relief=tk.FLAT,
            padx=16,
            pady=4,
            cursor="hand2",
            command=command
        )
        launch_btn.pack(side=tk.RIGHT, padx=15)

    def update_live_badge(self):
        is_open, msg = check_store_status()
        if is_open:
            self.status_badge.config(
                text="● STORE STATUS: OPEN (Accepting Orders)",
                bg="#064e3b",
                fg="#6ee7b7"
            )
        else:
            self.status_badge.config(
                text="● STORE STATUS: CLOSED (Transactions Locked)",
                bg="#7f1d1d",
                fg="#fca5a5"
            )

    def open_customer_app(self):
        subprocess.Popen([sys.executable, "-m", "user_app.user_main"])

    def open_admin_app(self):
        subprocess.Popen([sys.executable, "-m", "admin_app.admin_main"])

    def run_reports_script(self):
        from data_analysis.sales_report import generate_sales_and_inventory_reports
        try:
            generate_sales_and_inventory_reports()
            messagebox.showinfo(
                "Reports Generated",
                "Successfully exported CSV reports to the 'reports/' folder!"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate reports: {e}")


if __name__ == "__main__":
    app = SnapKartLauncher()
    app.mainloop()