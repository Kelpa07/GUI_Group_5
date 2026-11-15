import tkinter as tk
from tkinter import messagebox

import database
import sample_data
from theme import (
    BG, CARD, MUTED, TEXT,
    Button, Card, TitleBlock, Toggle, font, make_entry,
)


class SettingsFrame(tk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._build()

    # ---------------- LAYOUT ----------------

    def _build(self):
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=26, pady=(22, 12))
        TitleBlock(header, "Settings", "Configure the institution, academic year and attendance rules").pack(side="left")

        general = Card(self, padx=22, pady=18)
        general.pack(fill="x", padx=26)
        tk.Label(general, text="General Settings", font=font(13, True), bg=CARD, fg=TEXT).pack(anchor="w", pady=(0, 6))

        self.school_var = tk.StringVar()
        self.year_var = tk.StringVar()
        self._field_row(general, "School Name", self.school_var, 40)
        self._field_row(general, "Academic Year", self.year_var, 40)

        attendance = Card(self, padx=22, pady=18)
        attendance.pack(fill="x", padx=26, pady=(14, 0))
        tk.Label(attendance, text="Attendance Settings", font=font(13, True), bg=CARD, fg=TEXT).pack(anchor="w", pady=(0, 6))

        self.late_var = tk.StringVar()
        self.min_var = tk.StringVar()
        self._field_row(attendance, "Late Threshold (Minutes)", self.late_var, 12,
                        hint="Shown as a reminder on the Mark Attendance screen.")
        self._field_row(attendance, "Minimum Attendance Percentage (%)", self.min_var, 12,
                        hint="Students below this value are flagged on Students and Reports.")

        saturday_row = tk.Frame(attendance, bg=CARD)
        saturday_row.pack(fill="x", pady=(12, 0))
        text = tk.Frame(saturday_row, bg=CARD)
        text.pack(side="left")
        tk.Label(text, text="Track Saturdays", font=font(11, True), bg=CARD, fg=TEXT).pack(anchor="w")
        tk.Label(text, text="Allow attendance to be saved for Saturday dates",
                 font=font(9), bg=CARD, fg=MUTED).pack(anchor="w")
        self.saturday_var = tk.BooleanVar(value=False)
        Toggle(saturday_row, self.saturday_var).pack(side="right")

        demo = Card(self, padx=22, pady=18)
        demo.pack(fill="x", padx=26, pady=(14, 0))
        tk.Label(demo, text="Demonstration Data", font=font(13, True), bg=CARD, fg=TEXT).pack(anchor="w", pady=(0, 4))
        tk.Label(
            demo,
            text="Realistic sample students and attendance records for the presentation. "
                 "Demo records are stored in a separate 'Demo Class' and can be removed at any time. "
                 "They are never added automatically.",
            font=font(9), bg=CARD, fg=MUTED, wraplength=760, justify="left",
        ).pack(anchor="w")

        actions = tk.Frame(demo, bg=CARD)
        actions.pack(anchor="w", pady=(12, 0))
        Button(actions, "Load Demo Data", self.load_demo, "primary", padx=14, pady=7).pack(side="left")
        Button(actions, "Remove Demo Data", self.remove_demo, "ghost", padx=14, pady=7).pack(side="left", padx=(10, 0))
        self.demo_label = tk.Label(actions, text="", font=font(9), bg=CARD, fg=MUTED)
        self.demo_label.pack(side="left", padx=(14, 0))

        footer = tk.Frame(self, bg=BG)
        footer.pack(fill="x", padx=26, pady=(16, 24))
        Button(footer, "Save Settings", self.save, "primary", padx=20, pady=9).pack(side="right")

    def _field_row(self, parent, label, variable, width, hint=""):
        row = tk.Frame(parent, bg=CARD)
        row.pack(fill="x", pady=6)
        row.grid_columnconfigure(0, minsize=260)

        left = tk.Frame(row, bg=CARD)
        left.grid(row=0, column=0, sticky="w")
        tk.Label(left, text=label, font=font(11), bg=CARD, fg=TEXT, anchor="w").pack(fill="x")
        if hint:
            tk.Label(left, text=hint, font=font(8), bg=CARD, fg=MUTED, anchor="w",
                     wraplength=250, justify="left").pack(fill="x")

        make_entry(row, variable, width=width).grid(row=0, column=1, sticky="w", ipady=7)

    # ---------------- ACTIONS ----------------

    def refresh(self):
        settings = database.load_settings()
        self.app.settings = settings
        self.school_var.set(settings["school_name"])
        self.year_var.set(settings["academic_year"])
        self.late_var.set(settings["late_threshold"])
        self.min_var.set(settings["min_percentage"])
        self.saturday_var.set(settings.get("track_saturdays") == "yes")

        owner = self.app.user["id"]
        count = sample_data.count_demo_students(owner)
        if count:
            records = sample_data.count_demo_records(owner)
            self.demo_label.configure(text=f"{count} demo students loaded with {records} attendance records.")
        else:
            self.demo_label.configure(text="No demonstration data is currently loaded.")

    def save(self):
        late = self.late_var.get().strip()
        minimum = self.min_var.get().strip()

        if not self.school_var.get().strip():
            messagebox.showwarning("Missing Information", "School name cannot be empty.")
            return
        if not self.year_var.get().strip():
            messagebox.showwarning("Missing Information", "Academic year cannot be empty.")
            return
        if not late.isdigit() or int(late) > 240:
            messagebox.showwarning("Invalid Value", "Late threshold must be a whole number of minutes up to 240.")
            return
        try:
            value = float(minimum)
        except ValueError:
            messagebox.showwarning("Invalid Value", "Minimum attendance percentage must be a number.")
            return
        if value < 0 or value > 100:
            messagebox.showwarning("Invalid Value", "Minimum attendance percentage must be between 0 and 100.")
            return

        database.save_settings({
            "school_name": self.school_var.get().strip(),
            "academic_year": self.year_var.get().strip(),
            "late_threshold": late,
            "min_percentage": minimum,
            "track_saturdays": "yes" if self.saturday_var.get() else "no",
        })
        self.app.reload_settings()
        self.app.apply_settings()
        messagebox.showinfo("Settings Saved", "Your settings have been saved and will be used the next time the application starts.")

    def load_demo(self):
        owner = self.app.user["id"]
        if sample_data.count_demo_students(owner):
            messagebox.showinfo("Demo Data Already Loaded", "Demonstration records already exist for your account. Remove them first if you want a fresh set.")
            return
        students, records = sample_data.create_demo_data(owner)
        messagebox.showinfo("Demo Data Loaded", f"{students} demonstration students and {records} attendance records were created under 'Demo Class'.")
        self.refresh()

    def remove_demo(self):
        answer = messagebox.askyesno(
            "Remove Demo Data",
            "Delete every student and attendance record in 'Demo Class'? Your own records are not affected.",
        )
        if not answer:
            return
        removed = sample_data.delete_demo_data(self.app.user["id"])
        messagebox.showinfo("Demo Data Removed", f"{removed} demonstration student record(s) and their attendance were deleted.")
        self.refresh()
