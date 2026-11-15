import re

import streamlit as st

import database
from passwords import hash_password, verify_password
from web_utils import current_user

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

user = current_user()
st.title("My profile")

with st.container(border=True):
    st.subheader("Personal details")
    with st.form("profile_details"):
        name = st.text_input("Full name", value=user["name"])
        email = st.text_input("Email address", value=user["email"])
        phone = st.text_input("Phone number", value=user.get("phone") or "")
        department = st.text_input("Department", value=user.get("department") or "")
        class_label = st.text_input("Class / section", value=user.get("class_label") or "")
        save_profile = st.form_submit_button("Save profile", type="primary")

    if save_profile:
        name, email = name.strip(), email.strip().lower()
        phone, department, class_label = phone.strip(), department.strip(), class_label.strip()
        if not name or any(character.isdigit() for character in name):
            st.error("Enter a full name without numbers.")
        elif not EMAIL_PATTERN.fullmatch(email):
            st.error("Enter a valid email address.")
        elif phone and not phone.replace("+", "").replace(" ", "").replace("-", "").isdigit():
            st.error("Phone number may contain digits, spaces, +, and - only.")
        elif database.email_taken(email, exclude_user_id=user["id"]):
            st.error("That email address is already in use.")
        else:
            database.update_user_profile(
                user["id"], name, email, phone, department, class_label
            )
            st.success("Profile updated.")
            st.rerun()

with st.container(border=True):
    st.subheader("Change password")
    with st.form("change_password"):
        current_password = st.text_input("Current password", type="password")
        new_password = st.text_input("New password", type="password")
        confirm_password = st.text_input("Confirm new password", type="password")
        change_password = st.form_submit_button("Update password", type="primary")

    if change_password:
        latest_user = database.find_user_by_id(user["id"])
        error = None
        if not current_password:
            error = "Enter your current password."
        elif latest_user is None or not verify_password(
            current_password, latest_user["password_hash"]
        ):
            error = "Your current password is incorrect."
        elif len(new_password) < 6 or not any(c.isupper() for c in new_password) \
                or not any(c.islower() for c in new_password) or not any(c.isdigit() for c in new_password):
            error = "Use at least 6 characters, including uppercase, lowercase, and a number."
        elif new_password == current_password:
            error = "Choose a password different from your current one."
        elif new_password != confirm_password:
            error = "The new passwords do not match."

        if error:
            st.error(error)
        else:
            database.update_user_password(user["id"], hash_password(new_password))
            st.success("Password updated.")
