import tkinter as tk
from tkinter import ttk


# ---------------- COLOURS ----------------

TEAL = "#0D9488"          # main brand colour
TEAL_DARK = "#0F766E"     # button hover / pressed
TEAL_SOFT = "#E6F7F5"     # selected sidebar item
BG = "#F4F6F8"            # page background (light grey)
CARD = "#FFFFFF"          # cards and tables
BORDER = "#E2E8F0"        # card borders
TEXT = "#1F2937"          # main text
MUTED = "#6B7280"         # secondary text
WHITE = "#FFFFFF"

RED = "#DC2626"
RED_SOFT = "#FEE2E2"
AMBER = "#F59E0B"
AMBER_SOFT = "#FEF3C7"
GREEN = "#10B981"
GREEN_SOFT = "#D1FAE5"
SLATE = "#334155"
SLATE_SOFT = "#E2E8F0"

# Colours used by the four attendance statuses
STATUS_COLORS = {
    "Present": (GREEN, "#ECFDF5"),
    "Absent": (RED, "#FEF2F2"),
    "Late": (AMBER, "#FFFBEB"),
    "Excused": (SLATE, "#F1F5F9"),
}


# ---------------- FONTS ----------------

def font(size=11, bold=False):
    """Return a font tuple. Segoe UI is the Windows UI font."""
    weight = "bold" if bold else "normal"
    return ("Segoe UI", size, weight)


# ---------------- TTK STYLES ----------------

def setup_styles(root):
    """Configure ttk styles once, right after the main window is created."""
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(
        "Treeview",
        background=CARD,
        fieldbackground=CARD,
        foreground=TEXT,
        rowheight=38,
        borderwidth=0,
        font=font(10),
    )
    style.configure(
        "Treeview.Heading",
        background="#F8FAFC",
        foreground=MUTED,
        font=font(10, True),
        borderwidth=0,
        relief="flat",
    )
    style.map(
        "Treeview",
        background=[("selected", TEAL_SOFT)],
        foreground=[("selected", TEAL_DARK)],
    )
    style.map(
        "Treeview.Heading",
        background=[("active", "#F8FAFC")],
    )

    style.configure(
        "TCombobox",
        fieldbackground=CARD,
        background=CARD,
        foreground=TEXT,
        arrowcolor=TEXT,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
        padding=6,
        font=font(10),
    )
    style.configure(
        "TEntry",
        fieldbackground=CARD,
        foreground=TEXT,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
        padding=6,
    )

    style.configure(
        "Vertical.TScrollbar",
        background="#CBD5E1",
        troughcolor=BG,
        bordercolor=BG,
        arrowcolor=WHITE,
    )


# ---------------- REUSABLE WIDGETS ----------------

class Card(tk.Frame):
    """A white panel with a thin grey border, used for every card in the UI."""

    def __init__(self, parent, padx=16, pady=14, bg=CARD):
        super().__init__(
            parent,
            bg=bg,
            padx=padx,
            pady=pady,
            highlightbackground=BORDER,
            highlightcolor=BORDER,
            highlightthickness=1,
            bd=0,
        )


class TitleBlock(tk.Frame):
    """Page title plus a small grey subtitle, shown at the top of each screen."""

    def __init__(self, parent, title, subtitle=""):
        super().__init__(parent, bg=BG)
        tk.Label(self, text=title, font=font(20, True), bg=BG, fg=TEXT).pack(anchor="w")
        self.subtitle_label = tk.Label(self, text=subtitle, font=font(10), bg=BG, fg=MUTED)
        self.subtitle_label.pack(anchor="w")


class Button(tk.Label):
    """
    A flat coloured button drawn with a Label.
    Label is used instead of tk.Button so we control the exact colours
    and the rounded-corner look is replaced by a clean flat rectangle.
    """

    def __init__(self, parent, text, command=None, kind="primary", width=None, padx=18, pady=8):
        colors = {
            "primary": (TEAL, WHITE, TEAL_DARK),
            "ghost": (CARD, TEXT, "#F1F5F9"),
            "danger": (RED, WHITE, "#B91C1C"),
        }
        base_fg, base_text, hover = colors[kind]
        self.base_bg = base_fg
        self.hover_bg = hover
        self.command = command

        super().__init__(
            parent,
            text=text,
            font=font(11, True),
            bg=base_fg,
            fg=base_text,
            padx=padx,
            pady=pady,
            cursor="hand2",
            width=width,
        )
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", lambda e: self.config(bg=self.hover_bg))
        self.bind("<Leave>", lambda e: self.config(bg=self.base_bg))

    def _on_click(self, event):
        if self.command:
            self.command()


