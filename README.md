# AttendTrack — Student Attendance Tracker

A desktop application for recording and analysing student attendance, built with
**Python and Tkinter** for the B.Ed ICT **PRG 304 (Python GUI Programming)** group
project at Samtse College of Education.

Everything runs in one Tkinter window: sign up, dashboard, attendance marking,
student records, reports, profile and settings. Data is stored in a local
**SQLite** database, cleaned and analysed with **Pandas**, and drawn with
**Matplotlib** charts embedded inside the Tkinter widgets.

An interactive **Streamlit web interface** is also available. It shares the
SQLite database, account system, attendance calculations, and student records
with the desktop app.

---

## 1. Requirements

| Requirement | Details |
| --- | --- |
| Python | 3.10 or newer (built and tested on 3.13.7) |
| Streamlit | 1.57 or newer for the browser interface |
| Tkinter | Ships with Python. On Linux it may need `sudo apt install python3-tk` |
| pandas | Data cleaning, grouping and all attendance calculations |
| matplotlib | Trend line, bar, donut, pie and histogram charts |
| sqlite3 | Ships with Python — no database server needed |

---

## 2. Installation

```bash
pip install -r requirements.txt
```

For the desktop app, check that Tkinter is available:

```bash
python -m tkinter
```

A small Tk window should appear. If it does not, install the Tkinter package for
your operating system before continuing.

---

## 3. Running the application

### Web app

Install the requirements and start Streamlit:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Open the local URL printed by Streamlit. The browser app includes sign-up and
login, an interactive dashboard, editable attendance, student management,
filtered reports with CSV downloads, profile/password management, settings, and
optional demonstration data.

### Desktop app

```bash
python main.py
```

From the folder that contains `main.py`. On the first run the program creates
`attendance_tracker.db` in the same folder, builds all four tables and opens the
sign-up screen.

1. Choose **Sign Up**, enter your name, email, password and confirmation, then create the account.
2. You are logged straight into the **Dashboard**.
3. Open **Students** to add your class list, then **Attendance** to mark a day.
4. Press **Log Out** at the bottom of the sidebar when you finish.

Passwords are never stored as plain text (see section 6), so please remember the
one you used — there is no email reset link in this project.

---

## 4. Files in this project

| File | What it does |
| --- | --- |
| `main.py` | Creates the one Tkinter window, the sidebar shell, screen switching and the scrollable content area |
| `streamlit_app.py` | Starts the browser-based app and its authenticated page navigation |
| `app_pages/` | Interactive browser pages for authentication, dashboard, attendance, students, reports, profile and settings |
| `passwords.py` | Shared PBKDF2 password hashing and verification used by both interfaces |
| `theme.py` | The shared teal-and-white look: colours, fonts, cards, buttons, form fields, toggle switch |
| `database.py` | Every SQLite operation: connection, tables, constraints and parameterised queries. No GUI code here |
| `auth.py` | Sign-up and login screen, field validation, PBKDF2 password hashing and verification |
| `analytics.py` | All Pandas work: cleaning, attendance rates, categories, grouping by day/weekday/class/section, descriptive statistics |
| `charts.py` | Matplotlib figures returned as `FigureCanvasTkAgg` canvases |
| `dashboard.py` | Dashboard screen: five summary cards, two charts, three category lists |
| `attendance.py` | Mark Attendance screen: class/section/date picker and one Present/Absent/Late/Excused control per student |
| `students.py` | Students screen: search, `ttk.Treeview` table, pagination, add/edit dialog, delete with confirmation |
| `reports.py` | Reports screen: filters, four charts, statistics card, summary cards, rate table and CSV export |
| `profile.py` | My Profile screen: account details, profile editing and secure password change |
| `settings.py` | Settings screen: institution, academic year, late threshold, minimum percentage, Saturdays, demo data |
| `sample_data.py` | Optional realistic demonstration data, loaded only when you press the button |
| `requirements.txt` | Python packages for the web app, analytics and charts |
| `attendance_tracker.db` | Created automatically on first run |

---

## 5. The attendance rule used everywhere

```
Attendance Rate = (Present Days / Eligible Recorded Days) × 100

Eligible Recorded Days = Present + Absent + Late
```

* **Late** counts as an eligible day but not as present.
* **Excused** days are removed from the denominator completely.
* A student with no eligible recorded days gets no percentage — they are shown as
  *No Data* and left out of averages rather than counted as zero.
* The overall rate for a class, section or date range uses exactly the same rule.

Students are then grouped as **Excellent (90% and above)**, **Good (75–89%)** and
**Needs Improvement (below 75%)**.

Every number on the Dashboard and Reports screens is calculated from the live
SQLite records each time the screen opens. Nothing is typed into the interface by
hand.

---

## 6. Database and security

Four tables are created automatically with primary keys, foreign keys, `CHECK`
and `UNIQUE` constraints, and `ON DELETE CASCADE` so a student's records disappear
with them:

| Table | Contents |
| --- | --- |
| `users` | id, name, unique email, password hash, phone, department, class label |
| `students` | id, owner (user), student id, name, class, section — unique per owner |
| `attendance` | id, owner, student, date, status — one row per student per date |
| `settings` | key/value pairs for the application settings |

* Passwords are hashed with **PBKDF2-HMAC-SHA256**, 200,000 iterations and a
  random salt per user, stored as `salt$hash`. Verification uses a
  timing-safe comparison, and the plain password never touches the database.
* Every query uses `?` placeholders, so typed-in text cannot alter the SQL.
* Students and attendance belong to the signed-in teacher (`owner_id`), so two
  accounts on the same computer never see each other's records.

To start over, close the application and delete `attendance_tracker.db`. A fresh
database is created the next time you run it.

---

## 7. Duplicate attendance

Marking a student for a date that already exists **updates** that record instead
of adding a second one (`UNIQUE(student_row, date)` plus an upsert). When you save
over existing records the program tells you how many were updated, and asks you to
confirm first.

---

## 8. Demonstration data (optional)

For the presentation, open **Settings → Demonstration Data → Load Demo Data**.
This creates 26 students in a separate **Demo Class** with 20 school days of
attendance each (520 records) spread across all three categories.

* It is never loaded automatically and cannot load twice by accident.
* **Remove Demo Data** deletes only the Demo Class rows; your own students stay.
* To remove it permanently, delete the file and start again (section 6).

---

## 9. Exporting reports

On the Reports screen, set your **From / To** dates, **Class** and **Section**,
press **Generate Report**, then choose:

* **Export Student Rates (CSV)** — one row per student with counts, rate and category
* **Export Attendance Records (CSV)** — one row per attendance record

Both open a normal Tkinter save dialog. Files are written with a UTF-8 BOM so
Excel opens the headings correctly.

---

## 10. Troubleshooting

| Problem | Fix |
| --- | --- |
| `ModuleNotFoundError: No module named 'pandas'` | Run `pip install -r requirements.txt` in the same terminal you use to start the app |
| `ModuleNotFoundError: No module named '_tkinter'` | Install Tkinter (`sudo apt install python3-tk`, or re-run the Python installer on Windows and tick *tcl/tk*) |
| Charts do not appear | Confirm `matplotlib` installed correctly: `python -c "import matplotlib; print(matplotlib.__version__)"` |
| Window looks cramped | The layout is designed for 1280×720 and larger; maximise the window |
| Forgotten password | Delete `attendance_tracker.db` (this removes all data) and sign up again |
