"""
main.py
Application entry point.

One Tk window is created here. A fixed sidebar on the left switches between the
screens, which are ordinary Frames packed into a scrollable content area.
Nothing opens a second window except small modal dialogs for editing records.

Run with:  python main.py
"""

import tkinter as tk
from tkinter import ttk

import database
from theme import (
    BG, BORDER, CARD, MUTED, RED, TEAL, TEAL_DARK, TEAL_SOFT, TEXT, WHITE,
    font, setup_styles,
)

# Sidebar order. Each entry is (key, label, icon character).
NAV_ITEMS = [
    ("dashboard", "Dashboard", "◉"),
    ("attendance", "Attendance", "✓"),
    ("students", "Students", "☰"),
    ("reports", "Reports", "▦"),
    ("profile", "My Profile", "☺"),
    ("settings", "Settings", "⚙"),
]


class AttendTrackApp:
    """Owns the main window, the sidebar and the current screen."""

    def __init__(self, root):
        self.root = root
        self.user = None
        self.settings = database.load_settings()
        self.frames = {}
        self.current = None

        root.title("AttendTrack - Student Attendance Tracker")
        root.geometry(self._start_geometry())
        root.minsize(900, 600)
        root.configure(bg=BG)

        setup_styles(root)

        self.container = tk.Frame(root, bg=BG)
        self.container.pack(fill="both", expand=True)

        self.show_auth()

    def _start_geometry(self):
        """Open at a sensible size for the screen the app is started on."""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = min(1280, screen_width - 20)
        height = min(820, screen_height - 60)
        return f"{width}x{height}"

    # ---------------- AUTH ----------------

    def show_auth(self):
        """Destroy the application shell and show sign up / log in again."""
        self._clear_container()
        self.frames = {}
        self.current = None
        self.user = None

        import auth

        self.auth_frame = auth.AuthFrame(self.container, self)
        self.auth_frame.pack(fill="both", expand=True)

    def start_session(self, user):
        """Called after a successful sign up or login."""
        self.user = user
        self.settings = database.load_settings()
        self._clear_container()
        self._build_shell()
        self.apply_settings()
        self.show_screen("dashboard")

    def logout(self):
        self.show_auth()

    def _clear_container(self):
        for child in self.container.winfo_children():
            child.destroy()

    # ---------------- SHELL ----------------

    def _build_shell(self):
        self.sidebar = tk.Frame(
            self.container, bg=CARD, width=212,
            highlightbackground=BORDER, highlightcolor=BORDER, highlightthickness=1,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand = tk.Frame(self.sidebar, bg=CARD)
        brand.pack(fill="x", padx=16, pady=(20, 24))

        icon = tk.Canvas(brand, width=32, height=32, bg=TEAL, highlightthickness=0, bd=0)
        icon.pack(side="left")
        icon.create_rectangle(0, 0, 32, 32, fill=TEAL, outline=TEAL)
        icon.create_polygon(6, 14, 16, 8, 26, 14, 16, 20, fill=WHITE, outline=WHITE)
        icon.create_line(10, 17, 10, 24, fill=WHITE, width=2)
        icon.create_line(10, 24, 22, 24, fill=WHITE, width=2)

        tk.Label(brand, text="AttendTrack", font=font(14, True), bg=CARD, fg=TEXT).pack(side="left", padx=(10, 0))

        self.nav_buttons = {}
        for key, label, glyph in NAV_ITEMS:
            row = tk.Frame(self.sidebar, bg=CARD, cursor="hand2")
            row.pack(fill="x", padx=10, pady=2)

            indicator = tk.Frame(row, bg=CARD, width=3)
            indicator.pack(side="left", fill="y")

            body = tk.Frame(row, bg=CARD, padx=10, pady=9)
            body.pack(side="left", fill="x", expand=True)

            tk.Label(body, text=glyph, font=font(12), bg=CARD, fg=MUTED, width=2).pack(side="left")
            text = tk.Label(body, text=label, font=font(11), bg=CARD, fg=TEXT)
            text.pack(side="left", padx=(8, 0))

            parts = (row, indicator, body, text)
            self.nav_buttons[key] = parts

            for widget in parts:
                widget.bind("<Button-1>", lambda event, name=key: self.show_screen(name))

            # Left border like the Figma design.
            row.configure(highlightbackground=CARD, highlightcolor=CARD, highlightthickness=0)

        self._build_footer()

        # Scrollable content area on the right.
        self.canvas = tk.Canvas(self.container, bg=BG, highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(self.container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.page_holder = tk.Frame(self.canvas, bg=BG)
        self.page_window = self.canvas.create_window((0, 0), window=self.page_holder, anchor="nw")

        self.page_holder.bind("<Configure>", self._on_page_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _build_footer(self):
        footer = tk.Frame(self.sidebar, bg=CARD)
        footer.pack(side="bottom", fill="x", padx=14, pady=(0, 16))

        tk.Frame(footer, bg=BORDER, height=1).pack(fill="x", pady=(0, 12))

        row = tk.Frame(footer, bg=CARD, cursor="hand2")
        row.pack(fill="x")

        avatar = tk.Canvas(row, width=34, height=34, bg=CARD, highlightthickness=0, bd=0)
        avatar.pack(side="left")
        avatar.create_oval(1, 1, 33, 33, fill="#E2E8F0", outline="#E2E8F0")
        avatar.create_oval(11, 8, 23, 20, fill="#94A3B8", outline="#94A3B8")
        avatar.create_arc(4, 18, 30, 40, start=200, extent=140, fill="#94A3B8", outline="#94A3B8")

        names = tk.Frame(row, bg=CARD)
        names.pack(side="left", padx=(10, 0))
        self.user_name_label = tk.Label(names, text=self.user["name"], font=font(11, True), bg=CARD, fg=TEXT, anchor="w")
        self.user_name_label.pack(fill="x")
        self.user_role_label = tk.Label(names, text=self.user.get("department") or "PRG 304", font=font(9), bg=CARD, fg=MUTED, anchor="w")
        self.user_role_label.pack(fill="x")

        for widget in (row, avatar, names, self.user_name_label, self.user_role_label):
            widget.bind("<Button-1>", lambda e: self.show_screen("profile"))

        logout = tk.Label(footer, text="Log Out", font=font(10, True), bg=CARD, fg=RED, cursor="hand2")
        logout.pack(anchor="w", pady=(10, 0))
        logout.bind("<Button-1>", lambda e: self.logout())

    # ---------------- NAVIGATION ----------------

    def show_screen(self, name):
        """Hide the current frame and show (building it the first time)."""
        frame = self.get_frame(name)
        if frame is None:
            return

        if self.current is not None:
            self.current.pack_forget()

        frame.pack(fill="both", expand=True)
        self.current = frame
        self._highlight(name)

        if hasattr(frame, "refresh"):
            frame.refresh()

        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto(0)

    def get_frame(self, name):
        if name in self.frames:
            return self.frames[name]

        builders = {
            "dashboard": ("dashboard", "DashboardFrame"),
            "attendance": ("attendance", "AttendanceFrame"),
            "students": ("students", "StudentsFrame"),
            "reports": ("reports", "ReportsFrame"),
            "profile": ("profile", "ProfileFrame"),
            "settings": ("settings", "SettingsFrame"),
        }
        if name not in builders:
            return None

        module_name, class_name = builders[name]
        import importlib

        module = importlib.import_module(module_name)
        frame_class = getattr(module, class_name)
        frame = frame_class(self.page_holder, self)
        self.frames[name] = frame
        return frame

    def _highlight(self, active_key):
        for key, (row, indicator, body, text) in self.nav_buttons.items():
            active = key == active_key
            background = TEAL_SOFT if active else CARD
            foreground = TEAL_DARK if active else TEXT
            for widget in (row, indicator, body, text):
                widget.configure(bg=background)
            text.configure(fg=foreground, font=font(11, active))
            indicator.configure(bg=TEAL if active else background)

    # ---------------- SHARED HELPERS FOR SCREENS ----------------

    def reload_settings(self):
        self.settings = database.load_settings()

    def apply_settings(self):
        """Push saved settings into the parts of the shell that display them."""
        self.root.title(self.school_name() + "  ·  AttendTrack")

    def min_percentage(self):
        try:
            return float(self.settings.get("min_percentage", "75"))
        except (TypeError, ValueError):
            return 75.0

    def academic_year(self):
        return self.settings.get("academic_year", "")

    def school_name(self):
        return self.settings.get("school_name", "AttendTrack")

    def status_text(self, user):
        self.user = user
        self.user_name_label.configure(text=user["name"])
        self.user_role_label.configure(text=user.get("department") or "PRG 304")

    # ---------------- SCROLLING ----------------

    def _on_page_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self.page_window, width=event.width)

    def _on_mousewheel(self, event):
        total = self.canvas.bbox("all")
        if total is None:
            return
        needs_scroll = total[3] > self.canvas.winfo_height()
        if not needs_scroll:
            return
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


def main():
    database.init_database()
    root = tk.Tk()
    AttendTrackApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
