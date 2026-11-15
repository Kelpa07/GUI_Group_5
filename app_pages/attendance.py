from datetime import date

import pandas as pd
import streamlit as st

import database
from web_utils import current_user

user = current_user()
settings = database.load_settings()
st.title("Mark attendance")
st.caption("Choose a class and date, update each student's status, then save.")

classes = database.fetch_classes(user["id"])
if not classes:
    st.info("Add students first on the Students page.")
    st.stop()

class_name = st.selectbox("Class", classes, key="attendance_class")
sections = database.fetch_sections(user["id"], class_name)
if not sections:
    st.info("There are no sections in this class.")
    st.stop()
section = st.selectbox("Section", sections, key="attendance_section")
attendance_date = st.date_input("Attendance date", value=date.today(), key="attendance_date")

if attendance_date > date.today():
    st.error("Attendance cannot be recorded for a future date.")
    st.stop()
if attendance_date.weekday() == 5 and settings.get("track_saturdays") != "yes":
    st.warning("Saturday attendance is disabled. Change this in Settings to record a Saturday.")
    st.stop()

students = database.fetch_students(user["id"], class_name=class_name, section=section)
saved = database.fetch_attendance_for_date(user["id"], attendance_date.isoformat())
editor_data = pd.DataFrame(
    [
        {
            "Student ID": student["student_id"],
            "Student name": student["name"],
            "Status": saved.get(student["id"], "Present"),
            "Student row": student["id"],
        }
        for student in students
    ]
)

if editor_data.empty:
    st.info("No students are registered in this class and section.")
    st.stop()

st.caption(f"Late threshold reminder: after {settings.get('late_threshold', '15')} minutes.")
edited = st.data_editor(
    editor_data,
    hide_index=True,
    disabled=["Student ID", "Student name", "Student row"],
    column_config={
        "Status": st.column_config.SelectboxColumn(
            "Attendance status",
            options=list(database.STATUSES),
            required=True,
        ),
        "Student row": None,
    },
    key=f"attendance_editor_{attendance_date}_{class_name}_{section}",
)

has_existing = any(student["id"] in saved for student in students)
overwrite = False
if has_existing:
    overwrite = st.checkbox(
        "I confirm that saving will replace this class's existing attendance for this date.",
        key=f"attendance_overwrite_{attendance_date}_{class_name}_{section}",
    )

if st.button("Save attendance", type="primary", icon=":material/save:"):
    if has_existing and not overwrite:
        st.warning("Confirm the update before replacing existing attendance.")
    elif not edited["Status"].isin(database.STATUSES).all():
        st.error("Choose a valid attendance status for every student.")
    else:
        expected_rows = {int(student["id"]) for student in students}
        submitted_rows = [int(row_id) for row_id in edited["Student row"]]
        if set(submitted_rows) != expected_rows or len(submitted_rows) != len(expected_rows):
            st.error("The attendance list changed unexpectedly. Reload the page and try again.")
            st.stop()
        entries = [
            (int(row["Student row"]), attendance_date.isoformat(), row["Status"])
            for _, row in edited.iterrows()
        ]
        database.save_attendance(user["id"], entries)
        st.success(f"Saved attendance for {len(entries)} students.")
        st.rerun()
