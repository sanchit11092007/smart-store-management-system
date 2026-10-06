import tkinter as tk
from tkinter import ttk, messagebox
from database.db_connection import get_db_connection
from common.store_status import check_store_status


class StoreSettingsFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        self.day_entries = {}
        self.closed_vars = {}

        self.create_header()
        self.create_status_banner()
        self.create_hours_table()
        self.load_current_hours()

    def create_header(self):
        header_frame = tk.Frame(self, bg="#1e293b", height=60)
        header_frame.pack(fill=tk.X, pady=(0, 15))

        title_lbl = tk.Label(
            header_frame, 
            text="Store Business Hours & Operational Control", 
            font=("Segoe UI", 14, "bold"), 
            bg="#1e293b", 
            fg="#ffffff"
        )
        title_lbl.pack(side=tk.LEFT, padx=15, pady=12)

    def create_status_banner(self):
        self.banner_frame = tk.Frame(self, bg="#f1f5f9", relief=tk.RIDGE, bd=1)
        self.banner_frame.pack(fill=tk.X, pady=(0, 15), ipady=8)

        self.status_indicator = tk.Label(
            self.banner_frame,
            text="LIVE STORE STATUS: CHECKING...",
            font=("Segoe UI", 11, "bold"),
            bg="#f1f5f9",
            fg="#334155"
        )
        self.status_indicator.pack(side=tk.LEFT, padx=15)

        ttk.Button(
            self.banner_frame, 
            text="Refresh Live Status", 
            command=self.refresh_live_status
        ).pack(side=tk.RIGHT, padx=15)

    def create_hours_table(self):
        container = ttk.LabelFrame(self, text="Weekly Schedule Configuration (24-Hour Format: HH:MM:SS)")
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Header titles
        headers = ["Day of Week", "Opening Time", "Closing Time", "Force Closed Today"]
        cols_weight = [2, 2, 2, 2]

        for col_idx, (header_text, weight) in enumerate(zip(headers, cols_weight)):
            lbl = tk.Label(
                container, 
                text=header_text, 
                font=("Segoe UI", 10, "bold"), 
                bg="#e2e8f0", 
                pady=6
            )
            lbl.grid(row=0, column=col_idx, sticky="ew", padx=2, pady=4)
            container.columnconfigure(col_idx, weight=weight)

        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        for idx, day in enumerate(days, start=1):
            # Day label
            day_lbl = tk.Label(container, text=day, font=("Segoe UI", 10))
            day_lbl.grid(row=idx, column=0, padx=10, pady=6, sticky="w")

            # Open time entry
            open_entry = ttk.Entry(container, width=15, justify="center")
            open_entry.grid(row=idx, column=1, padx=10, pady=6)

            # Close time entry
            close_entry = ttk.Entry(container, width=15, justify="center")
            close_entry.grid(row=idx, column=2, padx=10, pady=6)

            # Force closed checkbox
            is_closed = tk.BooleanVar()
            chk = ttk.Checkbutton(container, text="Mark Closed", variable=is_closed)
            chk.grid(row=idx, column=3, padx=10, pady=6)

            self.day_entries[day] = (open_entry, close_entry)
            self.closed_vars[day] = is_closed

        # Save button row
        action_frame = ttk.Frame(container)
        action_frame.grid(row=len(days) + 1, column=0, columnspan=4, pady=15)

        save_btn = tk.Button(
            action_frame,
            text="Save Operating Schedule",
            font=("Segoe UI", 10, "bold"),
            bg="#0284c7",
            fg="white",
            padx=15,
            pady=6,
            relief=tk.FLAT,
            command=self.save_schedule
        )
        save_btn.pack(side=tk.LEFT, padx=10)

        reload_btn = tk.Button(
            action_frame,
            text="Discard & Reload",
            font=("Segoe UI", 10),
            bg="#94a3b8",
            fg="white",
            padx=12,
            pady=6,
            relief=tk.FLAT,
            command=self.load_current_hours
        )
        reload_btn.pack(side=tk.LEFT, padx=10)

    def load_current_hours(self):
        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Error", "Could not connect to database.")
            return

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT day_name, open_time, close_time, is_closed_today FROM store_hours")
        records = cursor.fetchall()
        cursor.close()
        conn.close()

        for rec in records:
            day = rec["day_name"]
            if day in self.day_entries:
                open_entry, close_entry = self.day_entries[day]
                open_entry.delete(0, tk.END)
                open_entry.insert(0, str(rec["open_time"]))

                close_entry.delete(0, tk.END)
                close_entry.insert(0, str(rec["close_time"]))

                self.closed_vars[day].set(bool(rec["is_closed_today"]))

        self.refresh_live_status()

    def refresh_live_status(self):
        is_open, msg = check_store_status()
        if is_open:
            self.status_indicator.config(
                text=f"● LIVE STATUS: OPEN ({msg})", 
                fg="#16a34a"
            )
        else:
            self.status_indicator.config(
                text=f"● LIVE STATUS: CLOSED ({msg})", 
                fg="#dc2626"
            )

    def save_schedule(self):
        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Error", "Could not connect to database.")
            return

        cursor = conn.cursor()
        query = """
            UPDATE store_hours
            SET open_time = %s, close_time = %s, is_closed_today = %s
            WHERE day_name = %s
        """

        try:
            for day, (open_entry, close_entry) in self.day_entries.items():
                open_val = open_entry.get().strip()
                close_val = close_entry.get().strip()
                closed_val = self.closed_vars[day].get()

                cursor.execute(query, (open_val, close_val, closed_val, day))

            conn.commit()
            messagebox.showinfo("Success", "Operating schedule saved and updated in real-time!")
            self.refresh_live_status()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save schedule: {e}")
        finally:
            cursor.close()
            conn.close()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("SnapKart - Business Hours Setting Panel")
    root.geometry("850x620")
    app = StoreSettingsFrame(root)
    root.mainloop()