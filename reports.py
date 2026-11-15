import csv
import tkinter as tk
from datetime import date, datetime
from tkinter import filedialog, messagebox, ttk

import analytics
import database
from theme import (
    AMBER, BG, BORDER, CARD, GREEN, MUTED, RED, TEAL, TEXT,
    Button, Card, TitleBlock, font,
)
import charts

DATE_FORMAT = "%d-%m-%Y"


class ReportsFrame(tk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.canvases = []
        self.frame = None       # filtered attendance records
        self.summary = None     # one row per student
        self._build()

    # ---------------- LAYOUT ----------------

    def _build(self):
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=26, pady=(22, 12))
        TitleBlock(header, "Reports", "Deep analytics and attendance summaries").pack(side="left")

        filters = Card(self, padx=16, pady=12)
        filters.pack(fill="x", padx=26)

        tk.Label(filters, text="From:", font=font(10), bg=CARD, fg=MUTED).pack(side="left")
        self.start_var = tk.StringVar()
        self._entry(filters, self.start_var).pack(side="left", padx=(4, 12))

        tk.Label(filters, text="To:", font=font(10), bg=CARD, fg=MUTED).pack(side="left")
        self.end_var = tk.StringVar()
        self._entry(filters, self.end_var).pack(side="left", padx=(4, 12))

        tk.Label(filters, text="Class:", font=font(10), bg=CARD, fg=MUTED).pack(side="left")
        self.class_var = tk.StringVar(value="All Classes")
        self.class_box = ttk.Combobox(filters, textvariable=self.class_var, width=12, state="readonly")
        self.class_box.pack(side="left", padx=(4, 12))

        tk.Label(filters, text="Section:", font=font(10), bg=CARD, fg=MUTED).pack(side="left")
        self.section_var = tk.StringVar(value="All Sections")
        self.section_box = ttk.Combobox(filters, textvariable=self.section_var, width=12, state="readonly")
        self.section_box.pack(side="left", padx=(4, 12))

        Button(filters, "Generate Report", self.generate, "primary", padx=14, pady=6).pack(side="left")
        Button(filters, "Reset", self.reset_filters, "ghost", padx=12, pady=6).pack(side="left", padx=(8, 0))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=26, pady=(14, 0))
        self.body = body

        export_row = tk.Frame(self, bg=BG)
        export_row.pack(fill="x", padx=26, pady=(0, 22))
        tk.Label(export_row, text="Reports cover only the dates, class and section shown above.",
                 font=font(9), bg=BG, fg=MUTED).pack(side="left")
        Button(export_row, "Export Student Rates (CSV)", lambda: self.export("students"), "ghost", padx=14, pady=7).pack(side="right", padx=(8, 0))
        Button(export_row, "Export Attendance Records (CSV)", lambda: self.export("records"), "primary", padx=14, pady=7).pack(side="right")

    def _entry(self, parent, variable):
        return tk.Entry(
            parent, textvariable=variable, font=font(10), width=11, relief="flat",
            bg=CARD, fg=TEXT, justify="center", highlightthickness=1,
            highlightbackground=BORDER, highlightcolor=TEAL,
        )

    # ---------------- FILTERS ----------------

    def refresh(self):
        owner = self.app.user["id"]
        classes = ["All Classes"] + database.fetch_classes(owner)
        self.class_box["values"] = classes
        if self.class_var.get() not in classes:
            self.class_var.set("All Classes")
        self._load_sections()

        if not self.start_var.get():
            dates = database.fetch_all_dates(owner)
            if dates:
                self.start_var.set(_display(dates[0]))
                self.end_var.set(date.today().strftime(DATE_FORMAT))
            else:
                self.start_var.set(date.today().strftime(DATE_FORMAT))
                self.end_var.set(date.today().strftime(DATE_FORMAT))

        self.generate()

    def _load_sections(self):
        owner = self.app.user["id"]
        value = "" if self.class_var.get() == "All Classes" else self.class_var.get()
        sections = ["All Sections"] + database.fetch_sections(owner, value)
        self.section_box["values"] = sections
        if self.section_var.get() not in sections:
            self.section_var.set("All Sections")

    def reset_filters(self):
        self.class_var.set("All Classes")
        self.section_var.set("All Sections")
        dates = database.fetch_all_dates(self.app.user["id"])
        if dates:
            self.start_var.set(_display(dates[0]))
        self.end_var.set(date.today().strftime(DATE_FORMAT))
        self.generate()

    def _read_filters(self):
        """Return (start, end, class, section) or None when the dates are wrong."""
        try:
            start = datetime.strptime(self.start_var.get().strip(), DATE_FORMAT).date()
            end = datetime.strptime(self.end_var.get().strip(), DATE_FORMAT).date()
        except ValueError:
            messagebox.showwarning("Invalid Date", "Please type both dates as dd-mm-yyyy, for example 09-09-2026.")
            return None
        if start > end:
            messagebox.showwarning("Invalid Range", "The 'From' date must be on or before the 'To' date.")
            return None

        class_name = "" if self.class_var.get() == "All Classes" else self.class_var.get()
        section = "" if self.section_var.get() == "All Sections" else self.section_var.get()
        return start.isoformat(), end.isoformat(), class_name, section

    # ---------------- GENERATE ----------------

    def generate(self):
        params = self._read_filters()
        if params is None:
            return
        start, end, class_name, section = params
        owner = self.app.user["id"]

        self.frame = analytics.load_dataframe(owner, class_name, section, start, end)
        self.summary = analytics.student_summary(owner, self.frame)

        for canvas in self.canvases:
            charts.clear_canvas(canvas)
        self.canvases = []
        for child in self.body.winfo_children():
            child.destroy()

        self._draw_charts(class_name, section)
        self._draw_summary_cards(start, end)
        self._draw_table()

    def _draw_charts(self, class_name, section):
        self.body.grid_columnconfigure(0, weight=1, uniform="r")
        self.body.grid_columnconfigure(1, weight=1, uniform="r")

        # --- Section comparison ---
        left = Card(self.body)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        self._header(left, "Attendance across Sections")

        sections = analytics.group_rates(self.frame, "section")
        if sections.empty:
            self._empty(left, "No attendance in this selection yet.")
        else:
            labels = [s if str(s).startswith("Section") else "Sec " + str(s) for s in sections["section"]]
            canvas = charts.draw_bars(left, None, labels, list(sections["rate"]),
                                      colors=[charts.rate_color(r) for r in sections["rate"]])
            canvas.get_tk_widget().pack(fill="x", pady=(4, 8))
            self.canvases.append(canvas)

        # --- Monthly trend ---
        right = Card(self.body)
        right.grid(row=0, column=1, sticky="nsew")
        self._header(right, "Monthly Attendance Trend")

        months = analytics.monthly_trend(self.frame)
        if months.empty:
            self._empty(right, "No monthly data in this selection yet.")
        else:
            canvas = charts.draw_line(right, None, list(months["month"]), list(months["rate"]))
            canvas.get_tk_widget().pack(fill="x", pady=(4, 8))
            self.canvases.append(canvas)

        # --- Category share ---
        row1 = tk.Frame(self.body, bg=BG)
        row1.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(14, 0))
        row1.grid_columnconfigure(0, weight=1, uniform="r1")
        row1.grid_columnconfigure(1, weight=1, uniform="r1")

        pie_card = Card(row1)
        pie_card.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        self._header(pie_card, "Students by Category")
        counts = analytics.category_counts(self.summary)
        if counts["No Data"] == len(self.summary):
            self._empty(pie_card, "No student has an eligible attendance record yet.")
        else:
            canvas = charts.draw_pie(
                pie_card, None,
                [analytics.EXCELLENT, analytics.GOOD, analytics.NEEDS],
                [counts[analytics.EXCELLENT], counts[analytics.GOOD], counts[analytics.NEEDS]],
                [GREEN, AMBER, RED],
            )
            canvas.get_tk_widget().pack(fill="x", pady=(0, 8))
            self.canvases.append(canvas)

        hist_card = Card(row1)
        hist_card.grid(row=0, column=1, sticky="nsew")
        self._header(hist_card, "Distribution of Attendance Rates")
        rated = analytics.rated_students(self.summary)
        if rated.empty:
            self._empty(hist_card, "Nothing to plot yet.")
        else:
            canvas = charts.draw_histogram(hist_card, None, list(rated["Attendance Rate"].astype(float)))
            canvas.get_tk_widget().pack(fill="x", pady=(0, 8))
            self.canvases.append(canvas)

        # --- Descriptive statistics ---
        stats_card = Card(self.body)
        stats_card.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(14, 0))
        self._header(stats_card, "Descriptive Statistics of Student Attendance Rates")
        stats = analytics.descriptive_stats(self.summary)
        grid = tk.Frame(stats_card, bg=CARD)
        grid.pack(fill="x", pady=(2, 4))
        items = list(stats.items())
        for index, (key, value) in enumerate(items):
            cell = tk.Frame(grid, bg=CARD)
            cell.grid(row=index // 4, column=index % 4, sticky="w", padx=(0, 34), pady=6)
            tk.Label(cell, text=str(value), font=font(14, True), bg=CARD, fg=TEXT).pack(anchor="w")
            tk.Label(cell, text=key, font=font(9), bg=CARD, fg=MUTED).pack(anchor="w")

    def _header(self, card, title):
        tk.Label(card, text=title, font=font(11, True), bg=CARD, fg=TEXT, anchor="w",
                 justify="left", wraplength=420).pack(fill="x", pady=(0, 6))

    def _empty(self, card, message):
        box = tk.Frame(card, bg=CARD, height=150)
        box.pack(fill="x")
        box.pack_propagate(False)
        tk.Label(box, text=message, font=font(10), bg=CARD, fg=MUTED, wraplength=380,
                 justify="center").pack(expand=True)

    def _draw_summary_cards(self, start, end):
        row = tk.Frame(self.body, bg=BG)
        row.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(14, 0))
        for index in range(4):
            row.grid_columnconfigure(index, weight=1, uniform="sum")

        counts = analytics.status_totals(self.frame)
        overall = analytics.overall_rate(self.frame)
        day, absent_rate = analytics.most_absent_day(self.frame)
        minimum = self.app.min_percentage()
        below = analytics.students_below(self.summary, minimum)

        cards = [
            ("Total Registered Students", str(len(self.summary)),
             (self.class_var.get() if self.class_var.get() != "All Classes" else "All classes")
             + " · " + (self.section_var.get() if self.section_var.get() != "All Sections" else "All sections")),
            ("Overall Attendance Rate", f"{overall:.1f}%",
             f"{counts['Present']} present of {counts['Present'] + counts['Absent'] + counts['Late']} eligible records"),
            ("Most Absent Day", day,
             f"Average {absent_rate:.1f}% absent on that day" if day != "No data" else "No absence data"),
            ("Below Minimum Attendance", f"{len(below)} student(s)",
             f"Under the {minimum:.0f}% threshold set in Settings"),
        ]

        for index, (title, value, subtitle) in enumerate(cards):
            card = Card(row)
            card.grid(row=0, column=index, sticky="nsew", padx=(0, 14) if index < 3 else 0)
            tk.Label(card, text=title, font=font(9), bg=CARD, fg=MUTED, anchor="w").pack(fill="x")
            tk.Label(card, text=value, font=font(18, True), bg=CARD, fg=TEXT, anchor="w").pack(fill="x")
            tk.Label(card, text=subtitle, font=font(8), bg=CARD, fg=MUTED, anchor="w", wraplength=190,
                     justify="left").pack(fill="x")

    def _draw_table(self):
        card = Card(self.body)
        card.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=(14, 0))
        self.body.grid_rowconfigure(4, weight=1)

        self._header(card, "Individual Student Attendance")

        columns = ("Student ID", "Name", "Class", "Section", "Present", "Absent", "Late", "Excused", "Rate", "Category")
        widths = (90, 160, 90, 80, 70, 70, 60, 70, 70, 130)

        holder = tk.Frame(card, bg=CARD)
        holder.pack(fill="both", expand=True)

        table = ttk.Treeview(holder, columns=columns, show="headings", height=8)
        scrollbar = ttk.Scrollbar(holder, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)

        for name, width in zip(columns, widths):
            table.heading(name, text=name)
            table.column(name, width=width, anchor="w" if name in ("Name", "Class", "Section") else "center")

        table.tag_configure("Excellent", foreground=GREEN)
        table.tag_configure("Good", foreground=AMBER)
        table.tag_configure("Needs Improvement", foreground=RED)
        table.tag_configure("No Data", foreground=MUTED)

        for _, student in self.summary.iterrows():
            rate = student["Attendance Rate"]
            missing = rate is None or rate != rate
            table.insert("", "end", values=(
                student["student_id"], student["name"], student["class_name"], student["section"],
                student["Present"], student["Absent"], student["Late"], student["Excused"],
                "-" if missing else f"{rate:.1f}%", student["Category"],
            ), tags=(student["Category"],))

        table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.table = table

    # ---------------- CSV EXPORT ----------------

    def export(self, kind):
        if kind == "records" and (self.frame is None or self.frame.empty):
            messagebox.showwarning("Nothing to Export", "There are no attendance records in the current selection.")
            return
        if kind == "students" and (self.summary is None or self.summary.empty):
            messagebox.showwarning("Nothing to Export", "There are no students to export yet.")
            return

        suggested = "student_attendance_rates.csv" if kind == "students" else "attendance_records.csv"
        path = filedialog.asksaveasfilename(
            title="Save CSV Report",
            defaultextension=".csv",
            initialfile=suggested,
            filetypes=[("CSV File", "*.csv"), ("All Files", "*.*")],
        )
        if not path:
            return

        try:
            if kind == "students":
                headers = ["Student ID", "Student Name", "Class", "Section", "Present", "Absent",
                           "Late", "Excused", "Eligible Days", "Attendance Rate (%)", "Category"]
                records = []
                for _, student in self.summary.iterrows():
                    rate = student["Attendance Rate"]
                    records.append({
                        "Student ID": student["student_id"],
                        "Student Name": student["name"],
                        "Class": student["class_name"],
                        "Section": student["section"],
                        "Present": int(student["Present"]),
                        "Absent": int(student["Absent"]),
                        "Late": int(student["Late"]),
                        "Excused": int(student["Excused"]),
                        "Eligible Days": int(student["Eligible Days"]),
                        "Attendance Rate (%)": "" if rate is None or rate != rate else round(float(rate), 1),
                        "Category": student["Category"],
                    })
            else:
                headers = ["Student ID", "Student Name", "Class", "Section", "Date", "Attendance Status"]
                records = []
                for _, record in self.frame.iterrows():
                    records.append({
                        "Student ID": record["student_id"],
                        "Student Name": record["name"],
                        "Class": record["class_name"],
                        "Section": record["section"],
                        "Date": record["date"].strftime("%Y-%m-%d"),
                        "Attendance Status": record["status"],
                    })

            with open(path, "w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.DictWriter(handle, fieldnames=headers)
                writer.writeheader()
                writer.writerows(records)
        except Exception as error:
            messagebox.showerror("Export Failed", "The CSV file could not be written:\n" + str(error))
            return

        messagebox.showinfo("Export Ready", f"{len(records)} row(s) were saved to\n{path}")


def _display(iso_text):
    try:
        return datetime.strptime(iso_text, "%Y-%m-%d").strftime(DATE_FORMAT)
    except ValueError:
        return iso_text
