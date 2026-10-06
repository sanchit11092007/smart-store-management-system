import os
from datetime import datetime
import pandas as pd
import numpy as np
from database.db_connection import get_db_connection


def generate_sales_and_inventory_reports(export_dir="reports"):
    """
    Analyzes sales and inventory using Pandas and NumPy,
    then exports summary CSV reports.
    """
    conn = get_db_connection()
    if not conn:
        print("Database connection failed. Cannot generate reports.")
        return

    # Ensure output folder exists
    os.makedirs(export_dir, exist_ok=True)

    print("\n" + "=" * 50)
    print("      SNAPKART BUSINESS REPORT GENERATOR")
    print("=" * 50)

    try:
        # 1. Load data into Pandas DataFrames
        sales_df = pd.read_sql("SELECT * FROM sales", conn)
        items_df = pd.read_sql("SELECT * FROM sale_items", conn)
        inventory_df = pd.read_sql("SELECT * FROM inventory", conn)

        # ---------------------------------------------------------------------
        # A. SALES PERFORMANCE METRICS (NumPy & Pandas)
        # ---------------------------------------------------------------------
        if not sales_df.empty:
            sales_df["sale_datetime"] = pd.to_datetime(sales_df["sale_datetime"])
            total_revenue = float(np.sum(sales_df["total_amount"]))
            total_orders = len(sales_df)
            avg_order_val = float(np.mean(sales_df["total_amount"]))
            median_order_val = float(np.median(sales_df["total_amount"]))

            print(f"\n[+] Sales Overview:")
            print(f"    - Total Revenue Generated : ₹ {total_revenue:,.2f}")
            print(f"    - Total Orders Placed     : {total_orders:,}")
            print(f"    - Average Order Value (AOV): ₹ {avg_order_val:,.2f}")
            print(f"    - Median Order Value      : ₹ {median_order_val:,.2f}")

            # Merge items with product names for product breakdown
            merged_items = items_df.merge(inventory_df, on="item_id", how="left")
            top_products = (
                merged_items.groupby("name")
                .agg(units_sold=("quantity", "sum"), total_sales=("subtotal", "sum"))
                .sort_values(by="units_sold", ascending=False)
                .head(10)
            )

            # Export Daily Sales Summary CSV
            sales_summary_path = os.path.join(export_dir, "daily_sales_summary.csv")
            sales_df.to_csv(sales_summary_path, index=False)
            print(f"    - Saved Sales Report to   : {sales_summary_path}")

        # ---------------------------------------------------------------------
        # B. INVENTORY & RESTOCK ANALYSIS
        # ---------------------------------------------------------------------
        if not inventory_df.empty:
            total_skus = len(inventory_df)
            total_stock_units = int(np.sum(inventory_df["stock_quantity"]))
            total_stock_value = float(np.sum(inventory_df["price"] * inventory_df["stock_quantity"]))

            # Filter items requiring urgent reorder (stock < 20)
            reorder_df = inventory_df[inventory_df["stock_quantity"] < 20].copy()
            reorder_df["recommended_reorder_units"] = 50 - reorder_df["stock_quantity"]

            print(f"\n[+] Inventory Status:")
            print(f"    - Total Product Catalog   : {total_skus} items")
            print(f"    - Total Warehouse Units   : {total_stock_units:,} units")
            print(f"    - Total Valuation         : ₹ {total_stock_value:,.2f}")
            print(f"    - Critical Reorder Items  : {len(reorder_df)} products")

            # Export Restock Report CSV
            restock_path = os.path.join(export_dir, "inventory_restock_report.csv")
            reorder_df.to_csv(restock_path, index=False)
            print(f"    - Saved Restock Report to : {restock_path}")

        print("\n" + "=" * 50)
        print("  All CSV Reports Generated Successfully!")
        print("=" * 50 + "\n")

    except Exception as e:
        print(f"Error generating reports: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    generate_sales_and_inventory_reports()