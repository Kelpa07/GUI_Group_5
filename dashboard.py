"""
dashboard.py
The landing screen after login: summary cards, two Matplotlib charts and the
three attendance category lists.

Every number on this page is calculated from the SQLite records with Pandas by
analytics.py, so the page changes as soon as attendance is saved.
"""

import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import ttk

import pandas as pd

import analytics
import database
from theme import (
    AMBER, AMBER_SOFT, BG, CARD, GREEN, GREEN_SOFT, MUTED, RED, RED_SOFT,
    TEAL, TEAL_SOFT, TEXT, Card, TitleBlock, font,
)
import charts


class DashboardFrame(tk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.canvases = []
        self._build()

    # ---------------- LAYOUT ----------------

    def _build(self):
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=26, pady=(22, 10))

        self.title_block = TitleBlock(header, "Dashboard", "Academic Year")
        self.title_block.pack(side="left")
        self.subtitle_label = self.title_block.subtitle_label

        filters = Card(header, padx=12, pady=8)
        filters.pack(side="right")

        tk.Label(filters, text="Class:", font=font(10), bg=CARD, fg=MUTED).pack(side="left")
        self.class_var = tk.StringVar(value="All Classes")
        self.class_box = ttk.Combobox(filters, textvariable=self.class_var, width=12, state="readonly")
        self.class_box.pack(side="left", padx=(6, 14))

        tk.Label(filters, text="Section:", font=font(10), bg=CARD, fg=MUTED).pack(side="left")
        self.section_var = tk.StringVar(value="All Sections")
        self.section_box = ttk.Combobox(filters, textvariable=self.section_var, width=12, state="readonly")
        self.section_box.pack(side="left", padx=(6, 0))

        self.class_box.bind("<<ComboboxSelected>>", lambda e: self._on_filter_change())
        self.section_box.bind("<<ComboboxSelected>>", lambda e: self._on_filter_change())

        self.cards_row = tk.Frame(self, bg=BG)
        self.cards_row.pack(fill="x", padx=26)

        self.charts_row = tk.Frame(self, bg=BG)
        self.charts_row.pack(fill="x", padx=26, pady=(16, 0))

        tk.Label(self, text="Student Categories", font=font(13, True), bg=BG, fg=TEXT).pack(
            anchor="w", padx=30, pady=(18, 6)
        )
        self.categories_row = tk.Frame(self, bg=BG)
        self.categories_row.pack(fill="x", padx=26, pady=(0, 26))

    # ---------------- FILTERS ----------------

    def _selected_class(self):
        value = self.class_var.get()
        return "" if value == "All Classes" else value

    def _selected_section(self):
        value = self.section_var.get()
        return "" if value == "All Sections" else value

    def _on_filter_change(self):
        owner = self.app.user["id"]
        # Keep the section list relevant to the chosen class.
        sections = ["All Sections"] + database.fetch_sections(owner, self._selected_class())
        self.section_box["values"] = sections
        if self.section_var.get() not in sections:
            self.section_var.set("All Sections")
        self.refresh()

    def _load_filter_choices(self):
        owner = self.app.user["id"]
        classes = ["All Classes"] + database.fetch_classes(owner)
        if self.class_var.get() not in classes:
            self.class_var.set("All Classes")
        self.class_box["values"] = classes

        sections = ["All Sections"] + database.fetch_sections(owner, self._selected_class())
        if self.section_var.get() not in sections:
            self.section_var.set("All Sections")
        self.section_box["values"] = sections

    # ---------------- REFRESH ----------------

    def refresh(self):
        owner = self.app.user["id"]

        # Charts are redrawn from scratch, so release the previous figures first.
        for canvas in self.canvases:
            charts.clear_canvas(canvas)
        self.canvases = []

        self.subtitle_label.configure(text="Academic Year " + self.app.academic_year())

        self._load_filter_choices()

        df = analytics.load_dataframe(
            owner, self._selected_class(), self._selected_section()
        )
        summary = analytics.student_summary(owner, df)
        total_students = len(summary)
        overall = analytics.overall_rate(df)

        today = date.today().isoformat()
        counts = {status: database.count_attendance_on(owner, today, status)
                  for status in ("Present", "Absent", "Late")}
        counted_on = date.today()
        title_prefix = "Today"

        # When nothing is marked for today yet, show the most recent school day instead.
        if sum(counts.values()) == 0:
            dates = database.fetch_all_dates(owner)
            if dates:
                counted_on = datetime.strptime(dates[-1], "%Y-%m-%d").date()
                counts = {status: database.count_attendance_on(owner, dates[-1], status)
                          for status in ("Present", "Absent", "Late")}
                title_prefix = "Latest Day"

        self._draw_cards(df, total_students, overall, counts, counted_on, title_prefix)
        self._draw_charts(df)
        self._draw_categories(summary)

    # ---------------- CARDS ----------------

    def _clear(self, frame):
        for child in frame.winfo_children():
            child.destroy()

    def _draw_cards(self, df, total_students, overall, counts, counted_on, prefix):
        self._clear(self.cards_row)
        for index in range(5):
            self.cards_row.grid_columnconfigure(index, weight=1, uniform="cards")

        day_text = counted_on.strftime("%d %b %Y")
        self._stat_card(0, "Total Students", str(total_students), "students",
                        "Registered in " + (self._selected_class() or "all classes"))
        self._donut_card(1, "Overall Attendance", overall, df)
        self._stat_card(2, f"Present {prefix}", str(counts["Present"]), "present", day_text)
        self._stat_card(3, f"Absent {prefix}", str(counts["Absent"]), "absent", day_text)
        self._stat_card(4, f"Late {prefix}", str(counts["Late"]), "late", day_text)

    def _stat_card(self, column, title, value, kind, subtitle):
        card = Card(self.cards_row, padx=12, pady=12)
        card.grid(row=0, column=column, sticky="nsew", padx=(0, 12) if column < 4 else 0)

        tk.Label(card, text=title, font=font(9), bg=CARD, fg=MUTED, anchor="w").pack(fill="x")

        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x", pady=(2, 0))

        colors = {
            "students": (TEAL, TEAL_SOFT),
            "present": (GREEN, GREEN_SOFT),
            "absent": (RED, RED_SOFT),
            "late": (AMBER, AMBER_SOFT),
        }
        accent, soft = colors[kind]

        badge = tk.Canvas(row, width=30, height=30, bg=CARD, highlightthickness=0, bd=0)
        badge.pack(side="left", padx=(0, 10))
        badge.create_oval(1, 1, 29, 29, fill=soft, outline=soft)
        glyph = {"students": "☰", "present": "✓", "absent": "✗", "late": "⏱"}[kind]
        badge.create_text(15, 15, text=glyph, fill=accent, font=("Segoe UI", 12, "bold"))

        tk.Label(row, text=value, font=font(20, True), bg=CARD, fg=TEXT).pack(side="left")

        tk.Label(card, text=subtitle, font=font(8), bg=CARD, fg=MUTED, anchor="w").pack(fill="x", pady=(2, 0))

    def _donut_card(self, column, title, overall, df):
        card = Card(self.cards_row, padx=12, pady=12)
        card.grid(row=0, column=column, sticky="nsew", padx=6)

        tk.Label(card, text=title, font=font(9), bg=CARD, fg=MUTED, anchor="w").pack(fill="x")

        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x", pady=(2, 0))

        holder = tk.Frame(row, bg=CARD, width=34, height=34)
        holder.pack(side="left", padx=(0, 10))
        holder.pack_propagate(False)

        if not df.empty:
            canvas = charts.draw_donut(holder, None, overall, width=0.34, height=0.34)
            canvas.get_tk_widget().place(x=0, y=0)
            self.canvases.append(canvas)

        tk.Label(row, text=f"{overall:.1f}%", font=font(20, True), bg=CARD, fg=TEXT).pack(side="left")

        change = self._weekly_change(df)
        if change is None:
            note, color = "No comparison data yet", MUTED
        elif change >= 0:
            note, color = f"↑ {abs(change):.1f}% this week", GREEN
        else:
            note, color = f"↓ {abs(change):.1f}% this week", RED
        tk.Label(card, text=note, font=font(8), bg=CARD, fg=color, anchor="w").pack(fill="x", pady=(2, 0))

    def _weekly_change(self, df):
        """Rate for the last 7 days minus the rate for the 7 days before that."""
        if df.empty:
            return None
        today = date.today()
        current_start = (today - timedelta(days=6)).isoformat()
        previous_start = (today - timedelta(days=13)).isoformat()
        previous_end = (today - timedelta(days=7)).isoformat()

        current = df[df["date"] >= pd.Timestamp(current_start)]
        previous = df[(df["date"] >= pd.Timestamp(previous_start)) & (df["date"] <= pd.Timestamp(previous_end))]

        if current.empty or previous.empty:
            return None
        return round(analytics.overall_rate(current) - analytics.overall_rate(previous), 1)

    # ---------------- CHARTS ----------------

    def _draw_charts(self, df):
        self._clear(self.charts_row)
        self.charts_row.grid_columnconfigure(0, weight=1, uniform="charts")
        self.charts_row.grid_columnconfigure(1, weight=1, uniform="charts")

        trend_card = Card(self.charts_row)
        trend_card.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        day_card = Card(self.charts_row)
        day_card.grid(row=0, column=1, sticky="nsew")

        self._card_header(trend_card, "Attendance Trend (Last 10 Days)", "Daily Rate")
        self._card_header(day_card, "Attendance by Day of Week", "")

        trend = analytics.daily_trend(df, limit=10)
        if trend.empty:
            self._no_data(trend_card, "Mark attendance to see the trend line.")
        else:
            canvas = charts.draw_line(trend_card, None, list(trend["label"]), list(trend["rate"]))
            canvas.get_tk_widget().pack(fill="x", pady=(4, 6))
            self.canvases.append(canvas)

        weekdays = analytics.weekday_rates(df)
        if weekdays.empty:
            self._no_data(day_card, "No weekday data yet.")
        else:
            canvas = charts.draw_bars(
                day_card, None, list(weekdays["short"]), list(weekdays["rate"]),
                colors=[charts.rate_color(r) for r in weekdays["rate"]],
            )
            canvas.get_tk_widget().pack(fill="x", pady=(4, 6))
            self.canvases.append(canvas)

    def _card_header(self, card, title, legend):
        header = tk.Frame(card, bg=CARD)
        header.pack(fill="x")
        tk.Label(header, text=title, font=font(12, True), bg=CARD, fg=TEXT).pack(side="left")
        if legend:
            key = tk.Frame(header, bg=CARD)
            key.pack(side="right")
            tk.Label(key, text="●", font=font(10), bg=CARD, fg=TEAL).pack(side="left")
            tk.Label(key, text=legend, font=font(9), bg=CARD, fg=MUTED).pack(side="left", padx=(4, 0))

    def _no_data(self, card, message):
        box = tk.Frame(card, bg=CARD, height=170)
        box.pack(fill="x", pady=8)
        box.pack_propagate(False)
        tk.Label(box, text=message, font=font(10), bg=CARD, fg=MUTED).pack(expand=True)

    # ---------------- CATEGORIES ----------------

    def _draw_categories(self, summary):
        self._clear(self.categories_row)
        for index in range(3):
            self.categories_row.grid_columnconfigure(index, weight=1, uniform="cats")

        rated = analytics.rated_students(summary).sort_values("Attendance Rate", ascending=False)

        groups = [
            ("Excellent (≥90%)", GREEN, rated[rated["Category"] == analytics.EXCELLENT]),
            ("Good (75–89%)", AMBER, rated[rated["Category"] == analytics.GOOD]),
            ("Needs Improvement (<75%)", RED, rated[rated["Category"] == analytics.NEEDS]),
        ]

        for column, (title, color, members) in enumerate(groups):
            card = Card(self.categories_row)
            card.grid(row=0, column=column, sticky="nsew", padx=(0, 14) if column < 2 else 0)

            head = tk.Frame(card, bg=CARD)
            head.pack(fill="x")
            tk.Frame(head, bg=color, width=4, height=16).pack(side="left", padx=(0, 8))
            tk.Label(head, text=title, font=font(10, True), bg=CARD, fg=TEXT, anchor="w",
                     justify="left", wraplength=190).pack(side="left")
            tk.Label(head, text=f"{len(members)}", font=font(9), bg=CARD, fg=MUTED).pack(side="right")

            body = tk.Frame(card, bg=CARD)
            body.pack(fill="both", expand=True, pady=(8, 0))

            if members.empty:
                tk.Label(body, text="No students in this range yet.", font=font(9), bg=CARD, fg=MUTED).pack(anchor="w", pady=4)

            for _, student in members.head(6).iterrows():
                line = tk.Frame(body, bg=CARD)
                line.pack(fill="x", pady=2)
                tk.Label(line, text=student["name"], font=font(10), bg=CARD, fg=TEXT).pack(side="left")
                tk.Label(line, text=f"{student['Attendance Rate']:.1f}%", font=font(10, True),
                         bg=CARD, fg=color).pack(side="right")

            if len(members) > 6:
                tk.Label(body, text=f"+ {len(members) - 6} more", font=font(9), bg=CARD, fg=MUTED).pack(anchor="w", pady=(4, 0))
