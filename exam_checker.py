import streamlit as st
import pandas as pd
import io

def load_classlists(uploaded_files):
    """Load and merge multiple classlist CSV files."""
    student_courses = {}
    for file in uploaded_files:
        df = pd.read_csv(file)
        df = df[df['Status'] == 'Add']  # Filter only added students
        course = file.name.split('.')[0].upper()  # Course name from filename
        for _, row in df.iterrows():
            student_id = row['ID']
            if student_id not in student_courses:
                student_courses[student_id] = []
            student_courses[student_id].append(course)
    return student_courses

def load_schedule(file):
    """Load the exam schedule from an Excel file."""
    xls = pd.ExcelFile(file)
    df = pd.read_excel(xls, sheet_name=xls.sheet_names[0], skiprows=2)  # Skip first two rows
    df.columns = ['Course ID', 'Course Name', 'Grouping Key', 'Students Count', 'Duration',
                  'Needed Room Type', 'Instructor', 'Preferred Date', 'Preferred Time', 'Room Assigned']
    df = df.dropna(subset=['Course ID', 'Preferred Date', 'Preferred Time'])  # Remove empty rows
    return df

def detect_conflicts(student_courses, schedule):
    """Detect scheduling conflicts for students."""
    student_conflicts = {}
    exam_schedule = {}
    
    for _, row in schedule.iterrows():
        course = row['Course ID'].strip().upper()
        course = course.replace(" ", "")
        date_time = f"{row['Preferred Date']} {row['Preferred Time']}"
        if course not in exam_schedule:
            exam_schedule[course] = date_time
    
    print(exam_schedule)

    for student, courses in student_courses.items():
        exams = {course: exam_schedule[course] for course in courses if course in exam_schedule}
        if len(set(exams.values())) < len(exams):  # Check for duplicate date/time slots
            student_conflicts[student] = exams
    
    return student_conflicts

def main():
    st.title("Exam Schedule Conflict Checker")
    
    classlist_files = st.file_uploader("Upload Classlists (CSV)", accept_multiple_files=True, type=['csv'])
    schedule_file = st.file_uploader("Upload Exam Schedule (Excel)", type=['xlsx'])
    
    if classlist_files and schedule_file:
        student_courses = load_classlists(classlist_files)
        schedule_df = load_schedule(schedule_file)
        conflicts = detect_conflicts(student_courses, schedule_df)
        
        if conflicts:
            st.error("Conflicts detected! Listing affected students...")
            conflict_df = pd.DataFrame([{**{'Student ID': str(sid)}, **courses} for sid, courses in conflicts.items()])
            st.dataframe(conflict_df)
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                conflict_df.to_excel(writer, sheet_name='Conflicts', index=False)
                writer.close()
            st.download_button("Download Conflict Report", buffer.getvalue(), "conflicts.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.success("No scheduling conflicts detected!")

if __name__ == "__main__":
    main()
