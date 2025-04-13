# --- START OF FILE create_db.py ---

import sqlite3
import os
from datetime import date, timedelta

DB_NAME = "students.db"

def setup_database():
    """Creates/updates the database with students, grades, and attendance."""

    print(f"--- Database Setup Script for {DB_NAME} ---")
    conn = None
    student_user_id = None # To store the ID of the user named 'student'

    try:
        print(f"Connecting to (or creating) database: {DB_NAME}...")
        conn = sqlite3.connect(DB_NAME)
        # Enable Foreign Key support
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        print("Connection successful. Foreign key support enabled.")

        # --- Create Students Table (if not exists) ---
        print("Ensuring 'students' table structure...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                course TEXT NOT NULL
            )
        """)

        # --- Create Grades Table (if not exists) ---
        print("Ensuring 'grades' table structure...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                grade REAL NOT NULL CHECK(grade >= 0 AND grade <= 100), -- Assuming 0-100 scale
                date_graded TEXT NOT NULL, -- Store as ISO format string YYYY-MM-DD
                FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
            )
        """)

        # --- Create Attendance Table (if not exists) ---
        print("Ensuring 'attendance' table structure...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                date TEXT NOT NULL, -- Store as ISO format string YYYY-MM-DD
                subject TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('Present', 'Absent', 'Late', 'Excused')),
                FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
            )
        """)
        print("All table structures ensured.")

        # --- Populate Students (if necessary) ---
        print("\nChecking and inserting base student users...")
        initial_students = [
            ('Peter Parker', 'peter.p@dailybugle.com', 'Photography'),
            ('Bruce Wayne', 'bruce.w@wayne.enterprises', 'Business Administration'),
            ('Clark Kent', 'clark.k@dailyplanet.com', 'Journalism'),
            ('Wanda Maximoff', 'wanda.m@avengers.org', 'Probability Theory'),
            ('Tony Stark', 'tony.s@starkindustries.com', 'Mechanical Engineering'),
            ('Natasha Romanoff', 'nat.r@shield.gov', 'International Relations'),
            ('student', 'student@example.com', 'General Studies') # Add the user for login
        ]
        inserted_students = 0
        for name, email, course in initial_students:
             cursor.execute("INSERT OR IGNORE INTO students (name, email, course) VALUES (?, ?, ?)", (name, email, course))
             if cursor.rowcount > 0:
                 inserted_students += 1
        print(f"Inserted {inserted_students} new students.")

        # --- Find the ID for the 'student' user ---
        print("Finding ID for user 'student'...")
        cursor.execute("SELECT id FROM students WHERE name = ?", ('student',))
        result = cursor.fetchone()
        if result:
            student_user_id = result[0]
            print(f"ID for 'student' is: {student_user_id}")
        else:
            print("WARNING: Could not find user 'student'. Sample grades/attendance might not be linked correctly.")
            # Optionally handle error or exit if 'student' must exist

        # --- Populate Grades (Sample Data for 'student' if ID found) ---
        if student_user_id:
            print(f"\nPopulating sample grades for student ID: {student_user_id}...")
            sample_grades = [
                (student_user_id, 'Mathematics', 85.5, (date.today() - timedelta(days=30)).isoformat()),
                (student_user_id, 'Physics', 78.0, (date.today() - timedelta(days=25)).isoformat()),
                (student_user_id, 'Literature', 92.0, (date.today() - timedelta(days=20)).isoformat()),
                (student_user_id, 'History', 65.0, (date.today() - timedelta(days=15)).isoformat()),
                (student_user_id, 'Mathematics', 88.0, (date.today() - timedelta(days=10)).isoformat()),
                (student_user_id, 'Physics', 82.5, (date.today() - timedelta(days=5)).isoformat()),
            ]
            # Simple check: insert only if no grades exist for this student yet
            cursor.execute("SELECT COUNT(*) FROM grades WHERE student_id = ?", (student_user_id,))
            if cursor.fetchone()[0] == 0:
                 cursor.executemany("""
                     INSERT INTO grades (student_id, subject, grade, date_graded)
                     VALUES (?, ?, ?, ?)
                 """, sample_grades)
                 print(f"Inserted {len(sample_grades)} sample grade records for 'student'.")
            else:
                 print("Sample grades for 'student' already exist, skipping insertion.")

        # --- Populate Attendance (Sample Data for 'student' if ID found) ---
        if student_user_id:
            print(f"\nPopulating sample attendance for student ID: {student_user_id}...")
            sample_attendance = [
                (student_user_id, (date.today() - timedelta(days=14)).isoformat(), 'Mathematics', 'Present'),
                (student_user_id, (date.today() - timedelta(days=13)).isoformat(), 'Physics', 'Present'),
                (student_user_id, (date.today() - timedelta(days=12)).isoformat(), 'Literature', 'Absent'),
                (student_user_id, (date.today() - timedelta(days=11)).isoformat(), 'History', 'Present'),
                (student_user_id, (date.today() - timedelta(days=10)).isoformat(), 'Mathematics', 'Present'),
                (student_user_id, (date.today() - timedelta(days=9)).isoformat(), 'Physics', 'Late'),
                (student_user_id, (date.today() - timedelta(days=8)).isoformat(), 'Literature', 'Present'),
                (student_user_id, (date.today() - timedelta(days=7)).isoformat(), 'History', 'Present'),
                (student_user_id, (date.today() - timedelta(days=6)).isoformat(), 'Mathematics', 'Excused'),
                (student_user_id, (date.today() - timedelta(days=5)).isoformat(), 'Physics', 'Present'),
                (student_user_id, (date.today() - timedelta(days=4)).isoformat(), 'Literature', 'Present'),
                (student_user_id, (date.today() - timedelta(days=3)).isoformat(), 'History', 'Absent'),
                (student_user_id, (date.today() - timedelta(days=2)).isoformat(), 'Mathematics', 'Present'),
                (student_user_id, (date.today() - timedelta(days=1)).isoformat(), 'Physics', 'Present'),
            ]
             # Simple check: insert only if no attendance exists for this student yet
            cursor.execute("SELECT COUNT(*) FROM attendance WHERE student_id = ?", (student_user_id,))
            if cursor.fetchone()[0] == 0:
                cursor.executemany("""
                    INSERT INTO attendance (student_id, date, subject, status)
                    VALUES (?, ?, ?, ?)
                """, sample_attendance)
                print(f"Inserted {len(sample_attendance)} sample attendance records for 'student'.")
            else:
                 print("Sample attendance for 'student' already exist, skipping insertion.")

        # --- Commit ---
        print("\nCommitting changes...")
        conn.commit()
        print("Changes committed successfully.")

    except sqlite3.Error as e:
        print(f"\n--- DATABASE ERROR ---")
        print(f"Error details: {e}")
        if conn:
            print("Rolling back changes due to error.")
            conn.rollback()
    except Exception as e:
        print(f"\n--- UNEXPECTED ERROR ---")
        print(f"Error details: {e}")
    finally:
        if conn:
            conn.close()
            print("\nDatabase connection closed.")
        print("--- Database Setup Script Finished ---")

if __name__ == "__main__":
    setup_database()
    print(f"\n'{DB_NAME}' should be ready with student, grades, and attendance data.")
    print("Make sure you have 'pandas' and 'plotly' installed (`pip install pandas plotly`)")
# --- END OF FILE create_db.py ---