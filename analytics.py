import pandas as pd
import database

# Order matters: these labels are also used for the chart legends.
ELIGIBLE_STATUSES = ("Present", "Absent", "Late")
WEEK_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
SHORT_WEEK = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

EXCELLENT = "Excellent"
GOOD = "Good"
NEEDS = "Needs Improvement"


def load_dataframe(owner_id, class_name="", section="", start_date="", end_date=""):
    """
    Read attendance rows from SQLite and return one clean DataFrame.

    The merge with the students table means every attendance record also
    carries the student name, class and section, so later grouping is simple.
    """
    conn = database.get_connection()
    try:
        sql = """
            SELECT a.student_row, s.student_id, s.name, s.class_name, s.section,
                   a.date, a.status
              FROM attendance a
              JOIN students s ON s.id = a.student_row
             WHERE a.owner_id = ?
        """
        params = [owner_id]

        if class_name:
            sql += " AND s.class_name = ?"
            params.append(class_name)
        if section:
            sql += " AND s.section = ?"
            params.append(section)
        if start_date:
            sql += " AND a.date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND a.date <= ?"
            params.append(end_date)

        df = pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()

    if df.empty:
        return make_empty_frame()

    # ---- Data cleaning (proposal: remove duplicates, fix types, drop blanks) ----
    df = df.drop_duplicates(subset=["student_row", "date"])
    df = df.dropna(subset=["date", "status"])
    df["status"] = df["status"].str.strip()
    df = df[df["status"].isin(database.STATUSES)]
    df["name"] = df["name"].str.strip()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df["day_name"] = df["date"].dt.day_name()
    df["month"] = df["date"].dt.strftime("%b %Y")
    df["month_key"] = df["date"].dt.strftime("%Y-%m")

    return df.sort_values("date").reset_index(drop=True)


def make_empty_frame():
    return pd.DataFrame(
        columns=[
            "student_row", "student_id", "name", "class_name", "section",
            "date", "status", "day_name", "month", "month_key",
        ]
    )


# ---------------- INDIVIDUAL RATES ----------------

def student_summary(owner_id, df):
    """
    One row per registered student with their counts, attendance rate and
    category. Students who have attendance but were deleted are not shown.
    """
    students = database.fetch_students(owner_id)
    columns = ["student_row", "student_id", "name", "class_name", "section"]
    if students:
        master = pd.DataFrame(students, columns=["id"] + columns[1:]).rename(columns={"id": "student_row"})
    else:
        master = pd.DataFrame(columns=columns)

    if df.empty:
        for status in database.STATUSES:
            master[status] = 0
    else:
        counts = df.pivot_table(
            index="student_row", columns="status", values="date", aggfunc="count", fill_value=0
        )
        for status in database.STATUSES:
            if status not in counts.columns:
                counts[status] = 0
        counts = counts[list(database.STATUSES)]
        master = master.merge(counts, left_on="student_row", right_index=True, how="left")

    for status in database.STATUSES:
        master[status] = master[status].fillna(0).astype(int)

    master["Total Records"] = master[list(database.STATUSES)].sum(axis=1)
    master["Eligible Days"] = master[list(ELIGIBLE_STATUSES)].sum(axis=1)

    # The core formula. Students with zero eligible days stay blank on purpose.
    master["Attendance Rate"] = [
        round(p / e * 100, 1) if e > 0 else None
        for p, e in zip(master["Present"], master["Eligible Days"])
    ]
    master["Category"] = master["Attendance Rate"].apply(category_of)
    return master.sort_values(["class_name", "section", "name"]).reset_index(drop=True)


def category_of(rate):
    """Excellent >= 90, Good 75-89, Needs Improvement below 75."""
    if rate is None or (isinstance(rate, float) and pd.isna(rate)):
        return "No Data"
    if rate >= 90:
        return EXCELLENT
    if rate >= 75:
        return GOOD
    return NEEDS


def rated_students(summary):
    """Only the students that can be turned into a percentage."""
    return summary[summary["Attendance Rate"].notna()]


def overall_rate(df):
    """Overall attendance using the same rule as the individual rates."""
    if df.empty:
        return 0.0
    counts = df["status"].value_counts()
    present = int(counts.get("Present", 0))
    eligible = sum(int(counts.get(s, 0)) for s in ELIGIBLE_STATUSES)
    if eligible == 0:
        return 0.0
    return round(present / eligible * 100, 1)


def category_counts(summary):
    """How many students sit in each of the three categories."""
    rated = rated_students(summary)
    return {
        EXCELLENT: int((rated["Category"] == EXCELLENT).sum()),
        GOOD: int((rated["Category"] == GOOD).sum()),
        NEEDS: int((rated["Category"] == NEEDS).sum()),
        "No Data": int((summary["Category"] == "No Data").sum()),
    }