class Field(tk.Frame):
    """
    A labelled input box with its own inline error message,
    following the validation style used in our lecture form example.
    """

    def __init__(self, parent, label, variable, show="", placeholder="", bg=CARD,
                 label_on_top=True, width=None):
        super().__init__(parent, bg=bg)
        self.placeholder = placeholder
        self.variable = variable

        if label_on_top and label:
            tk.Label(self, text=label, font=font(10, True), bg=bg, fg=TEXT).pack(anchor="w")

        self.entry = tk.Entry(
            self,
            textvariable=variable,
            font=font(11),
            bg=CARD,
            fg=TEXT,
            relief="flat",
            show=show,
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=TEAL,
            insertbackground=TEXT,
            width=width,
        )
        self.entry.pack(fill="x", ipady=8, pady=(4, 0) if label_on_top else 0)

        self.error = tk.Label(self, text="", font=font(9), bg=bg, fg=RED)
        self.error.pack(anchor="w")

        if placeholder:
            self._show_placeholder()
            self.entry.bind("<FocusIn>", self._clear_placeholder)
            self.entry.bind("<FocusOut>", self._show_placeholder)

    def _show_placeholder(self, event=None):
        if self.variable.get() == "" and self.placeholder:
            self.entry.config(fg="#9CA3AF")
            self.variable.set(self.placeholder)
            self._is_placeholder = True

    def _clear_placeholder(self, event=None):
        if getattr(self, "_is_placeholder", False):
            self.variable.set("")
            self._is_placeholder = False
        self.entry.config(fg=TEXT)

    def get(self):
        """Return the real value, ignoring placeholder text."""
        value = self.variable.get().strip()
        if self.placeholder and value == self.placeholder.strip():
            return ""
        return value

    def set_error(self, message):
        self.error.config(text=message)

    def clear_error(self):
        self.error.config(text="")


def make_entry(parent, variable, bg=CARD, width=None, show=""):
    """A plain bordered entry box (used inside grid layouts)."""
    entry = tk.Entry(
        parent,
        textvariable=variable,
        font=font(11),
        bg=CARD,
        fg=TEXT,
        relief="flat",
        show=show,
        highlightthickness=1,
        highlightbackground=BORDER,
        highlightcolor=TEAL,
        insertbackground=TEXT,
        width=width,
    )
    return entry


def add_placeholder(entry, variable, text):
    """Show grey hint text in an entry until the user types in it."""
    state = {"shown": False}

    def show(event=None):
        if variable.get() == "":
            variable.set(text)
            entry.configure(fg="#9CA3AF")
            state["shown"] = True

    def clear(event=None):
        if state["shown"]:
            variable.set("")
            entry.configure(fg=TEXT)
            state["shown"] = False

    entry.bind("<FocusIn>", clear)
    entry.bind("<FocusOut>", show)
    show()
    return state


class Toggle(tk.Canvas):
    """A working on/off switch used on the Settings screen."""

    def __init__(self, parent, variable, bg=CARD):
        super().__init__(parent, width=44, height=24, bg=bg, highlightthickness=0, bd=0)
        self.variable = variable
        self.config(cursor="hand2")
        self.bind("<Button-1>", self._toggle)
        self.variable.trace_add("write", lambda *a: self.draw())
        self.draw()

    def _toggle(self, event=None):
        self.variable.set(not self.variable.get())

    def draw(self):
        self.delete("all")
        on = self.variable.get()
        track = TEAL if on else "#CBD5E1"
        knob = WHITE
        self.create_rectangle(2, 2, 42, 22, fill=track, outline=track)
        self.create_oval(2, 2, 42, 22, fill=track, outline=track)
        x0 = 24 if on else 4
        self.create_oval(x0, 4, x0 + 16, 20, fill=knob, outline=knob)
