import random
from datetime import date, timedelta

import database

DEMO_CLASS = "Demo Class"

NAMES = [
    "Karma Chimi Rinzin", "Tandin Wangmo", "Dorji Selden", "Tandin Zangmo",
    "Jamyang Choden", "Sangay Namling Yoezer", "Pema Gyelmo", "Jigme Tenzin",
    "Sonam Phuentcho", "Karma Dema", "Kuenga Yangchen", "Tshering Zangmo",
    "Ugyen Tshering", "Chhimi Dema", "Norbu Wangdi", "Sona Lhaden",
    "Tashi Pem", "Jampa Choden", "Kezang Wangmo", "Dawa Dem",
    "Yonten Zangmo", "Nima Gyeltshen", "Sangay Lham", "Phurba Dorji",
    "Kinley Dema", "Tshewang Lhendon",
]

# One expected attendance rate per demo student, chosen so the three
# categories are all represented: 12 Excellent, 9 Good, 5 Needs Improvement.
TARGET_RATES = [
    0.99, 0.98, 0.97, 0.96, 0.95, 0.95, 0.94, 0.93, 0.92, 0.91, 0.91, 0.90,
    0.89, 0.87, 0.86, 0.84, 0.82, 0.80, 0.78, 0.76, 0.75,
    0.71, 0.66, 0.60, 0.54, 0.48,
]

EXCUSED_CHANCE = 0.04


def school_days(count=20, end=None):
    """The most recent weekday dates, oldest first (Saturday and Sunday skipped)."""
    end = end or date.today()
    days = []
    cursor = end
    while len(days) < count:
        if cursor.weekday() < 5:
            days.append(cursor)
        cursor -= timedelta(days=1)
    return sorted(days)


def status_weights(target):
    """Turn one expected rate into weights for the four statuses."""
    late = min(0.10, round((1 - target) * 0.4, 3))
    absent = max(0.0, round(1 - target - EXCUSED_CHANCE - late, 3))
    return [target, absent, late, EXCUSED_CHANCE]


def create_demo_data(owner_id, students_per_section=13, days=20):
    """
    Insert demo students and a realistic attendance history.

    Returns (students created, attendance records created).
    """
    rng = random.Random(2026)
    dates = school_days(days)

    row_ids = []
    for index, name in enumerate(NAMES[:students_per_section * 2]):
        section = "Section A" if index < students_per_section else "Section B"
        # A 9 prefix keeps demo IDs clear of the real 0823xxxx numbers.
        student_id = "90" + str(index + 1).zfill(5)
        row_id = database.add_student(owner_id, student_id, name, DEMO_CLASS, section)
        if row_id:
            row_ids.append((row_id, index))

    entries = []
    for row_id, index in row_ids:
        target = TARGET_RATES[index % len(TARGET_RATES)]
        weights = status_weights(target)
        for day in dates:
            status = rng.choices(list(database.STATUSES), weights=weights, k=1)[0]
            entries.append((row_id, day.isoformat(), status))

    records = database.save_attendance(owner_id, entries)
    return len(row_ids), records


def count_demo_students(owner_id):
    return len(database.fetch_students(owner_id, class_name=DEMO_CLASS))


def count_demo_records(owner_id):
    conn = database.get_connection()
    try:
        row = conn.execute(
            """
            SELECT COUNT(*) AS n
              FROM attendance a
              JOIN students s ON s.id = a.student_row
             WHERE s.owner_id = ? AND s.class_name = ?
            """,
            (owner_id, DEMO_CLASS),
        ).fetchone()
        return row["n"]
    finally:
        conn.close()


def delete_demo_data(owner_id):
    """Remove the demo students and, through them, their attendance rows."""
    return database.clear_demo_data(owner_id, DEMO_CLASS)
