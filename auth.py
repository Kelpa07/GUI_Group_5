import re
import tkinter as tk
from tkinter import messagebox

import database
from passwords import ITERATIONS, hash_password, verify_password
from theme import (
    BG, CARD, MUTED, TEAL, TEAL_DARK, TEXT, WHITE,
    Button, Field, font,
)

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


# ---------------- VALIDATION ----------------

def validate_name(name, field):
    if not name:
        field.set_error("Full name is required.")
        return False
    if any(c.isdigit() for c in name):
        field.set_error("Name cannot contain numbers.")
        return False
    return True


def validate_email(email, field):
    if not email:
        field.set_error("Email address is required.")
        return False
    if not EMAIL_PATTERN.match(email):
        field.set_error("Enter a valid email, for example name@sce.rub.edu.bt")
        return False
    return True


def validate_password(password, field):
    if not password:
        field.set_error("Password is required.")
        return False
    if len(password) < 6:
        field.set_error("Password must be at least 6 characters.")
        return False
    if not any(c.isupper() for c in password):
        field.set_error("Password needs an uppercase letter.")
        return False
    if not any(c.islower() for c in password):
        field.set_error("Password needs a lowercase letter.")
        return False
    if not any(c.isdigit() for c in password):
        field.set_error("Password needs a number.")
        return False
    return True


# ---------------- SCREEN ----------------

