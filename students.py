import tkinter as tk
from tkinter import messagebox, ttk

import analytics
import database
from theme import (
    BG, CARD, MUTED, RED, TEXT,
    Button, Card, Field, TitleBlock, add_placeholder, font,
)

PAGE_SIZE = 10

COLUMNS = ("Student ID", "Name", "Class", "Section", "Attendance Rate", "Category")
WIDTHS = (110, 200, 110, 90, 130, 150)


class StudentsFrame(tk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.rows = []
        self.page = 1
        self._build()

    # ---------------- LAYOUT ----------------

    def _build(self):
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=26, pady=(22, 12))

        TitleBlock(header, "Students",
                   "Manage and review student records and rates · red rows are below the minimum set in Settings"
                   ).pack(side="left")

        Button(header, "+  Add Student", self.add_student, "primary").pack(side="right")

        search_card = Card(header, padx=10, pady=6)
        search_card.pack(side="right", padx=(0, 14))

        self.search_var = tk.StringVar()
        entry = tk.Entry(
            search_card, textvariable=self.search_var, font=font(10), relief="flat",
            bg=CARD, fg=TEXT, width=22, highlightthickness=0, insertbackground=TEXT,
        )
        entry.pack(side="left", padx=(4, 0), ipady=6)
        entry.bind("<KeyRelease>", lambda e: self._reset_and_refresh())
        self.search_placeholder = add_placeholder(entry, self.search_var, "Search students...")
        tk.Label(search_card, text="🔍", font=font(11), bg=CARD, fg=MUTED).pack(side="left", padx=(8, 4))

        table_card = Card(self, padx=0, pady=0)
        table_card.pack(fill="both", expand=True, padx=26)

        holder = tk.Frame(table_card, bg=CARD)
        holder.pack(fill="both", expand=True, padx=1, pady=1)

        # One page of rows fits without scrolling, so the footer stays visible.
        self.table = ttk.Treeview(holder, columns=COLUMNS, show="headings", height=PAGE_SIZE)
        scrollbar = ttk.Scrollbar(holder, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)

        for name, width in zip(COLUMNS, WIDTHS):
            self.table.heading(name, text=name)
            self.table.column(name, width=width, anchor="w" if name in ("Name", "Class", "Section") else "center")

        # Rows under the minimum set in Settings get a soft red background.
        self.table.tag_configure("below_min", background="#FEF2F2", foreground=RED)

        self.table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.table.bind("<Double-1>", lambda e: self.edit_student())

        footer = tk.Frame(self, bg=BG)
        footer.pack(fill="x", padx=26, pady=(10, 22))

        self.count_label = tk.Label(footer, text="", font=font(10), bg=BG, fg=MUTED)
        self.count_label.pack(side="left")

        nav = tk.Frame(footer, bg=BG)
        nav.pack(side="right")

        Button(nav, "Previous", self.previous_page, "ghost", padx=12, pady=5).pack(side="left", padx=(0, 6))
        self.page_label = tk.Label(nav, text="", font=font(10), bg=BG, fg=TEXT)
        self.page_label.pack(side="left", padx=6)
        Button(nav, "Next", self.next_page, "ghost", padx=12, pady=5).pack(side="left", padx=(6, 0))

        actions = tk.Frame(footer, bg=BG)
        actions.pack(side="left", padx=(24, 0))
        Button(actions, "Edit", self.edit_student, "ghost", padx=14, pady=5).pack(side="left", padx=(0, 6))
        Button(actions, "Delete", self.delete_student, "ghost", padx=14, pady=5).pack(side="left")

    # ---------------- DATA ----------------

    def refresh(self):
        owner = self.app.user["id"]
        df = analytics.load_dataframe(owner)
        summary = analytics.student_summary(owner, df)

        if self.search_placeholder["shown"]:
            search = ""
        else:
            search = self.search_var.get().strip().lower()
        if search:
            keep = summary["student_id"].str.lower().str.contains(search, na=False) | \
                   summary["name"].str.lower().str.contains(search, na=False)
            summary = summary[keep]

        self.rows = summary.to_dict("records")
        total_pages = max(1, (len(self.rows) + PAGE_SIZE - 1) // PAGE_SIZE)
        if self.page > total_pages:
            self.page = total_pages

        self._render_page()

    def _reset_and_refresh(self):
        self.page = 1
        self.refresh()

    def _render_page(self):
        self.table.delete(*self.table.get_children())

        start = (self.page - 1) * PAGE_SIZE
        page_rows = self.rows[start:start + PAGE_SIZE]
        minimum = self.app.min_percentage()

        for row in page_rows:
            rate = row["Attendance Rate"]
            category = row["Category"]
            tags = []

            if rate is not None and not _is_missing(rate) and rate < minimum:
                tags.append("below_min")

            self.table.insert(
                "",
                "end",
                iid=str(row["student_row"]),
                values=(
                    row["student_id"],
                    row["name"],
                    row["class_name"],
                    row["section"],
                    "-" if _is_missing(rate) else f"{rate:.1f}%",
                    category,
                ),
                tags=tuple(tags),
            )

        total = len(self.rows)
        if total == 0:
            self.count_label.configure(text="No student records found")
        else:
            last = min(start + PAGE_SIZE, total)
            self.count_label.configure(text=f"Showing {start + 1}-{last} of {total} students")

        total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        self.page_label.configure(text=f"Page {self.page} of {total_pages}")

    # ---------------- PAGINATION ----------------

    def previous_page(self):
        if self.page > 1:
            self.page -= 1
            self._render_page()

    def next_page(self):
        total_pages = max(1, (len(self.rows) + PAGE_SIZE - 1) // PAGE_SIZE)
        if self.page < total_pages:
            self.page += 1
            self._render_page()

    # ---------------- ADD / EDIT / DELETE ----------------

    def _selected_row(self):
        chosen = self.table.selection()
        if not chosen:
            messagebox.showwarning("No Selection", "Please select a student in the table first.")
            return None
        return int(chosen[0])

    def add_student(self):
        StudentDialog(self, self.app, None, on_saved=self._reset_and_refresh)

    def edit_student(self):
        row_id = self._selected_row()
        if row_id is None:
            return
        student = database.fetch_student_row(self.app.user["id"], row_id)
        if student is None:
            messagebox.showerror("Not Found", "That student record could not be loaded.")
            return
        StudentDialog(self, self.app, student, on_saved=self._reset_and_refresh)

    def delete_student(self):
        row_id = self._selected_row()
        if row_id is None:
            return

        student = database.fetch_student_row(self.app.user["id"], row_id)
        if student is None:
            return

        answer = messagebox.askyesno(
            "Delete Student",
            "Delete " + student["name"] + " (" + student["student_id"] + ")?\n\n"
            "Their attendance records will also be removed. This cannot be undone.",
        )
        if not answer:
            return

        database.delete_student(row_id, self.app.user["id"])
        messagebox.showinfo("Deleted", "The student record was removed.")
        self._reset_and_refresh()


def _is_missing(value):
    """True when a rate is blank because the student has no eligible days."""
    if value is None:
        return True
    try:
        return bool(value != value)  # NaN check
    except Exception:
        return False


class StudentDialog(tk.Toplevel):
    """Modal form used for both adding and editing a student."""

    def __init__(self, parent, app, student, on_saved):
        super().__init__(parent)
        self.app = app
        self.student = student
        self.on_saved = on_saved

        editing = student is not None
        self.title("Edit Student" if editing else "Add Student")
        self.configure(bg=CARD, padx=26, pady=22)
        self.resizable(False, False)
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 260, parent.winfo_rooty() + 120))
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        tk.Label(self, text="Edit Student" if editing else "Add a New Student",
                 font=font(16, True), bg=CARD, fg=TEXT).pack(anchor="w")
        tk.Label(self, text="Student ID, name, class and section are required.",
                 font=font(10), bg=CARD, fg=MUTED).pack(anchor="w", pady=(2, 14))

        self.id_field = Field(self, "Student ID", tk.StringVar(value="" if not editing else student["student_id"]))
        self.id_field.pack(fill="x", pady=(0, 4))

        self.name_field = Field(self, "Student Name", tk.StringVar(value="" if not editing else student["name"]))
        self.name_field.pack(fill="x", pady=(0, 4))

        classes = database.fetch_classes(self.app.user["id"]) or ["B.ed ICT"]
        sections = database.fetch_sections(self.app.user["id"]) or ["Section A"]

        self.class_var = tk.StringVar(value="" if not editing else student["class_name"])
        self.section_var = tk.StringVar(value="" if not editing else student["section"])

        self._combo_row("Class", self.class_var, classes)
        self._combo_row("Section", self.section_var, sections)

        buttons = tk.Frame(self, bg=CARD)
        buttons.pack(fill="x", pady=(18, 0))
        Button(buttons, "Cancel", self.destroy, "ghost").pack(side="right", padx=(8, 0))
        Button(buttons, "Save Student", self.save, "primary").pack(side="right")

    def _combo_row(self, label, variable, values):
        row = tk.Frame(self, bg=CARD)
        row.pack(fill="x", pady=(6, 2))
        tk.Label(row, text=label, font=font(10, True), bg=CARD, fg=TEXT, width=14, anchor="w").pack(side="left")
        box = ttk.Combobox(row, textvariable=variable, values=values, width=28)
        box.pack(side="left", padx=(6, 0), ipady=5)

    def save(self):
        for field in (self.id_field, self.name_field):
            field.clear_error()

        student_id = self.id_field.get()
        name = self.name_field.get()
        class_name = self.class_var.get().strip()
        section = self.section_var.get().strip()
        owner = self.app.user["id"]

        valid = True
        if not student_id:
            self.id_field.set_error("Student ID is required.")
            valid = False
        if not name:
            self.name_field.set_error("Student name is required.")
            valid = False
        elif any(c.isdigit() for c in name):
            self.name_field.set_error("Student name cannot contain numbers.")
            valid = False
        if not class_name:
            messagebox.showwarning("Missing Information", "Please choose or type a class.")
            valid = False
        if not section:
            messagebox.showwarning("Missing Information", "Please choose or type a section.")
            valid = False
        if not valid:
            return

        if self.student is None:
            if database.student_id_exists(owner, student_id):
                self.id_field.set_error("This Student ID already exists.")
                return
            database.add_student(owner, student_id, name, class_name, section)
        else:
            if database.student_id_exists(owner, student_id, exclude_row=self.student["id"]):
                self.id_field.set_error("Another student already uses this Student ID.")
                return
            database.update_student(self.student["id"], owner, student_id, name, class_name, section)

        self.destroy()
        self.on_saved()
