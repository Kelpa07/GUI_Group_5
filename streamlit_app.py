"""Browser entry point for AttendTrack."""

import streamlit as st

import database

st.set_page_config(
    page_title="AttendTrack",
    page_icon="🎓",
    layout="wide",
)

database.init_database()
st.session_state.setdefault("user_id", None)

if st.session_state.get("user_id") is None:
    pages = [
        st.Page(
            "app_pages/authentication.py",
            title="Sign in",
            icon=":material/lock:",
            url_path="sign-in",
        )
    ]
    page = st.navigation(pages, position="hidden")
else:
    user = database.find_user_by_id(st.session_state.user_id)
    if user is None:
        st.session_state.pop("user_id", None)
        st.rerun()

    with st.sidebar:
        st.title("AttendTrack", anchor=False)
        st.caption(f"{user['name']} · {user['email']}")
        if st.button("Sign out", icon=":material/logout:", width="stretch"):
            st.session_state.pop("user_id", None)
            st.rerun()

    pages = [
        st.Page("app_pages/dashboard.py", title="Dashboard", icon=":material/dashboard:"),
        st.Page("app_pages/attendance.py", title="Attendance", icon=":material/checklist:"),
        st.Page("app_pages/students.py", title="Students", icon=":material/groups:"),
        st.Page("app_pages/reports.py", title="Reports", icon=":material/analytics:"),
        st.Page("app_pages/profile.py", title="My profile", icon=":material/account_circle:"),
        st.Page("app_pages/settings.py", title="Settings", icon=":material/settings:"),
    ]
    page = st.navigation(pages, position="top")

page.run()
