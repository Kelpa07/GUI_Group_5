import pandas as pd
import streamlit as st

import analytics
import database
from web_utils import current_user

user = current_user()
st.title("Students")
st.caption("Add, search, update, and remove student records.")

with st.expander("Add a student", expanded=False):
    with st.form("add_student"):
        new_id = st.text_input("Student ID", max_chars=40)
        new_name = st.text_input("Student name", max_chars=100)
        new_class = st.text_input("Class", max_chars=80)
        new_section = st.text_input("Section", max_chars=80)
        add_submitted = st.form_submit_button("Add student", type="primary")
    if add_submitted:
        new_id, new_name = new_id.strip(), new_name.strip()
        new_class, new_section = new_class.strip(), new_section.strip()
        if not all((new_id, new_name, new_class, new_section)):
            st.error("Student ID, name, class, and section are required.")
        elif any(character.isdigit() for character in new_name):
            st.error("Student name cannot contain numbers.")
        elif database.student_id_exists(user["id"], new_id):
            st.error("That student ID is already in use.")
        elif database.add_student(user["id"], new_id, new_name, new_class, new_section) is None:
            st.error("The student could not be added.")
        else:
            st.success(f"Added {new_name}.")
            st.rerun()

frame = analytics.load_dataframe(user["id"])
summary = analytics.student_summary(user["id"], frame)
query = st.text_input("Search students", placeholder="Search by ID or name", key="student_search")
if query.strip():
    query = query.strip()
    keep = (
        summary["student_id"].str.contains(query, case=False, na=False, regex=False)
        | summary["name"].str.contains(query, case=False, na=False, regex=False)
    )
    summary = summary[keep]

st.dataframe(
    summary[["student_id", "name", "class_name", "section", "Attendance Rate", "Category"]],
    hide_index=True,
    column_config={
        "student_id": st.column_config.TextColumn("Student ID"),
        "class_name": st.column_config.TextColumn("Class"),
        "Attendance Rate": st.column_config.NumberColumn("Attendance rate (%)", format="%.1f%%"),
    },
)

if summary.empty:
    st.info("No student records found.")
    st.stop()

student_options = {
    f"{row['student_id']} · {row['name']} · {row['class_name']} / {row['section']}": int(row["student_row"])
    for _, row in summary.iterrows()
}
selected_label = st.selectbox("Select a student to edit", list(student_options), key="selected_student")
student = database.fetch_student_row(user["id"], student_options[selected_label])

if student is not None:
    with st.expander("Edit selected student"):
        with st.form(f"edit_student_{student['id']}"):
            edit_id = st.text_input("Student ID", value=student["student_id"])
            edit_name = st.text_input("Student name", value=student["name"])
            edit_class = st.text_input("Class", value=student["class_name"])
            edit_section = st.text_input("Section", value=student["section"])
            edit_submitted = st.form_submit_button("Save changes", type="primary")
        if edit_submitted:
            edit_id, edit_name = edit_id.strip(), edit_name.strip()
            edit_class, edit_section = edit_class.strip(), edit_section.strip()
            if not all((edit_id, edit_name, edit_class, edit_section)):
                st.error("All student fields are required.")
            elif any(character.isdigit() for character in edit_name):
                st.error("Student name cannot contain numbers.")
            elif database.student_id_exists(user["id"], edit_id, exclude_row=student["id"]):
                st.error("Another student already uses that ID.")
            elif not database.update_student(
                student["id"], user["id"], edit_id, edit_name, edit_class, edit_section
            ):
                st.error("The student could not be updated.")
            else:
                st.success("Student details updated.")
                st.rerun()

    with st.expander("Remove selected student"):
        confirmed = st.checkbox(
            "I understand this also deletes the student's attendance records.",
            key=f"delete_confirm_{student['id']}",
        )
        if st.button("Delete student", type="secondary", key=f"delete_student_{student['id']}"):
            if not confirmed:
                st.warning("Confirm deletion before continuing.")
            else:
                database.delete_student(student["id"], user["id"])
                st.success("Student and attendance records deleted.")
                st.rerun()
