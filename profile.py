import tkinter as tk
from tkinter import messagebox

import auth
import database
from theme import (
    BG, BORDER, CARD, MUTED, TEAL, TEXT,
    Button, Card, TitleBlock, font, make_entry,
)


class ProfileFrame(tk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.editing = False
        self._build()

    # ---------------- LAYOUT ----------------

    def _build(self):
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=26, pady=(22, 12))
        TitleBlock(header, "My Profile", "Manage your account details and password").pack(side="left")

        banner = Card(self, padx=20, pady=18)
        banner.pack(fill="x", padx=26)

        avatar = tk.Canvas(banner, width=64, height=64, bg=CARD, highlightthickness=0, bd=0)
        avatar.pack(side="left")
        avatar.create_oval(1, 1, 63, 63, fill="#E2E8F0", outline="#E2E8F0")
        avatar.create_oval(22, 14, 42, 34, fill="#94A3B8", outline="#94A3B8")
        avatar.create_arc(10, 30, 54, 70, start=200, extent=140, fill="#94A3B8", outline="#94A3B8")

        names = tk.Frame(banner, bg=CARD)
        names.pack(side="left", padx=(18, 0))
        self.banner_name = tk.Label(names, text="", font=font(17, True), bg=CARD, fg=TEXT, anchor="w")
        self.banner_name.pack(anchor="w")
        self.banner_meta = tk.Label(names, text="", font=font(10), bg=CARD, fg=MUTED, anchor="w")
        self.banner_meta.pack(anchor="w")

        columns = tk.Frame(self, bg=BG)
        columns.pack(fill="x", padx=26, pady=(16, 22))
        columns.grid_columnconfigure(0, weight=3, uniform="p")
        columns.grid_columnconfigure(1, weight=2, uniform="p")

        self._build_details(columns)
        self._build_password(columns)

    def _build_details(self, parent):
        card = Card(parent, padx=22, pady=20)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 14))

        tk.Label(card, text="Personal Details", font=font(13, True), bg=CARD, fg=TEXT).pack(anchor="w", pady=(0, 12))

        self.name_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.department_var = tk.StringVar()
        self.class_var = tk.StringVar()

        self.entries = {}
        for label, variable in (
            ("Full Name", self.name_var),
            ("Email Address", self.email_var),
            ("Phone Number", self.phone_var),
            ("Department", self.department_var),
            ("Class / Section", self.class_var),
        ):
            tk.Label(card, text=label, font=font(10, True), bg=CARD, fg=TEXT).pack(anchor="w", pady=(8, 0))
            entry = make_entry(card, variable)
            entry.pack(fill="x", ipady=8, pady=(4, 0))
            self.entries[label] = entry

        self.save_button = Button(card, "Edit Profile", self.toggle_edit, "primary", padx=16, pady=8)
        self.save_button.pack(anchor="w", pady=(20, 0))

    def _build_password(self, parent):
        card = Card(parent, padx=22, pady=20)
        card.grid(row=0, column=1, sticky="nsew")

        tk.Label(card, text="Change Password", font=font(13, True), bg=CARD, fg=TEXT).pack(anchor="w", pady=(0, 4))
        tk.Label(
            card,
            text="Passwords are stored hashed with PBKDF2, never as plain text.",
            font=font(9), bg=CARD, fg=MUTED, wraplength=300, justify="left",
        ).pack(anchor="w", pady=(0, 8))

        self.current_var = tk.StringVar()
        self.new_var = tk.StringVar()
        self.confirm_var = tk.StringVar()

        self.current_entry = self._password_row(card, "Current Password", self.current_var)
        self.new_entry = self._password_row(card, "New Password", self.new_var)
        self.confirm_entry = self._password_row(card, "Confirm New Password", self.confirm_var)

        Button(card, "Update Password", self.update_password, "primary", padx=16, pady=8).pack(anchor="w", pady=(18, 0))

    def _password_row(self, parent, label, variable):
        tk.Label(parent, text=label, font=font(10, True), bg=CARD, fg=TEXT).pack(anchor="w", pady=(8, 0))
        entry = tk.Entry(
            parent, textvariable=variable, font=font(11), relief="flat", bg=CARD, fg=TEXT,
            show="•", highlightthickness=1, highlightbackground=BORDER, highlightcolor=TEAL,
            insertbackground=TEXT,
        )
        entry.pack(fill="x", ipady=8, pady=(4, 0))
        entry._variable = variable
        return entry

    def _password_value(self, entry):
        return entry._variable.get()

    # ---------------- ACTIONS ----------------

    def refresh(self):
        user = database.find_user_by_id(self.app.user["id"])
        if user is None:
            return
        self.app.user = user

        self.banner_name.configure(text=user["name"])
        meta = " · ".join([v for v in (user.get("class_label"), user["email"]) if v])
        self.banner_meta.configure(text=meta)

        self.name_var.set(user["name"])
        self.email_var.set(user["email"])
        self.phone_var.set(user.get("phone") or "")
        self.department_var.set(user.get("department") or "")
        self.class_var.set(user.get("class_label") or "")
        self._set_editable(False)

    def toggle_edit(self):
        if self.editing:
            self.save_profile()
        else:
            self._set_editable(True)

    def _set_editable(self, editing):
        self.editing = editing
        state = "normal" if editing else "disabled"
        for entry in self.entries.values():
            entry.configure(state=state, disabledbackground=CARD, disabledforeground=TEXT)
        self.save_button.configure(text="Save Profile" if editing else "Edit Profile")

    def save_profile(self):
        name = self.name_var.get().strip()
        email = self.email_var.get().strip().lower()
        phone = self.phone_var.get().strip()
        department = self.department_var.get().strip()
        class_label = self.class_var.get().strip()

        if not name:
            messagebox.showwarning("Missing Information", "Full name cannot be empty.")
            return
        if any(c.isdigit() for c in name):
            messagebox.showwarning("Invalid Name", "Full name cannot contain numbers.")
            return
        if not auth.EMAIL_PATTERN.match(email):
            messagebox.showwarning("Invalid Email", "Please enter a valid email address.")
            return
        if phone and not phone.replace("+", "").replace(" ", "").replace("-", "").isdigit():
            messagebox.showwarning("Invalid Phone", "Phone number may contain digits, spaces, + and - only.")
            return
        if database.email_taken(email, exclude_user_id=self.app.user["id"]):
            messagebox.showerror("Email In Use", "Another account already uses that email address.")
            return

        database.update_user_profile(
            self.app.user["id"], name, email, phone, department, class_label
        )
        self.app.status_text(database.find_user_by_id(self.app.user["id"]))
        self._set_editable(False)
        self.refresh()
        messagebox.showinfo("Profile Updated", "Your profile details have been saved.")

    def update_password(self):
        current = self._password_value(self.current_entry)
        new = self._password_value(self.new_entry)
        confirm = self._password_value(self.confirm_entry)

        if not current:
            messagebox.showwarning("Missing Information", "Please enter your current password.")
            return
        if not auth.verify_password(current, self.app.user["password_hash"]):
            messagebox.showerror("Incorrect Password", "Your current password is not correct.")
            return

        error = None
        if len(new) < 6:
            error = "New password must be at least 6 characters."
        elif not any(c.isupper() for c in new):
            error = "New password needs an uppercase letter."
        elif not any(c.islower() for c in new):
            error = "New password needs a lowercase letter."
        elif not any(c.isdigit() for c in new):
            error = "New password needs a number."
        elif new == current:
            error = "New password must be different from the current password."
        elif confirm != new:
            error = "New password and confirmation do not match."

        if error:
            messagebox.showwarning("Invalid Password", error)
            return

        database.update_user_password(self.app.user["id"], auth.hash_password(new))
        self.app.user = database.find_user_by_id(self.app.user["id"])
        for entry in (self.current_entry, self.new_entry, self.confirm_entry):
            entry._variable.set("")
        messagebox.showinfo("Password Changed", "Your password has been updated successfully.")
