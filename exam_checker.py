import streamlit as st
import pandas as pd
from pathlib import Path
from io import BytesIO
import itertools
import re


def extract_hour(text):
    match = re.search(r'(\d+)', text)
    return int(match.group(1)) if match else None

def extract_start_time(in_time):
    first_time = in_time.split('-')[0].strip()

    if 'pm' in first_time.lower():
        first_time = first_time.replace('PM', '').replace('pm', '').strip()
        h = int(first_time.split(':')[0].strip()) +12
        h = str(h).zfill(2) 
        first_time = h + ':' + first_time.split(':')[1]
    else:
        parts = first_time.split(':')
        first_time = parts[0].zfill(2) + ':' + parts[1]
    first_time = first_time.replace('AM', '').replace('PM', '').strip()
    print("first time", first_time)

    return first_time

# Cached function to load and parse class list CSVs
def load_classlists(files):
    student_courses = {}
    for f in files:
        try:
            df = pd.read_csv(f)
        except Exception as e:
            st.error(f"Error reading {f.name}: {e}")
            continue
        # Validate required columns
        if 'ID' not in df.columns or 'Status' not in df.columns:
            st.error(f"File {f.name} is missing required columns 'ID' and/or 'Status'.")
            continue
        # Derive course code from filename (before first '_')
        course = Path(f.name).stem.split('_')[0].upper()
        # Keep only added students
        adds = df.loc[df['Status'] == 'Add', 'ID'].astype(str)
        for sid in adds:
            student_courses.setdefault(sid, set()).add(course)
    return student_courses

# Cached function to load exam schedule from Excel
def load_schedule(excel_file):
    try:
        sched = pd.read_excel(excel_file, header=1)
    except Exception as e:
        st.error(f"Error reading schedule file: {e}")
        return pd.DataFrame()
    # Normalize column names
    sched.columns = [str(c).strip().lower().replace(' ', '_') for c in sched.columns]
    # Validate essential columns
    
    #print(sched.columns)
    #st.write(sched.columns)
    
    required = {'course_id', 'preferred_date', 'preferred_time', 'duration_by_hour'}
    if not required.issubset(set(sched.columns)):
        st.error("Schedule file must contain 'Course ID', 'Preferred Date', 'Preferred Time', and 'Duration by Hour' columns.")
        return pd.DataFrame()
    # Normalize course IDs
    sched['course_id'] = sched['course_id'].astype(str).str.upper()
    # Parse dates and times
    print(sched['preferred_date'])
    first_time =  sched['preferred_time'].apply(lambda x: extract_start_time(x))
    
    #print("-----------")
    #print (first_time)
    #print("-----------")
    


    # combine date + that first time and parse with the right format
    sched['start_dt'] = pd.to_datetime(
        sched['preferred_date'].astype(str) + ' ' + first_time,
        errors='coerce'
    )
    
    #print("------gggg-----")
    #print (sched['start_dt'] )
    #print("------hhhh-----")

    # Ensure duration is numeric
    #hour = sched['duration_by_hour'].apply()
    hour = sched['duration_by_hour'].apply(lambda x: extract_hour(str(x)))
    sched['duration_by_hour'] = pd.to_numeric(hour, errors='coerce').fillna(0)
    # Compute end datetime
    sched['end_dt'] = sched['start_dt'] + pd.to_timedelta(sched['duration_by_hour'], unit='h')
    return sched

# Detect scheduling conflicts for each student based on overlapping intervals
def detect_conflicts(student_courses, schedule_df):
    # Build map: course_id -> (start_dt, end_dt)

    print(schedule_df)
    exam_map = {
        row['course_id']: (row['start_dt'], row['end_dt'])
        for _, row in schedule_df.iterrows()
    }
    conflicts = []
    print("exam_map", exam_map)
    for sid, courses in student_courses.items():
        # Gather this student's exam slots
        slots = {c: exam_map[c] for c in courses if c in exam_map}
        # Compare each pair for overlap
        for c1, c2 in itertools.combinations(slots.keys(), 2):
            start1, end1 = slots[c1]
            start2, end2 = slots[c2]
            # Check for overlap
            if start1 < end2 and start2 < end1:
                conflicts.append({
                    'Student ID': sid,
                    'Date': start1.date(),
                    'Course 1': c1,
                    'Start 1': start1.time(),
                    'End 1': end1.time(),
                    'Course 2': c2,
                    'Start 2': start2.time(),
                    'End 2': end2.time()
                })
    return pd.DataFrame(conflicts)

# Main Streamlit app
def main():
    st.title("Exam Conflict Checker - Version 2")
    st.write("Upload class list CSVs and an exam schedule Excel to detect student exam conflicts, including overlapping times.")

    # Upload inputs
    class_files = st.file_uploader("Upload Class List CSVs", type="csv", accept_multiple_files=True)
    schedule_file = st.file_uploader("Upload Exam Schedule Excel", type=["xlsx", "xls"])

    if class_files and schedule_file:
        # Load data
        student_courses = load_classlists(class_files)
        if not student_courses:
            st.warning("No valid class list data found.")
            return

        schedule_df = load_schedule(schedule_file)
        if schedule_df.empty:
            st.warning("No valid schedule data found.")
            return

        # Detect and display conflicts
        conf_df = detect_conflicts(student_courses, schedule_df)
        if conf_df.empty:
            st.success("No conflicts detected! 🎉")
        else:
            st.subheader("Conflicts Found")
            st.dataframe(conf_df)

            # Provide download as Excel
            towrite = BytesIO()
            with pd.ExcelWriter(towrite, engine='xlsxwriter') as writer:
                conf_df.to_excel(writer, index=False, sheet_name='Conflicts')
            towrite.seek(0)
            st.download_button(
                label="Download Conflict Report as Excel",
                data=towrite.getvalue(),
                file_name="exam_conflicts.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# Entry point
if __name__ == "__main__":
    main()
