# --- START OF FILE streamlitapp.py ---

# --- START OF FILE streamlitapp.py ---
import streamlit as st
import requests
from jose import jwt
import models
import pandas as pd
import plotly.express as px
from datetime import date
import os # Import os

# --- Use Streamlit Secrets ---
# API_URL = "http://localhost:8000" # OLD - Local only
API_URL = st.secrets.get("API_URL", "http://localhost:8000") # Use secret, fallback for local dev
SECRET_KEY = st.secrets.get("SECRET_KEY", "your_secret_key_here") # Use secret, fallback for local dev

# --- REST OF YOUR STREAMLITAPP.PY CODE ---
# ... (all your dashboard functions etc.) ...

# --- In the login logic, ensure SECRET_KEY is used from the variable above ---
# payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"]) # Ensure this uses the variable

# --- END OF FILE streamlitapp.py ---
# --- Dashboard Functions ---

def show_admin_dashboard():
    # (Keep existing admin dashboard function as is)
    st.title("Admin Dashboard")
    st.write("Welcome, Admin!")

    menu = ["View All Students", "Add New Student", "Delete Student"]
    choice = st.selectbox("Choose Action", menu)

    if choice == "View All Students":
        try:
            students = models.get_all_students()
            if students:
                df_students = pd.DataFrame(students).set_index('id')
                st.dataframe(df_students)
            else:
                st.warning("No students found in the database.")
        except Exception as e:
            st.error(f"Error fetching students: {e}")
            st.info("Ensure the database 'students.db' exists and the 'students' table is created.")

    elif choice == "Add New Student":
        with st.form("Add Student"):
            name = st.text_input("Student Name")
            email = st.text_input("Email")
            course = st.text_input("Course")
            submit = st.form_submit_button("Add")
            if submit:
                if name and email and course:
                    success = models.add_student(name, email, course)
                    if success:
                        st.success("Student added successfully!")
                        st.rerun() # Refresh view
                    else:
                        st.error(f"Failed to add student. Check if email '{email}' already exists or view logs.")
                else:
                    st.warning("Please fill out all fields.")

    elif choice == "Delete Student":
        try:
            students = models.get_all_students()
            if students:
                student_options = {f"{s['name']} (ID: {s['id']})": s['id'] for s in students}
                if not student_options:
                     st.warning("No students available to delete.")
                else:
                    selected_display_name = st.selectbox("Select student to delete", list(student_options.keys()))
                    if st.button("Delete", key="delete_student_confirm"):
                         st.warning(f"Are you sure you want to delete {selected_display_name}? This action cannot be undone and will remove associated grades and attendance.", icon="⚠️")
                         if st.button("Confirm Deletion", key="delete_student_final"):
                            student_id_to_delete = student_options[selected_display_name]
                            deleted = models.delete_student(student_id_to_delete)
                            if deleted:
                                st.success(f"'{selected_display_name}' deleted successfully.")
                                st.rerun() # Refresh view
                            else:
                                 st.error(f"Error deleting student {selected_display_name}. Check logs.")

            else:
                st.warning("No students found in the database.")
        except Exception as e:
            st.error(f"Error fetching students for deletion: {e}")


