import os
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


class StreamlitAppTests(unittest.TestCase):
    def test_account_creation_and_all_pages(self):
        project = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            database_path = str(Path(directory) / "attendtrack-test.db")
            with patch.dict(os.environ, {"ATTENDTRACK_DB_PATH": database_path}):
                app = AppTest.from_file(str(project / "streamlit_app.py")).run(timeout=20)
                self.assertFalse(app.exception)

                app.segmented_control[0].set_value("Create account").run(timeout=20)
                for key, value in {
                    "signup_name": "Test Teacher",
                    "signup_email": "teacher@example.test",
                    "signup_password": "StrongPass1",
                    "signup_confirm": "StrongPass1",
                }.items():
                    app.text_input(key=key).set_value(value)
                app.run(timeout=20)
                app.button(key="signup_submit").click().run(timeout=20)

                self.assertFalse(app.exception)
                owner_id = app.session_state["user_id"]

                import database

                student_row = database.add_student(
                    owner_id, "T001", "Test Student", "Class 1", "A"
                )
                today = date.today()
                database.save_attendance(
                    owner_id,
                    [
                        (student_row, (today - timedelta(days=1)).isoformat(), "Present"),
                        (student_row, today.isoformat(), "Late"),
                    ],
                )

                for page in (
                    "app_pages/dashboard.py",
                    "app_pages/attendance.py",
                    "app_pages/students.py",
                    "app_pages/reports.py",
                    "app_pages/profile.py",
                    "app_pages/settings.py",
                ):
                    app.switch_page(page).run(timeout=30)
                    self.assertFalse(app.exception, f"{page}: {app.exception}")


if __name__ == "__main__":
    unittest.main()
