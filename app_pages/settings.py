import streamlit as st

import database
import sample_data
from web_utils import current_user

user = current_user()
settings = database.load_settings()
st.title("Settings")

with st.container(border=True):
    st.subheader("General settings")
    with st.form("general_settings"):
        school_name = st.text_input("School name", value=settings["school_name"])
        academic_year = st.text_input("Academic year", value=settings["academic_year"])
        late_threshold = st.number_input(
            "Late threshold (minutes)",
            min_value=0,
            max_value=240,
            value=int(settings["late_threshold"]),
        )
        minimum = st.number_input(
            "Minimum attendance percentage",
            min_value=0.0,
            max_value=100.0,
            value=float(settings["min_percentage"]),
            step=1.0,
        )
        track_saturdays = st.checkbox(
            "Track Saturdays",
            value=settings.get("track_saturdays") == "yes",
        )
        save_settings = st.form_submit_button("Save settings", type="primary")

    if save_settings:
        if not school_name.strip() or not academic_year.strip():
            st.error("School name and academic year cannot be empty.")
        else:
            database.save_settings(
                {
                    "school_name": school_name.strip(),
                    "academic_year": academic_year.strip(),
                    "late_threshold": str(late_threshold),
                    "min_percentage": str(minimum),
                    "track_saturdays": "yes" if track_saturdays else "no",
                }
            )
            st.success("Settings saved.")
            st.rerun()

with st.container(border=True):
    st.subheader("Demonstration data")
    student_count = sample_data.count_demo_students(user["id"])
    record_count = sample_data.count_demo_records(user["id"])
    if student_count:
        st.info(f"{student_count} demo students and {record_count} attendance records are loaded.")
        confirm_remove = st.checkbox("I want to remove the Demo Class records.")
        if st.button("Remove demo data", disabled=not confirm_remove):
            removed = sample_data.delete_demo_data(user["id"])
            st.success(f"Removed {removed} demo students and their attendance records.")
            st.rerun()
    else:
        st.write(
            "Load sample students in a separate Demo Class to explore the dashboard "
            "and reports. Your own class records are not changed."
        )
        if st.button("Load demo data", type="primary"):
            created, records = sample_data.create_demo_data(user["id"])
            st.success(f"Created {created} demo students and {records} attendance records.")
            st.rerun()