# --- Teacher Dashboard ---
def show_teacher_dashboard():
    """Displays the teacher dashboard for managing students."""
    st.title("🧑‍🏫 Teacher Dashboard")
    st.write("Welcome, Teacher!")

    teacher_menu = ["View Student Profiles", "Manage Grades", "Manage Attendance"]
    choice = st.sidebar.radio("Teacher Actions", teacher_menu)
    st.sidebar.divider()

    # --- Get list of all students for selection ---
    try:
        all_students = models.get_all_students()
        if not all_students:
            st.warning("No students found in the system.")
            return
        student_options = {s['name']: s['id'] for s in all_students}
        student_names = list(student_options.keys())
    except Exception as e:
        st.error(f"Error fetching student list: {e}")
        return

    # --- View Student Profiles ---
    if choice == "View Student Profiles":
        st.header("View Student Profiles")
        selected_name = st.selectbox("Select Student", student_names)
        if selected_name:
            student_id = student_options[selected_name]
            student_details = models.get_student_details_by_id(student_id)

            if student_details:
                st.subheader(f"Profile: {student_details['name']}")
                st.write(f"**ID:** {student_details['id']}")
                st.write(f"**Email:** {student_details['email']}")
                st.write(f"**Course:** {student_details['course']}")
                st.divider()

                # Display Grades (reuse student dashboard logic if complex charts needed)
                st.subheader("Grades")
                df_grades = models.get_grades_by_student_id(student_id)
                if not df_grades.empty:
                    st.dataframe(df_grades[['subject', 'grade', 'date_graded']].style.format({"grade": "{:.1f}%", "date_graded": "{:%Y-%m-%d}"}))
                else:
                    st.info("No grades recorded for this student.")

                # Display Attendance
                st.subheader("Attendance")
                df_attendance = models.get_attendance_by_student_id(student_id)
                if not df_attendance.empty:
                    st.dataframe(df_attendance[['date', 'subject', 'status']].style.format({"date": "{:%Y-%m-%d}"}))
                else:
                    st.info("No attendance records found for this student.")
            else:
                st.error("Could not retrieve details for the selected student.")

    # --- Manage Grades ---
    elif choice == "Manage Grades":
        st.header("Manage Student Grades")
        selected_name_grade = st.selectbox("Select Student for Grade Management", student_names, key="grade_student_select")

        if selected_name_grade:
            student_id = student_options[selected_name_grade]
            st.subheader(f"Grades for: {selected_name_grade}")

            # --- Add New Grade Form ---
            with st.form("Add Grade Form"):
                st.write("**Add New Grade**")
                subject = st.text_input("Subject")
                grade_value = st.number_input("Grade (0-100)", min_value=0.0, max_value=100.0, step=0.5, format="%.1f")
                grade_date = st.date_input("Date Graded", value=date.today())
                submitted_add = st.form_submit_button("Add Grade")

                if submitted_add:
                    if subject and grade_value is not None and grade_date:
                         success = models.add_grade(student_id, subject, grade_value, grade_date)
                         if success:
                             st.success(f"Grade '{grade_value}%' for '{subject}' added successfully for {selected_name_grade}.")
                             # No rerun here, let the table below refresh naturally or add explicit refresh button
                         else:
                             st.error("Failed to add grade. Check logs.")
                    else:
                         st.warning("Please fill in all fields to add a grade.")

            st.divider()

            # --- Edit Existing Grade ---
            st.write("**Edit Existing Grade**")
            df_grades = models.get_grades_by_student_id(student_id)

            if not df_grades.empty:
                 # Create a display string for the select box including grade ID
                 grade_edit_options = {
                     f"{row['date_graded'].strftime('%Y-%m-%d')} - {row['subject']} ({row['grade']:.1f}%) (ID: {row['id']})": row['id']
                     for index, row in df_grades.iterrows()
                 }
                 selected_grade_display = st.selectbox("Select Grade to Edit", list(grade_edit_options.keys()))

                 if selected_grade_display:
                      grade_id_to_edit = grade_edit_options[selected_grade_display]
                      # Find the original grade value for the form default
                      original_grade = df_grades.loc[df_grades['id'] == grade_id_to_edit, 'grade'].iloc[0]

                      with st.form("Edit Grade Form"):
                          new_grade_value = st.number_input("New Grade (0-100)", min_value=0.0, max_value=100.0, value=original_grade, step=0.5, format="%.1f", key=f"edit_grade_{grade_id_to_edit}")
                          submitted_edit = st.form_submit_button("Update Grade")

                          if submitted_edit:
                              if new_grade_value is not None:
                                   success = models.update_grade(grade_id_to_edit, new_grade_value)
                                   if success:
                                       st.success(f"Grade ID {grade_id_to_edit} updated successfully to {new_grade_value}%.")
                                       # Consider st.rerun() or a refresh button if immediate update needed
                                   else:
                                       st.error(f"Failed to update grade ID {grade_id_to_edit}. Check logs.")
            else:
                 st.info("No existing grades to edit for this student.")


    # --- Manage Attendance ---
    elif choice == "Manage Attendance":
        st.header("Manage Student Attendance")
        selected_name_att = st.selectbox("Select Student for Attendance Management", student_names, key="att_student_select")

        if selected_name_att:
            student_id = student_options[selected_name_att]
            st.subheader(f"Attendance for: {selected_name_att}")

            # --- Add New Attendance Record Form ---
            with st.form("Add Attendance Form"):
                st.write("**Add Attendance Record**")
                att_date = st.date_input("Date", value=date.today())
                att_subject = st.text_input("Subject/Class")
                att_status = st.selectbox("Status", ['Present', 'Absent', 'Late', 'Excused'])
                submitted_add_att = st.form_submit_button("Add Attendance Record")

                if submitted_add_att:
                     if att_date and att_subject and att_status:
                          success = models.add_attendance(student_id, att_date, att_subject, att_status)
                          if success:
                              st.success(f"Attendance recorded as '{att_status}' for {selected_name_att} in '{att_subject}' on {att_date.strftime('%Y-%m-%d')}.")
                          else:
                              st.error("Failed to add attendance. Record might already exist for this date/subject, or check logs.")
                     else:
                          st.warning("Please fill in all fields to add attendance.")

            st.divider()

            # --- Edit Existing Attendance ---
            st.write("**Edit Existing Attendance**")
            df_attendance = models.get_attendance_by_student_id(student_id)

            if not df_attendance.empty:
                 att_edit_options = {
                     f"{row['date'].strftime('%Y-%m-%d')} - {row['subject']} ({row['status']}) (ID: {row['id']})": row['id']
                     for index, row in df_attendance.iterrows()
                 }
                 selected_att_display = st.selectbox("Select Attendance Record to Edit", list(att_edit_options.keys()))

                 if selected_att_display:
                      att_id_to_edit = att_edit_options[selected_att_display]
                      original_status = df_attendance.loc[df_attendance['id'] == att_id_to_edit, 'status'].iloc[0]
                      status_index = ['Present', 'Absent', 'Late', 'Excused'].index(original_status)

                      with st.form("Edit Attendance Form"):
                          new_att_status = st.selectbox("New Status", ['Present', 'Absent', 'Late', 'Excused'], index=status_index, key=f"edit_att_{att_id_to_edit}")
                          submitted_edit_att = st.form_submit_button("Update Attendance")

                          if submitted_edit_att:
                              if new_att_status:
                                   success = models.update_attendance(att_id_to_edit, new_att_status)
                                   if success:
                                       st.success(f"Attendance ID {att_id_to_edit} updated successfully to '{new_att_status}'.")
                                   else:
                                       st.error(f"Failed to update attendance ID {att_id_to_edit}. Check logs.")
            else:
                 st.info("No existing attendance records to edit for this student.")


