from datetime import date

import pandas as pd
import streamlit as st

import analytics
import database
from web_utils import class_section_filters, current_user, student_summary

user = current_user()
st.title("Dashboard")
st.caption(f"Academic year {database.load_settings()['academic_year']}")

with st.sidebar:
    st.subheader("Dashboard filters")
    class_name, section = class_section_filters(user["id"], "dashboard")

frame = analytics.load_dataframe(user["id"], class_name, section)
summary = student_summary(user["id"], frame, class_name, section)
today = pd.Timestamp(date.today())
today_frame = frame[frame["date"] == today] if not frame.empty else frame
if today_frame.empty and not frame.empty:
    latest = frame["date"].max()
    today_frame = frame[frame["date"] == latest]
    day_label = f"Latest day · {latest.strftime('%d %b %Y')}"
else:
    day_label = "Today"

counts = analytics.status_totals(today_frame)
with st.container(horizontal=True):
    st.metric("Students", len(summary), border=True)
    st.metric("Overall attendance", f"{analytics.overall_rate(frame):.1f}%", border=True)
    st.metric(f"Present · {day_label}", counts["Present"], border=True)
    st.metric(f"Absent · {day_label}", counts["Absent"], border=True)
    st.metric(f"Late · {day_label}", counts["Late"], border=True)

left, right = st.columns(2)
with left, st.container(border=True):
    st.subheader("Attendance trend")
    trend = analytics.daily_trend(frame, limit=10)
    if trend.empty:
        st.info("Mark attendance to see a trend.")
    else:
        st.line_chart(trend.set_index("label")["rate"], y_label="Attendance rate (%)")

with right, st.container(border=True):
    st.subheader("Attendance by weekday")
    weekdays = analytics.weekday_rates(frame)
    if weekdays.empty:
        st.info("No weekday data yet.")
    else:
        st.bar_chart(weekdays.set_index("short")["rate"], y_label="Attendance rate (%)")

st.subheader("Student categories")
rated = analytics.rated_students(summary).sort_values("Attendance Rate", ascending=False)
categories = [
    (analytics.EXCELLENT, "Excellent · 90% and above"),
    (analytics.GOOD, "Good · 75–89%"),
    (analytics.NEEDS, "Needs improvement · below 75%"),
]
category_columns = st.columns(3)
for column, (category, label) in zip(category_columns, categories):
    with column, st.container(border=True):
        members = rated[rated["Category"] == category]
        st.markdown(f"**{label}** · {len(members)}")
        if members.empty:
            st.caption("No students in this category.")
        else:
            st.dataframe(
                members[["student_id", "name", "Attendance Rate"]].head(6),
                hide_index=True,
                column_config={
                    "student_id": st.column_config.TextColumn("Student ID"),
                    "Attendance Rate": st.column_config.NumberColumn("Rate (%)", format="%.1f%%"),
                },
            )