def students_below(summary, minimum):
    """Students whose rate is under the minimum set in Settings."""
    rated = rated_students(summary)
    return rated[rated["Attendance Rate"] < minimum]


# ---------------- GROUPING FOR CHARTS ----------------

def rate_from_counts(group):
    """Turn one grouped frame of status counts into a percentage."""
    counts = group["status"].value_counts()
    present = int(counts.get("Present", 0))
    eligible = sum(int(counts.get(s, 0)) for s in ELIGIBLE_STATUSES)
    if eligible == 0:
        return None
    return round(present / eligible * 100, 1)


def daily_trend(df, limit=10):
    """Attendance rate for the most recent dates, oldest first."""
    if df.empty:
        return pd.DataFrame(columns=["label", "rate"])

    rows = []
    for date, group in df.groupby("date"):
        rate = rate_from_counts(group)
        if rate is not None:
            rows.append({"date": date, "label": date.strftime("%d %b"), "rate": rate})

    trend = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    if limit and len(trend) > limit:
        trend = trend.tail(limit).reset_index(drop=True)
    return trend


def weekday_rates(df):
    """Average attendance rate for each weekday that has data."""
    if df.empty:
        return pd.DataFrame(columns=["day", "short", "rate"])

    rows = []
    for day, group in df.groupby("day_name"):
        rate = rate_from_counts(group)
        if rate is not None and day in WEEK_ORDER:
            rows.append({"day": day, "short": SHORT_WEEK[WEEK_ORDER.index(day)], "rate": rate})

    result = pd.DataFrame(rows)
    if result.empty:
        return pd.DataFrame(columns=["day", "short", "rate"])
    result["order"] = result["day"].map({d: i for i, d in enumerate(WEEK_ORDER)})
    return result.sort_values("order").drop(columns=["order", "day"]).reset_index(drop=True)


def group_rates(df, by):
    """Attendance rate per class or per section, as a two column frame."""
    if df.empty:
        return pd.DataFrame(columns=[by, "rate"])
    rows = []
    for key, group in df.groupby(by):
        rate = rate_from_counts(group)
        if rate is not None:
            rows.append({by: str(key), "rate": rate})
    result = pd.DataFrame(rows).sort_values(by).reset_index(drop=True)
    return result


def monthly_trend(df):
    """Attendance rate per calendar month, in date order."""
    if df.empty:
        return pd.DataFrame(columns=["month", "rate"])
    rows = []
    for key, group in df.groupby("month_key"):
        rate = rate_from_counts(group)
        if rate is not None:
            label = group["month"].iloc[0]
            rows.append({"month_key": key, "month": label, "rate": rate})
    result = pd.DataFrame(rows).sort_values("month_key").reset_index(drop=True)
    return result.drop(columns=["month_key"])


def status_totals(df):
    """Count of each of the four statuses in the current selection."""
    counts = {s: 0 for s in database.STATUSES}
    if not df.empty:
        for status, n in df["status"].value_counts().items():
            counts[status] = int(n)
    return counts


def most_absent_day(df):
    """Weekday carrying the highest average absence rate."""
    if df.empty:
        return "No data", 0.0
    rows = []
    for day, group in df.groupby("day_name"):
        counts = group["status"].value_counts()
        eligible = sum(int(counts.get(s, 0)) for s in ELIGIBLE_STATUSES)
        if eligible:
            rows.append({"day": day, "absent": round(int(counts.get("Absent", 0)) / eligible * 100, 1)})
    if not rows:
        return "No data", 0.0
    frame = pd.DataFrame(rows).sort_values("absent", ascending=False).reset_index(drop=True)
    return frame.loc[0, "day"], frame.loc[0, "absent"]


# ---------------- DESCRIPTIVE STATISTICS (EDA) ----------------

def descriptive_stats(summary):
    """
    The measures listed in the proposal: mean, median, mode, minimum,
    maximum, count and standard deviation of the attendance rates.
    """
    rated = rated_students(summary)
    rates = rated["Attendance Rate"].astype(float)

    if rates.empty:
        return {
            "Count of students analysed": 0,
            "Mean attendance rate": "-",
            "Median attendance rate": "-",
            "Mode attendance rate": "-",
            "Minimum rate": "-",
            "Maximum rate": "-",
            "Standard deviation": "-",
        }

    modes = rates.mode()
    mode_text = ", ".join(f"{m:.1f}%" for m in modes.head(3))

    return {
        "Count of students analysed": int(rates.count()),
        "Mean attendance rate": f"{rates.mean():.1f}%",
        "Median attendance rate": f"{rates.median():.1f}%",
        "Mode attendance rate": mode_text,
        "Minimum rate": f"{rates.min():.1f}%",
        "Maximum rate": f"{rates.max():.1f}%",
        "Standard deviation": f"{rates.std(ddof=0):.1f}%" if rates.count() > 1 else "0.0%",
    }