# --- Student Dashboard (Existing Function) ---
def show_student_dashboard(username: str):
    # (Keep existing student dashboard function as is)
    st.title(f"🎓 Student Dashboard")
    student_details = models.get_student_details_by_name(username)
    if not student_details:
        st.error(f"Could not find details for student '{username}'.")
        return
    student_id = student_details['id']
    st.write(f"Welcome, **{student_details['name']}**!")
    st.write(f"Course: {student_details['course']} | Email: {student_details['email']}")
    st.divider()
    try:
        df_grades = models.get_grades_by_student_id(student_id)
        df_attendance = models.get_attendance_by_student_id(student_id)
    except Exception as e:
        st.error(f"An error occurred while fetching dashboard data: {e}")
        return

    # --- Performance Analysis (Grades) ---
    st.header("📊 Performance Analysis")
    if not df_grades.empty:
        avg_grade = df_grades['grade'].mean()
        st.metric("Average Grade", f"{avg_grade:.2f}%")
        col1, col2 = st.columns(2)
        with col1:
             st.subheader("Grades per Subject")
             fig_grades_bar = px.bar(df_grades, x='subject', y='grade', color='subject', title="Grades by Subject", labels={'grade':'Grade (%)'})
             fig_grades_bar.update_layout(xaxis_title="Subject", yaxis_title="Grade (%)")
             st.plotly_chart(fig_grades_bar, use_container_width=True)
        with col2:
            st.subheader("Grade Trend Over Time")
            df_grades_sorted = df_grades.sort_values('date_graded')
            fig_grades_trend = px.line(df_grades_sorted, x='date_graded', y='grade', markers=True, title="Grade Trend", labels={'date_graded':'Date', 'grade':'Grade (%)'})
            fig_grades_trend.update_layout(xaxis_title="Date Graded", yaxis_title="Grade (%)")
            st.plotly_chart(fig_grades_trend, use_container_width=True)
        with st.expander("View All Grades Details"):
             # Display ID as well now
             st.dataframe(df_grades[['id', 'subject', 'grade', 'date_graded']].style.format({"grade": "{:.1f}%", "date_graded": "{:%Y-%m-%d}"}))
    else:
        st.info("No grade information available yet.")
    st.divider()

    # --- Attendance Management ---
    st.header("🗓️ Attendance")
    if not df_attendance.empty:
        total_records = len(df_attendance)
        present_count = len(df_attendance[df_attendance['status'] == 'Present'])
        late_count = len(df_attendance[df_attendance['status'] == 'Late'])
        attendance_perc = ((present_count + late_count) / total_records) * 100 if total_records > 0 else 0
        st.metric("Overall Attendance", f"{attendance_perc:.1f}%")
        col3, col4 = st.columns(2)
        with col3:
            st.subheader("Attendance Status Distribution")
            status_counts = df_attendance['status'].value_counts().reset_index()
            status_counts.columns = ['status', 'count']
            fig_attendance_pie = px.pie(status_counts, values='count', names='status', title="Attendance Breakdown", hole=0.3)
            fig_attendance_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_attendance_pie, use_container_width=True)
        with col4:
            st.subheader("Recent Attendance Records")
            # Display ID as well now
            st.dataframe(df_attendance[['id', 'date', 'subject', 'status']].head().style.format({"date": "{:%Y-%m-%d}"}))
        with st.expander("View All Attendance Records"):
             st.dataframe(df_attendance[['id', 'date', 'subject', 'status']].style.format({"date": "{:%Y-%m-%d}"}))
    else:
        st.info("No attendance information available yet.")