class AuthFrame(tk.Frame):
    """The first screen the user sees. It swaps between Sign Up and Log In."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.mode = "signup"

        self._build_brand()
        self.form = tk.Frame(self, bg=CARD)
        self.form.place(relx=0.5, rely=0, relwidth=0.5, relheight=1)

        self._show_signup()

    # ---------- shared left panel ----------

    def _build_brand(self):
        panel = tk.Frame(self, bg=TEAL)
        panel.place(relx=0, rely=0, relwidth=0.5, relheight=1)

        title_row = tk.Frame(panel, bg=TEAL)
        title_row.pack(anchor="center", pady=(90, 0))

        icon = tk.Canvas(title_row, width=40, height=40, bg=TEAL, highlightthickness=0, bd=0)
        icon.pack(side="left", padx=(0, 12))
        # A simple graduation-cap mark drawn with canvas shapes.
        icon.create_polygon(4, 16, 20, 8, 36, 16, 20, 24, fill=WHITE, outline=WHITE)
        icon.create_line(12, 20, 12, 30, fill=WHITE, width=2)
        icon.create_line(12, 30, 28, 30, fill=WHITE, width=2)
        icon.create_line(34, 17, 34, 29, fill=WHITE, width=2)

        tk.Label(title_row, text="AttendTrack", font=("Segoe UI", 26, "bold"), bg=TEAL, fg=WHITE).pack(side="left")

        tk.Label(
            panel,
            text="Smart Attendance Management for Educators.\n"
                 "Record daily status, evaluate performance,\n"
                 "and track analytics effortlessly.",
            font=font(12),
            bg=TEAL,
            fg=WHITE,
            justify="center",
        ).pack(anchor="center", pady=(26, 0), padx=40)

        tk.Label(
            panel,
            text="© 2026 AttendTrack · PRG 304 Group 5",
            font=font(9),
            bg=TEAL,
            fg="#CCFBF5",
        ).place(relx=0.5, rely=0.94, anchor="center")
        return panel

    # ---------- mode switching ----------

    def _clear_form(self):
        for child in self.form.winfo_children():
            child.destroy()

    def _show_signup(self):
        self.mode = "signup"
        self._clear_form()
        self._heading("Create your Account", "Join other educators managing classrooms efficiently.")

        self.name_field = Field(self.form, "Full Name", tk.StringVar(), placeholder="e.g. Karma Chimi Rinzin")
        self.email_field = Field(self.form, "Email Address", tk.StringVar(), placeholder="e.g. 08230139.sce@rub.edu.bt")
        self.password_field = Field(self.form, "Password", tk.StringVar(), show="•")
        self.confirm_field = Field(self.form, "Confirm Password", tk.StringVar(), show="•")

        for f in (self.name_field, self.email_field, self.password_field, self.confirm_field):
            f.pack(fill="x", pady=(2, 4), padx=60)

        Button(self.form, "Sign Up", self.do_signup, "primary").pack(fill="x", ipady=8, pady=(14, 6), padx=60)
        self._switch_link("Already have an account?", "Log In", self._show_login)

    def _show_login(self):
        self.mode = "login"
        self._clear_form()
        self._heading("Welcome Back", "Sign in to continue tracking your classroom.")

        self.login_email = Field(self.form, "Email Address", tk.StringVar(), placeholder="your.email@sce.rub.edu.bt")
        self.login_password = Field(self.form, "Password", tk.StringVar(), show="•")
        self.login_email.pack(fill="x", pady=(2, 4), padx=60)
        self.login_password.pack(fill="x", pady=(2, 4), padx=60)

        Button(self.form, "Log In", self.do_login, "primary").pack(fill="x", ipady=8, pady=(14, 6), padx=60)
        self._switch_link("Don't have an account?", "Sign Up", self._show_signup)

    def _heading(self, title, subtitle):
        tk.Label(self.form, text=title, font=("Segoe UI", 26, "bold"), bg=CARD, fg=TEXT).pack(
            anchor="w", padx=60, pady=(70, 2)
        )
        tk.Label(self.form, text=subtitle, font=font(11), bg=CARD, fg=MUTED, wraplength=380, justify="left").pack(
            anchor="w", padx=60, pady=(0, 22)
        )

    def _switch_link(self, question, action, command):
        row = tk.Frame(self.form, bg=CARD)
        row.pack(pady=(2, 0))
        tk.Label(row, text=question + " ", font=font(10), bg=CARD, fg=MUTED).pack(side="left")
        link = tk.Label(row, text=action, font=font(10, True), bg=CARD, fg=TEAL, cursor="hand2")
        link.pack(side="left")
        link.bind("<Button-1>", lambda e: command())
        link.bind("<Enter>", lambda e: link.config(fg=TEAL_DARK, underline=True))
        link.bind("<Leave>", lambda e: link.config(fg=TEAL, underline=False))

    # ---------- actions ----------

    def do_signup(self):
        for f in (self.name_field, self.email_field, self.password_field, self.confirm_field):
            f.clear_error()

        name = self.name_field.get()
        email = self.email_field.get().lower()
        password = self.password_field.variable.get()
        confirm = self.confirm_field.variable.get()

        valid = True
        valid = validate_name(name, self.name_field) and valid
        valid = validate_email(email, self.email_field) and valid
        valid = validate_password(password, self.password_field) and valid

        if not confirm:
            self.confirm_field.set_error("Please confirm your password.")
            valid = False
        elif confirm != password:
            self.confirm_field.set_error("Passwords do not match.")
            valid = False

        if not valid:
            return

        if database.email_taken(email):
            self.email_field.set_error("This email is already registered. Please log in.")
            return

        try:
            user_id = database.add_user(name, email, hash_password(password))
        except Exception as error:
            messagebox.showerror("Registration Failed", "Could not save your account:\n" + str(error))
            return

        user = database.find_user_by_id(user_id)
        messagebox.showinfo("Account Created", "Welcome, " + name + "! Your account is ready.")
        self.app.start_session(user)

    def do_login(self):
        self.login_email.clear_error()
        self.login_password.clear_error()

        email = self.login_email.get().lower()
        password = self.login_password.variable.get()

        valid = validate_email(email, self.login_email)
        if not password:
            self.login_password.set_error("Password is required.")
            valid = False
        if not valid:
            return

        user = database.find_user_by_email(email)
        if user is None or not verify_password(password, user["password_hash"]):
            messagebox.showerror("Login Failed", "The email or password you entered is incorrect.")
            return

        self.app.start_session(user)
