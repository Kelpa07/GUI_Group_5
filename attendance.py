import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import messagebox, ttk

import database
from theme import (
    BG, BORDER, CARD, MUTED, STATUS_COLORS, TEAL, TEXT, WHITE,
    Button, Card, TitleBlock, font,
)

DATE_FORMAT = "%d-%m-%Y"
STATUSES = list(database.STATUSES)


class ScrollList(tk.Frame):
    """A vertically scrolling list of rows, used for the attendance table."""

    def __init__(self, parent, height=380):
        super().__init__(parent, bg=CARD)
        self.canvas = tk.Canvas(self, bg=CARD, highlightthickness=0, bd=0, height=height)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner = tk.Frame(self.canvas, bg=CARD)
        self.window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", self._on_inner)
        self.canvas.bind("<Configure>", self._on_canvas)

    def _on_inner(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas(self, event):
        self.canvas.itemconfigure(self.window, width=event.width)

    def clear(self):
        for child in self.inner.winfo_children():
            child.destroy()

    def scroll_to_top(self):
        self.canvas.yview_moveto(0)


class AttendanceFrame(tk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.selected_date = date.today()
        self.statuses = {}
        self.row_buttons = {}
        self._build()

    # ---------------- LAYOUT ----------------

    def _build(self):
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=26, pady=(22, 12))
        TitleBlock(header, "Mark Attendance", "Record daily student presence status").pack(side="left")

        controls = Card(self, padx=18, pady=14)
        controls.pack(fill="x", padx=26)

        tk.Label(controls, text="Class:", font=font(10), bg=CARD, fg=MUTED).pack(side="left")
        self.class_var = tk.StringVar()
        self.class_box = ttk.Combobox(controls, textvariable=self.class_var, width=14, state="readonly")
        self.class_box.pack(side="left", padx=(6, 18))

        tk.Label(controls, text="Section:", font=font(10), bg=CARD, fg=MUTED).pack(side="left")
        self.section_var = tk.StringVar()
        self.section_box = ttk.Combobox(controls, textvariable=self.section_var, width=14, state="readonly")
        self.section_box.pack(side="left", padx=(6, 18))

        tk.Label(controls, text="Date:", font=font(10), bg=CARD, fg=MUTED).pack(side="left")
        self.date_var = tk.StringVar(value=self.selected_date.strftime(DATE_FORMAT))
        date_entry = tk.Entry(
            controls, textvariable=self.date_var, font=font(10), width=12,
            relief="flat", bg=CARD, fg=TEXT, justify="center",
            highlightthickness=1, highlightbackground=BORDER, highlightcolor=TEAL,
        )
        date_entry.pack(side="left", ipady=6)
        date_entry.bind("<Return>", lambda e: self.apply_date())

        for text, command in (("◀", lambda: self.step_day(-1)), ("▶", lambda: self.step_day(1)), ("Today", self.use_today)):
            Button(controls, text, command, "ghost", padx=10, pady=4).pack(side="left", padx=(6, 0) if text != "◀" else (6, 0))

        self.late_note = tk.Label(controls, text="", font=font(9), bg=CARD, fg=MUTED)
        self.late_note.pack(side="right")

        # Table header
        table_card = Card(self, padx=0, pady=0)
        table_card.pack(fill="both", expand=True, padx=26, pady=(14, 10))

        head = tk.Frame(table_card, bg="#F8FAFC", padx=18, pady=12)
        head.pack(fill="x")
        head.columnconfigure(0, weight=1)
        head.columnconfigure(1, weight=2)

        tk.Label(head, text="Student ID", font=font(10, True), bg="#F8FAFC", fg=MUTED).grid(row=0, column=0, sticky="w")
        tk.Label(head, text="Student Name", font=font(10, True), bg="#F8FAFC", fg=MUTED).grid(row=0, column=1, sticky="w")
        tk.Label(head, text="Attendance Status", font=font(10, True), bg="#F8FAFC", fg=MUTED).grid(row=0, column=2, sticky="e")
        tk.Frame(table_card, bg=BORDER, height=1).pack(fill="x")

        self.list_area = ScrollList(table_card, height=380)
        self.list_area.pack(fill="both", expand=True)

        footer = tk.Frame(self, bg=BG)
        footer.pack(fill="x", padx=26, pady=(0, 22))

        self.summary_label = tk.Label(footer, text="", font=font(10), bg=BG, fg=MUTED)
        self.summary_label.pack(side="left")

        Button(footer, "✓  Save Attendance", self.save, "primary").pack(side="right")

    # ---------------- DATA LOADING ----------------

    def refresh(self):
        owner = self.app.user["id"]

        classes = database.fetch_classes(owner)
        self.class_box["values"] = classes
        if self.class_var.get() not in classes:
            self.class_var.set(classes[0] if classes else "")

        self._load_sections()
        self.late_note.configure(
            text="Late after " + self.app.settings.get("late_threshold", "15") + " minutes"
        )
        self._load_students()

    def _load_sections(self):
        owner = self.app.user["id"]
        sections = database.fetch_sections(owner, self.class_var.get())
        self.section_box["values"] = sections
        if self.section_var.get() not in sections:
            self.section_var.set(sections[0] if sections else "")

    def _load_students(self):
        owner = self.app.user["id"]
        students = database.fetch_students(
            owner, class_name=self.class_var.get(), section=self.section_var.get()
        )
        saved = database.fetch_attendance_for_date(owner, self.selected_date.isoformat())

        self.statuses = {row["id"]: saved.get(row["id"], "Present") for row in students}
        self._render_rows(students)

    def _render_rows(self, students):
        area = self.list_area
        area.clear()
        self.row_buttons = {}

        if not students:
            tk.Label(
                area.inner,
                text="No students registered for this class and section.\nAdd students first on the Students screen.",
                font=font(11), bg=CARD, fg=MUTED, justify="left",
            ).pack(pady=50)
            self._update_summary()
            return

        for index, student in enumerate(students):
            row = tk.Frame(area.inner, bg=CARD, padx=18, pady=10)
            row.pack(fill="x")
            row.columnconfigure(0, weight=1)
            row.columnconfigure(1, weight=2)

            tk.Label(row, text=student["student_id"], font=font(10), bg=CARD, fg=TEXT).grid(row=0, column=0, sticky="w")
            tk.Label(row, text=student["name"], font=font(10, True), bg=CARD, fg=TEXT).grid(row=0, column=1, sticky="w")

            group = tk.Frame(row, bg="#F1F5F9", padx=2, pady=2)
            group.grid(row=0, column=2, sticky="e")

            buttons = {}
            for status in STATUSES:
                label = tk.Label(
                    group,
                    text=status,
                    font=font(9, True),
                    bg="#F1F5F9",
                    fg=MUTED,
                    padx=14,
                    pady=6,
                    cursor="hand2",
                )
                label.pack(side="left")
                label.bind("<Button-1>", lambda e, sid=student["id"], s=status: self._choose(sid, s))
                buttons[status] = label

            self.row_buttons[student["id"]] = buttons
            self._paint_row(student["id"])

            tk.Frame(area.inner, bg=BORDER, height=1).pack(fill="x", padx=18)

        self._update_summary()
        area.scroll_to_top()

    # ---------------- STATUS BUTTONS ----------------

    def _choose(self, student_row, status):
        self.statuses[student_row] = status
        self._paint_row(student_row)
        self._update_summary()

    def _paint_row(self, student_row):
        buttons = self.row_buttons.get(student_row)
        if not buttons:
            return
        chosen = self.statuses.get(student_row)
        for status, label in buttons.items():
            active_color, inactive_color = STATUS_COLORS[status]
            if status == chosen:
                label.configure(bg=active_color, fg=WHITE)
            else:
                label.configure(bg="#F1F5F9", fg=MUTED)

    def _update_summary(self):
        counts = {status: 0 for status in STATUSES}
        for status in self.statuses.values():
            counts[status] += 1
        self.summary_label.configure(
            text=(
                f"{len(self.statuses)} students · Present {counts['Present']} · "
                f"Absent {counts['Absent']} · Late {counts['Late']} · Excused {counts['Excused']}"
            )
        )

    # ---------------- DATE CONTROLS ----------------

    def step_day(self, amount):
        self._set_date(self.selected_date + timedelta(days=amount))

    def use_today(self):
        self._set_date(date.today())

    def _set_date(self, new_date):
        self.selected_date = new_date
        self.date_var.set(new_date.strftime(DATE_FORMAT))
        self._load_students()

    def apply_date(self):
        """Read the typed date box and reload the list when it is valid."""
        try:
            parsed = datetime.strptime(self.date_var.get().strip(), DATE_FORMAT).date()
        except ValueError:
            messagebox.showwarning("Invalid Date", "Please type the date as dd-mm-yyyy, for example 09-09-2026.")
            self.date_var.set(self.selected_date.strftime(DATE_FORMAT))
            return
        self._set_date(parsed)

    # ---------------- SAVE ----------------

    def save(self):
        owner = self.app.user["id"]

        if not self.class_var.get() or not self.section_var.get():
            messagebox.showwarning("Missing Selection", "Please choose a class and a section first.")
            return

        try:
            parsed = datetime.strptime(self.date_var.get().strip(), DATE_FORMAT).date()
        except ValueError:
            messagebox.showwarning("Invalid Date", "Please type the date as dd-mm-yyyy, for example 09-09-2026.")
            return

        if parsed > date.today():
            messagebox.showwarning("Future Date", "Attendance cannot be recorded for a date in the future.")
            return

        self.selected_date = parsed
        self.date_var.set(parsed.strftime(DATE_FORMAT))

        if parsed.weekday() == 5 and self.app.settings.get("track_saturdays") != "yes":
            messagebox.showwarning(
                "Saturdays Are Not Tracked",
                "Saturday attendance is turned off.\nOpen Settings and switch on 'Track Saturdays' to record this date.",
            )
            return

        students = database.fetch_students(owner, class_name=self.class_var.get(), section=self.section_var.get())
        if not students:
            messagebox.showwarning("No Students", "There are no students in this class and section to mark.")
            return

        entries = []
        for student in students:
            status = self.statuses.get(student["id"])
            if status in STATUSES:
                entries.append((student["id"], parsed.isoformat(), status))

        if not entries:
            messagebox.showwarning("Nothing to Save", "Please choose a status for at least one student.")
            return

        already_saved = database.fetch_attendance_for_date(owner, parsed.isoformat())
        updated = len([e for e in entries if e[0] in already_saved])

        if already_saved:
            answer = messagebox.askyesno(
                "Update Existing Records",
                f"{len(already_saved)} student(s) already have attendance on {parsed.strftime(DATE_FORMAT)}.\n"
                "Save again to update those records?",
            )
            if not answer:
                return

        try:
            database.save_attendance(owner, entries)
        except Exception as error:
            messagebox.showerror("Save Failed", "Attendance could not be saved:\n" + str(error))
            return

        label = self.class_var.get() + " — " + self.section_var.get()
        if updated:
            messagebox.showinfo("Attendance Saved", f"Attendance for {label} was saved.\n{updated} existing record(s) were updated.")
        else:
            messagebox.showinfo("Attendance Saved", f"Attendance for {label} on {parsed.strftime(DATE_FORMAT)} has been recorded successfully.")

        self._load_students()
