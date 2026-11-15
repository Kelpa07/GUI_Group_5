import re

import streamlit as st

import database
from passwords import hash_password, verify_password

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

st.title("Welcome to AttendTrack")
st.write("Record classroom attendance and keep track of student progress.")

mode = st.segmented_control(
    "Account",
    ["Log in", "Create account"],
    default="Log in",
    key="auth_mode",
)

if mode == "Create account":
    with st.form("create_account"):
        name = st.text_input("Full name", max_chars=100, key="signup_name")
        email = st.text_input("Email address", max_chars=254, key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        confirm = st.text_input("Confirm password", type="password", key="signup_confirm")
        submitted = st.form_submit_button(
            "Create account", type="primary", key="signup_submit"
        )

    if submitted:
        name = name.strip()
        email = email.strip().lower()
        error = None
        if not name or any(character.isdigit() for character in name):
            error = "Enter a full name without numbers."
        elif not EMAIL_PATTERN.fullmatch(email):
            error = "Enter a valid email address."
        elif len(password) < 6 or not any(c.isupper() for c in password) \
                or not any(c.islower() for c in password) or not any(c.isdigit() for c in password):
            error = "Use at least 6 characters, including an uppercase letter, a lowercase letter, and a number."
        elif confirm != password:
            error = "The passwords do not match."
        elif database.email_taken(email):
            error = "That email is already registered. Please log in."

        if error:
            st.error(error)
        else:
            try:
                user_id = database.add_user(name, email, hash_password(password))
            except Exception as error:
                st.error(f"Could not create your account: {error}")
            else:
                st.session_state.user_id = user_id
                st.success("Your account is ready.")
                st.rerun()
else:
    with st.form("log_in"):
        email = st.text_input("Email address", max_chars=254, key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button("Log in", type="primary", key="login_submit")

    if submitted:
        email = email.strip().lower()
        if not EMAIL_PATTERN.fullmatch(email) or not password:
            st.error("Enter a valid email address and password.")
        else:
            user = database.find_user_by_email(email)
            if user is None or not verify_password(password, user["password_hash"]):
                st.error("The email or password you entered is incorrect.")
            else:
                st.session_state.user_id = user["id"]
                st.rerun()
