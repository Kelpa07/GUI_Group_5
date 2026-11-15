import matplotlib

matplotlib.use("TkAgg")

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import MaxNLocator

from theme import AMBER, GREEN, MUTED, RED, TEAL, TEXT

FONT = "Segoe UI"
GRID = "#E5E7EB"


def new_figure(width, height):
    fig = Figure(figsize=(width, height), dpi=100, facecolor="white")
    return fig


def clean_axes(ax):
    """Remove the boxy frame so charts match the flat Figma style."""
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.set_facecolor("white")


def draw_line(parent, frame, labels, values, width=5.6, height=2.6, ylabel=None):
    """Attendance trend line with markers."""
    fig = new_figure(width, height)
    ax = fig.add_subplot(111)
    clean_axes(ax)

    x = range(len(labels))
    ax.plot(x, values, color=TEAL, linewidth=2, marker="o", markersize=5,
            markerfacecolor=TEAL, markeredgecolor="white", markeredgewidth=1.2)

    ax.set_xticks(list(x))
    ax.set_xticklabels(_thin(labels), rotation=_rotation(labels), ha=_alignment(labels))
    ax.set_ylim(0, 105)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.grid(axis="y", color=GRID, linewidth=0.8, alpha=0.7)
    ax.set_axisbelow(True)

    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9, color=MUTED)

    fig.tight_layout(pad=1.2)
    return mount(parent, fig)


def draw_bars(parent, frame, labels, values, colors=None, width=5.6, height=2.6,
              show_values=True, value_suffix="%"):
    """Single-series bar chart, used for attendance by weekday."""
    fig = new_figure(width, height)
    ax = fig.add_subplot(111)
    clean_axes(ax)

    if colors is None:
        colors = [TEAL] * len(labels)

    bars = ax.bar(range(len(labels)), values, color=colors, width=0.55)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(_thin(labels, room=8), rotation=_rotation(labels, room=8),
                       ha=_alignment(labels, room=8))
    ax.set_ylim(0, 110)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.grid(axis="y", color=GRID, linewidth=0.8, alpha=0.7)
    ax.set_axisbelow(True)

    if show_values:
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 3,
                    f"{value:.0f}{value_suffix}", ha="center", fontsize=8,
                    color=TEXT, family=FONT)

    fig.tight_layout(pad=1.2)
    return mount(parent, fig)


def draw_donut(parent, frame, percent, width=1.6, height=1.6):
    """Small ring showing the overall attendance figure."""
    fig = new_figure(width, height)
    ax = fig.add_subplot(111)

    remaining = max(0.0, 100.0 - percent)
    ax.pie(
        [percent, remaining],
        colors=[TEAL, "#E8EDF2"],
        startangle=90,
        counterclock=False,
        wedgeprops={"width": 0.34, "edgecolor": "white"},
    )
    ax.set(aspect="equal")
    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.05, 1.05)
    return mount(parent, fig)


def draw_pie(parent, frame, labels, values, colors, width=4.2, height=2.8):
    """Category share of the class."""
    fig = new_figure(width, height)
    ax = fig.add_subplot(111)

    keep = [(l, v, c) for l, v, c in zip(labels, values, colors) if v > 0]
    if not keep:
        ax.text(0.5, 0.5, "No attendance data yet", ha="center", va="center",
                fontsize=10, color=MUTED, family=FONT)
        ax.axis("off")
        fig.tight_layout(pad=0.5)
        return mount(parent, fig)

    names, vals, cols = zip(*keep)
    ax.pie(
        vals,
        labels=names,
        colors=cols,
        autopct=lambda p: f"{p:.0f}%" if p > 0 else "",
        startangle=110,
        textprops={"fontsize": 9, "color": TEXT, "family": FONT},
        wedgeprops={"edgecolor": "white", "linewidth": 1.5},
    )
    ax.set(aspect="equal")
    fig.tight_layout(pad=0.8)
    return mount(parent, fig)


def draw_histogram(parent, frame, values, width=4.6, height=2.6):
    """Distribution of student attendance rates."""
    fig = new_figure(width, height)
    ax = fig.add_subplot(111)
    clean_axes(ax)

    if values:
        ax.hist(values, bins=[0, 50, 60, 70, 80, 90, 100], color=TEAL, edgecolor="white")
    ax.set_xlabel("Attendance rate (%)", fontsize=9, color=MUTED)
    ax.set_ylabel("Students", fontsize=9, color=MUTED)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(axis="y", color=GRID, linewidth=0.8, alpha=0.7)
    ax.set_axisbelow(True)

    fig.tight_layout(pad=1.2)
    return mount(parent, fig)


def mount(parent, fig):
    """Place a finished figure inside a Tkinter widget and return the canvas."""
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    widget = canvas.get_tk_widget()
    widget.config(bg="white", highlightthickness=0)
    canvas.fig = fig
    return canvas


def clear_canvas(canvas):
    """Destroy the Tk widget of a stored canvas before redrawing."""
    if canvas is not None:
        try:
            canvas.get_tk_widget().destroy()
        except Exception:
            pass


def rate_color(rate):
    if rate >= 90:
        return GREEN
    if rate >= 75:
        return AMBER
    return RED


def _step(labels, room=6):
    """How many labels to skip so the axis stays readable."""
    return max(1, -(-len(labels) // room))


def _thin(labels, room=6):
    """Blank out every other label when there are too many to fit."""
    step = _step(labels, room)
    return [label if index % step == 0 else "" for index, label in enumerate(labels)]


def _rotation(labels, room=6):
    return 0 if _step(labels, room) == 1 else 25


def _alignment(labels, room=6):
    return "center" if _step(labels, room) == 1 else "right"
