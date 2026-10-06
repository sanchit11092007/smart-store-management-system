import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from database.db_connection import get_db_connection


class AnalyticsFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        self.canvas = None
        self.create_header()
        self.create_kpi_cards()
        self.create_chart_container()
        self.load_analytics_data()

    def create_header(self):
        header_frame = tk.Frame(self, bg="#0f172a", height=50)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        title = tk.Label(
            header_frame,
            text="SnapKart Business Intelligence & Inventory Analytics",
            font=("Segoe UI", 13, "bold"),
            bg="#0f172a",
            fg="white"
        )
        title.pack(side=tk.LEFT, padx=15, pady=10)

        refresh_btn = tk.Button(
            header_frame,
            text="Refresh Charts",
            font=("Segoe UI", 9, "bold"),
            bg="#0284c7",
            fg="white",
            relief=tk.FLAT,
            padx=10,
            command=self.load_analytics_data
        )
        refresh_btn.pack(side=tk.RIGHT, padx=15, pady=10)

    def create_kpi_cards(self):
        # KPI summary boxes at the top
        cards_frame = tk.Frame(self)
        cards_frame.pack(fill=tk.X, pady=(0, 10))

        # Card 1: Total Products
        self.lbl_total_items = self.make_card(cards_frame, "Total Products", "0", "#0284c7", 0)

        # Card 2: Total Units in Stock
        self.lbl_total_units = self.make_card(cards_frame, "Total Units in Stock", "0", "#16a34a", 1)

        # Card 3: Total Stock Valuation
        self.lbl_total_value = self.make_card(cards_frame, "Total Inventory Value", "₹0.00", "#7c3aed", 2)

        # Card 4: Average Item Price
        self.lbl_avg_price = self.make_card(cards_frame, "Average Item Price", "₹0.00", "#ea580c", 3)

    def make_card(self, parent, title_text, value_text, color, col_index):
        frame = tk.Frame(parent, bg="#f8fafc", relief=tk.SOLID, bd=1)
        frame.grid(row=0, column=col_index, padx=6, sticky="nsew")
        parent.columnconfigure(col_index, weight=1)

        title = tk.Label(frame, text=title_text, font=("Segoe UI", 9), bg="#f8fafc", fg="#64748b")
        title.pack(anchor="w", padx=10, pady=(8, 2))

        val = tk.Label(frame, text=value_text, font=("Segoe UI", 13, "bold"), bg="#f8fafc", fg=color)
        val.pack(anchor="w", padx=10, pady=(0, 8))
        return val

    def create_chart_container(self):
        self.chart_frame = ttk.LabelFrame(self, text="Visual Inventory Distribution")
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=5)

    def load_analytics_data(self):
        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Database Error", "Cannot connect to MySQL database.")
            return

        try:
            # 1. Read inventory table using Pandas
            df = pd.read_sql("SELECT item_id, name, category, price, stock_quantity FROM inventory", conn)

            if df.empty:
                messagebox.showwarning("No Data", "No inventory data found to analyze.")
                return

            # 2. Calculate summary metrics using NumPy and Pandas
            total_items = len(df)
            total_units = int(df["stock_quantity"].sum())
            
            # Inventory Value = Price * Quantity
            total_value = float(np.sum(df["price"].astype(float) * df["stock_quantity"].astype(float)))
            avg_price = float(np.mean(df["price"].astype(float)))

            # Update KPI cards
            self.lbl_total_items.config(text=f"{total_items:,}")
            self.lbl_total_units.config(text=f"{total_units:,}")
            self.lbl_total_value.config(text=f"₹{total_value:,.2f}")
            self.lbl_avg_price.config(text=f"₹{avg_price:,.2f}")

            # 3. Draw charts using Matplotlib
            self.draw_charts(df)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load analytics: {e}")
        finally:
            if conn.is_connected():
                conn.close()

    def draw_charts(self, df):
        # Remove old chart if present
        if self.canvas:
            try:
                self.canvas.get_tk_widget().destroy()
            except Exception:
                pass

        plt.close("all")

        # Create two side-by-side subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2), dpi=100)
        fig.patch.set_facecolor("#f8fafc")

        # Ensure numeric types for groupby operations
        df["price"] = df["price"].astype(float)
        df["stock_quantity"] = df["stock_quantity"].astype(int)

        # Chart 1: Stock Quantity by Category
        category_stock = df.groupby("category")["stock_quantity"].sum().sort_values(ascending=False).head(8)
        bars1 = ax1.barh(category_stock.index, category_stock.values, color="#0284c7")
        ax1.set_title("Top 8 Departments by Stock Volume", fontsize=10, fontweight="bold", pad=8)
        ax1.set_xlabel("Units Available", fontsize=8)
        ax1.invert_yaxis()  # Largest on top
        ax1.tick_params(axis="both", labelsize=7)
        ax1.grid(axis="x", linestyle="--", alpha=0.5)

        # Chart 2: Average Price by Category
        category_price = df.groupby("category")["price"].mean().sort_values(ascending=False).head(8)
        ax2.bar(range(len(category_price)), category_price.values, color="#10b981")
        ax2.set_title("Top 8 Categories by Average Price (₹)", fontsize=10, fontweight="bold", pad=8)
        ax2.set_ylabel("Average Price (₹)", fontsize=8)
        ax2.set_xticks(range(len(category_price)))
        ax2.set_xticklabels([name[:14] for name in category_price.index], rotation=35, ha="right", fontsize=7)
        ax2.tick_params(axis="y", labelsize=8)
        ax2.grid(axis="y", linestyle="--", alpha=0.5)

        fig.tight_layout()

        # Embed into Tkinter
        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("SnapKart - Admin Analytics")
    root.geometry("980x660")
    app = AnalyticsFrame(root)
    root.mainloop()