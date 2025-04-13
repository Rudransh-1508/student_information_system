# --- START OF FILE models.py ---

from pydantic import BaseModel
from typing import Optional, List, Dict
import sqlite3
import pandas as pd
from datetime import date

# --- Pydantic Models (keep as is) ---
class User(BaseModel):
    username: str
    password: str
    role: str

class UserInDB(User):
    hashed_password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

# --- Database Connection ---
def connect_db():
    conn = sqlite3.connect("students.db")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# --- Student Management Functions (Admin) ---
def get_all_students() -> List[Dict]:
    """Gets basic details for all students."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, course FROM students ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_student(name, email, course):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO students (name, email, course) VALUES (?, ?, ?)", (name, email, course))
        conn.commit()
        return True # Indicate success
    except sqlite3.IntegrityError:
        print(f"Error: Student with email {email} already exists.")
        return False # Indicate failure
    except Exception as e:
        print(f"An error occurred adding student: {e}")
        conn.rollback()
        return False # Indicate failure
    finally:
        conn.close()

def delete_student(student_id):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
        conn.commit()
        return cursor.rowcount > 0 # True if a row was deleted
    except Exception as e:
        print(f"An error occurred deleting student: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# --- Student/Teacher Shared Data Functions ---

def get_student_id_by_name(name: str) -> Optional[int]:
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM students WHERE name = ?", (name,))
    result = cursor.fetchone()
    conn.close()
    return result['id'] if result else None

def get_student_details_by_id(student_id: int) -> Optional[dict]:
     """Gets basic details for a student by ID."""
     conn = connect_db()
     cursor = conn.cursor()
     cursor.execute("SELECT id, name, email, course FROM students WHERE id = ?", (student_id,))
     result = cursor.fetchone()
     conn.close()
     return dict(result) if result else None


def get_grades_by_student_id(student_id: int) -> pd.DataFrame:
    """Retrieves all grades (including ID) for a specific student ID."""
    conn = connect_db()
    try:
        # Select ID for potential updates
        query = """
            SELECT id, subject, grade, date_graded
            FROM grades
            WHERE student_id = ?
            ORDER BY date_graded DESC, subject
        """
        df = pd.read_sql_query(query, conn, params=(student_id,))
        if not df.empty:
             df['date_graded'] = pd.to_datetime(df['date_graded'])
        return df
    except Exception as e:
        print(f"Error fetching grades: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_attendance_by_student_id(student_id: int) -> pd.DataFrame:
    """Retrieves all attendance records (including ID) for a specific student ID."""
    conn = connect_db()
    try:
        # Select ID for potential updates
        query = """
            SELECT id, date, subject, status
            FROM attendance
            WHERE student_id = ?
            ORDER BY date DESC, subject
        """
        df = pd.read_sql_query(query, conn, params=(student_id,))
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception as e:
        print(f"Error fetching attendance: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# --- Teacher Specific Functions ---

def add_grade(student_id: int, subject: str, grade: float, date_graded: date) -> bool:
    """Adds a new grade record for a student."""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO grades (student_id, subject, grade, date_graded)
            VALUES (?, ?, ?, ?)
        """, (student_id, subject, grade, date_graded.isoformat()))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding grade: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def update_grade(grade_id: int, new_grade: float) -> bool:
    """Updates the grade value for a specific grade record ID."""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE grades SET grade = ? WHERE id = ?", (new_grade, grade_id))
        conn.commit()
        # Check if any row was actually updated
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating grade: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def add_attendance(student_id: int, attendance_date: date, subject: str, status: str) -> bool:
    """Adds a new attendance record for a student."""
    conn = connect_db()
    cursor = conn.cursor()
    # Optional: Check if a record for this student, date, and subject already exists
    cursor.execute("SELECT id FROM attendance WHERE student_id = ? AND date = ? AND subject = ?",
                   (student_id, attendance_date.isoformat(), subject))
    if cursor.fetchone():
        print(f"Attendance record already exists for student {student_id} on {attendance_date.isoformat()} for {subject}. Use update instead.")
        conn.close()
        return False # Indicate failure because it exists

    try:
        cursor.execute("""
            INSERT INTO attendance (student_id, date, subject, status)
            VALUES (?, ?, ?, ?)
        """, (student_id, attendance_date.isoformat(), subject, status))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding attendance: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def update_attendance(attendance_id: int, new_status: str) -> bool:
    """Updates the status for a specific attendance record ID."""
    conn = connect_db()
    cursor = conn.cursor()
    allowed_statuses = ['Present', 'Absent', 'Late', 'Excused']
    if new_status not in allowed_statuses:
        print(f"Error: Invalid attendance status '{new_status}'. Must be one of {allowed_statuses}")
        conn.close()
        return False

    try:
        cursor.execute("UPDATE attendance SET status = ? WHERE id = ?", (new_status, attendance_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating attendance: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# --- END OF FILE models.py ---