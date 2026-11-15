from datetime import date, datetime

import pandas as pd
import streamlit as st

import analytics
import database
from web_utils import current_user, student_summary

user = current_user()
st.title("Reports")
st.caption("Filter attendance records, explore trends, and download CSV reports.")

dates = database.fetch_all_dates(user["id"])
start_default = datetime.strptime(dates[0], "%Y-%m-%d").date() if dates else date.today()
filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
with filter_col1:
    start_date = st.date_input("From", value=start_default, key="report_from")
with filter_col2:
    end_date = st.date_input("To", value=date.today(), key="report_to")
with filter_col3:
    classes = ["All classes"] + database.fetch_classes(user["id"])
    chosen_class = st.selectbox("Class", classes, key="report_class")
class_name = "" if chosen_class == "All classes" else chosen_class
with filter_col4:
    sections = ["All sections"] + database.fetch_sections(user["id"], class_name)
    chosen_section = st.selectbox("Section", sections, key="report_section")
section = "" if chosen_section == "All sections" else chosen_section

if start_date > end_date:
    st.error("The start date must be on or before the end date.")
    st.stop()

frame = analytics.load_dataframe(
    user["id"], class_name, section, start_date.isoformat(), end_date.isoformat()
)
summary = student_summary(user["id"], frame, class_name, section)
counts = analytics.status_totals(frame)
overall = analytics.overall_rate(frame)
most_absent_day, absent_rate = analytics.most_absent_day(frame)
minimum = float(database.load_settings().get("min_percentage", "75"))
below_minimum = analytics.students_below(summary, minimum)

with st.container(horizontal=True):
    st.metric("Registered students", len(summary), border=True)
    st.metric("Overall attendance", f"{overall:.1f}%", border=True)
    st.metric("Eligible records", counts["Present"] + counts["Absent"] + counts["Late"], border=True)
    st.metric(
        "Most absent weekday",
        most_absent_day,
        f"{absent_rate:.1f}% absent" if most_absent_day != "No data" else None,
        border=True,
    )
    st.metric("Below minimum", len(below_minimum), f"Threshold: {minimum:g}%", border=True)

left, right = st.columns(2)
with left, st.container(border=True):
    st.subheader("Attendance by section")
    section_rates = analytics.group_rates(frame, "section")
    if section_rates.empty:
        st.info("No attendance in this date range.")
    else:
        st.bar_chart(section_rates.set_index("section")["rate"], y_label="Attendance rate (%)")
with right, st.container(border=True):
    st.subheader("Monthly attendance trend")
    monthly = analytics.monthly_trend(frame)
    if monthly.empty:
        st.info("No monthly data in this date range.")
    else:
        st.line_chart(monthly.set_index("month")["rate"], y_label="Attendance rate (%)")

left, right = st.columns(2)
with left, st.container(border=True):
    st.subheader("Student categories")
    category_counts = analytics.category_counts(summary)
    values = {
        "Excellent": category_counts[analytics.EXCELLENT],
        "Good": category_counts[analytics.GOOD],
        "Needs improvement": category_counts[analytics.NEEDS],
    }
    if sum(values.values()):
        st.bar_chart(pd.Series(values, name="Students"), y_label="Students")
    else:
        st.info("No eligible attendance records for this selection.")
with right, st.container(border=True):
    st.subheader("Attendance rate distribution")
    rated = analytics.rated_students(summary)
    if rated.empty:
        st.info("No attendance rates to plot.")
    else:
        bins = [0, 50, 60, 70, 80, 90, 100]
        labels = ["0–50%", "50–60%", "60–70%", "70–80%", "80–90%", "90–100%"]
        counts_by_range = pd.cut(
            rated["Attendance Rate"], bins=bins, labels=labels, include_lowest=True
        ).value_counts(sort=False)
        distribution = pd.DataFrame(
            {"Students": counts_by_range.to_numpy()},
            index=pd.Index(labels, name="Attendance rate"),
        )
        st.bar_chart(distribution, y_label="Students")

st.subheader("Descriptive statistics")
stats = {key: str(value) for key, value in analytics.descriptive_stats(summary).items()}
st.table(stats, border="horizontal", width="content")

st.subheader("Individual student attendance")
export_columns = [
    "student_id", "name", "class_name", "section", "Present", "Absent", "Late",
    "Excused", "Eligible Days", "Attendance Rate", "Category",
]
st.dataframe(
    summary[export_columns],
    hide_index=True,
    column_config={
        "student_id": st.column_config.TextColumn("Student ID"),
        "name": st.column_config.TextColumn("Student name"),
        "class_name": st.column_config.TextColumn("Class"),
        "Attendance Rate": st.column_config.NumberColumn("Rate (%)", format="%.1f%%"),
    },
)

student_csv = summary[export_columns].to_csv(index=False).encode("utf-8-sig")
record_columns = ["student_id", "name", "class_name", "section", "date", "status"]
records = frame[record_columns].copy()
if not records.empty:
    records["date"] = records["date"].dt.strftime("%Y-%m-%d")
records_csv = records.to_csv(index=False).encode("utf-8-sig")
download_left, download_right = st.columns(2)
with download_left:
    st.download_button(
        "Download student rates (CSV)",
        student_csv,
        file_name="student_attendance_rates.csv",
        mime="text/csv",
    )
with download_right:
    st.download_button(
        "Download attendance records (CSV)",
        records_csv,
        file_name="attendance_records.csv",
        mime="text/csv",
    )
