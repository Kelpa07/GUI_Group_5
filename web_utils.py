"""Shared helpers for the Streamlit interface."""

import streamlit as st

import analytics
import database


def current_user():
    """Load the signed-in user from the database, not from editable UI state."""
    user_id = st.session_state.get("user_id")
    if user_id is None:
        st.error("Your session has expired. Please sign in again.")
        st.stop()
    user = database.find_user_by_id(user_id)
    if user is None:
        st.session_state.pop("user_id", None)
        st.error("Your account could not be found. Please sign in again.")
        st.stop()
    return user


def student_summary(owner_id, frame, class_name="", section=""):
    """Build rates for the current filters while retaining no-data students."""
    summary = analytics.student_summary(owner_id, frame)
    if class_name:
        summary = summary[summary["class_name"] == class_name]
    if section:
        summary = summary[summary["section"] == section]
    return summary.reset_index(drop=True)


def class_section_filters(owner_id, key_prefix):
    """Render class and section filters and return their database values."""
    classes = ["All classes"] + database.fetch_classes(owner_id)
    selected_class = st.selectbox(
        "Class",
        classes,
        key=f"{key_prefix}_class",
    )
    class_name = "" if selected_class == "All classes" else selected_class

    sections = ["All sections"] + database.fetch_sections(owner_id, class_name)
    selected_section = st.selectbox(
        "Section",
        sections,
        key=f"{key_prefix}_section",
    )
    section = "" if selected_section == "All sections" else selected_section
    return class_name, section
