import tkinter as tk
from tkinter import messagebox
from common.auth import register_customer, login_customer


class AuthDialog(tk.Toplevel):
    def __init__(self, parent, on_login_success):
        super().__init__(parent)

        self.title("SnapKart - Customer Account")
        self.geometry("420x520")
        self.resizable(False, False)
        self.configure(bg="#ffffff")

        # Keep window in front
        self.transient(parent)
        self.grab_set()

        self.on_login_success = on_login_success
        self.is_login_view = True

        self.create_header()
        self.create_form_container()
        self.show_login_form()

    def create_header(self):
        header = tk.Frame(self, bg="#ffffff")
        header.pack(fill=tk.X, padx=30, pady=(25, 10))

        self.lbl_title = tk.Label(
            header,
            text="Welcome to SnapKart",
            font=("Segoe UI", 16, "bold"),
            fg="#0f172a",
            bg="#ffffff"
        )
        self.lbl_title.pack(anchor="w")

        self.lbl_subtitle = tk.Label(
            header,
            text="Log in to manage your orders and speed up checkout",
            font=("Segoe UI", 8),
            fg="#64748b",
            bg="#ffffff"
        )
        self.lbl_subtitle.pack(anchor="w", pady=(2, 0))

    def create_form_container(self):
        self.form_frame = tk.Frame(self, bg="#ffffff")
        self.form_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

    # ------------------ LOGIN VIEW ------------------
    def show_login_form(self):
        self.is_login_view = True
        self.lbl_title.config(text="Welcome Back 👋")
        self.lbl_subtitle.config(text="Enter your credentials to access your SnapKart account")

        for w in self.form_frame.winfo_children():
            w.destroy()

        # Email field
        tk.Label(self.form_frame, text="Email Address", font=("Segoe UI", 9, "bold"), fg="#0f172a", bg="#ffffff").pack(anchor="w", pady=(10, 3))
        self.login_email = tk.Entry(self.form_frame, font=("Segoe UI", 10), bg="#f8fafc", relief=tk.SOLID, bd=1)
        self.login_email.pack(fill=tk.X, ipady=6)

        # Password field
        tk.Label(self.form_frame, text="Password", font=("Segoe UI", 9, "bold"), fg="#0f172a", bg="#ffffff").pack(anchor="w", pady=(14, 3))
        self.login_pwd = tk.Entry(self.form_frame, font=("Segoe UI", 10), bg="#f8fafc", show="•", relief=tk.SOLID, bd=1)
        self.login_pwd.pack(fill=tk.X, ipady=6)

        # Submit Button
        btn_login = tk.Button(
            self.form_frame,
            text="Log In",
            font=("Segoe UI", 10, "bold"),
            bg="#16a34a",
            fg="#ffffff",
            activebackground="#15803d",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.handle_login
        )
        btn_login.pack(fill=tk.X, pady=(22, 10), ipady=6)

        # Toggle to Register
        toggle_box = tk.Frame(self.form_frame, bg="#ffffff")
        toggle_box.pack(pady=10)
        tk.Label(toggle_box, text="Don't have an account? ", font=("Segoe UI", 8), fg="#64748b", bg="#ffffff").pack(side=tk.LEFT)
        btn_switch = tk.Label(toggle_box, text="Create Account", font=("Segoe UI", 8, "bold"), fg="#16a34a", bg="#ffffff", cursor="hand2")
        btn_switch.pack(side=tk.LEFT)
        btn_switch.bind("<Button-1>", lambda e: self.show_register_form())

    # ------------------ SIGN UP VIEW ------------------
    def show_register_form(self):
        self.is_login_view = False
        self.lbl_title.config(text="Create Account 🛒")
        self.lbl_subtitle.config(text="Join SnapKart for faster checkout and order tracking")

        for w in self.form_frame.winfo_children():
            w.destroy()

        # Name
        tk.Label(self.form_frame, text="Full Name", font=("Segoe UI", 8, "bold"), fg="#0f172a", bg="#ffffff").pack(anchor="w", pady=(6, 2))
        self.reg_name = tk.Entry(self.form_frame, font=("Segoe UI", 9), bg="#f8fafc", relief=tk.SOLID, bd=1)
        self.reg_name.pack(fill=tk.X, ipady=4)

        # Email
        tk.Label(self.form_frame, text="Email Address", font=("Segoe UI", 8, "bold"), fg="#0f172a", bg="#ffffff").pack(anchor="w", pady=(8, 2))
        self.reg_email = tk.Entry(self.form_frame, font=("Segoe UI", 9), bg="#f8fafc", relief=tk.SOLID, bd=1)
        self.reg_email.pack(fill=tk.X, ipady=4)

        # Phone
        tk.Label(self.form_frame, text="Phone Number", font=("Segoe UI", 8, "bold"), fg="#0f172a", bg="#ffffff").pack(anchor="w", pady=(8, 2))
        self.reg_phone = tk.Entry(self.form_frame, font=("Segoe UI", 9), bg="#f8fafc", relief=tk.SOLID, bd=1)
        self.reg_phone.pack(fill=tk.X, ipady=4)

        # Password
        tk.Label(self.form_frame, text="Password (min 6 chars)", font=("Segoe UI", 8, "bold"), fg="#0f172a", bg="#ffffff").pack(anchor="w", pady=(8, 2))
        self.reg_pwd = tk.Entry(self.form_frame, font=("Segoe UI", 9), bg="#f8fafc", show="•", relief=tk.SOLID, bd=1)
        self.reg_pwd.pack(fill=tk.X, ipady=4)

        # Submit Button
        btn_reg = tk.Button(
            self.form_frame,
            text="Sign Up",
            font=("Segoe UI", 9, "bold"),
            bg="#16a34a",
            fg="#ffffff",
            activebackground="#15803d",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.handle_register
        )
        btn_reg.pack(fill=tk.X, pady=(16, 8), ipady=5)

        # Toggle to Login
        toggle_box = tk.Frame(self.form_frame, bg="#ffffff")
        toggle_box.pack(pady=4)
        tk.Label(toggle_box, text="Already have an account? ", font=("Segoe UI", 8), fg="#64748b", bg="#ffffff").pack(side=tk.LEFT)
        btn_switch = tk.Label(toggle_box, text="Log In", font=("Segoe UI", 8, "bold"), fg="#16a34a", bg="#ffffff", cursor="hand2")
        btn_switch.pack(side=tk.LEFT)
        btn_switch.bind("<Button-1>", lambda e: self.show_login_form())

    # ------------------ ACTIONS ------------------
    def handle_login(self):
        email = self.login_email.get().strip()
        pwd = self.login_pwd.get().strip()

        ok, user_data, msg = login_customer(email, pwd)
        if ok:
            messagebox.showinfo("Success", msg)
            self.on_login_success(user_data)
            self.destroy()
        else:
            messagebox.showerror("Login Failed", msg)

    def handle_register(self):
        name = self.reg_name.get().strip()
        email = self.reg_email.get().strip()
        phone = self.reg_phone.get().strip()
        pwd = self.reg_pwd.get().strip()

        ok, msg = register_customer(name, email, phone, pwd)
        if ok:
            messagebox.showinfo("Account Created", msg)
            self.show_login_form()
            self.login_email.insert(0, email)
        else:
            messagebox.showerror("Registration Failed", msg)