# --- Main App Logic (Login/Logout) ---
st.set_page_config(layout="wide")
st.sidebar.title("🎓 SIS Menu")

if "token" not in st.session_state:
    st.session_state.token = None
    st.session_state.role = None
    st.session_state.username = None

if not st.session_state.token:
    st.title("Login Required")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            # (Keep existing login API call and token handling logic)
            try:
                response = requests.post(f"{API_URL}/token", data={"username": username, "password": password})
                response.raise_for_status()
                token_data = response.json()
                token = token_data["access_token"]
                payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
                role = payload.get("role")
                user = payload.get("sub")
                if role and user:
                    st.session_state.token = token
                    st.session_state.role = role
                    st.session_state.username = user
                    st.sidebar.success(f"Logged in as {user} ({role})")
                    st.rerun()
                else:
                    st.error("Invalid token received.")
            except requests.exceptions.RequestException as e:
                 st.error(f"Connection Error: Could not connect to API at {API_URL}. ({e})")
            except requests.exceptions.HTTPError as e:
                 if e.response.status_code == 400: st.error("Invalid username or password.")
                 else: st.error(f"Login failed: {e.response.status_code} - {e.response.text}")
            except jwt.ExpiredSignatureError: st.error("Session expired. Please log in again.")
            except jwt.JWTError as e: st.error(f"Token Error: {e}")
            except Exception as e: st.error(f"Login error: {e}")

if st.session_state.token:
    st.sidebar.write(f"User: **{st.session_state.username}**")
    st.sidebar.write(f"Role: **{st.session_state.role}**")
    if st.sidebar.button("Logout"):
        st.session_state.token = None
        st.session_state.role = None
        st.session_state.username = None
        st.rerun()
    st.sidebar.divider()

    # --- Role-Based Routing ---
    if st.session_state.role == "admin":
        show_admin_dashboard()
    elif st.session_state.role == "teacher":
        # Call the new teacher dashboard function
        show_teacher_dashboard()
    elif st.session_state.role == "student":
        show_student_dashboard(st.session_state.username)
    else:
        st.error("Unknown user role.")

# --- END OF FILE streamlitapp.py ---