# Exam Conflict Checker (Version 2)

This Streamlit app detects **exam schedule conflicts** for students based on class enrollment data and a master exam schedule.

## 📁 Input Files

### 1. Class List Files (CSV format)
Upload **one or more CSV files**, each representing a course’s class list.  The file's name should be the course code. <br>
**Example**: **CSAI 230.csv** or **CSAI_230.csv**. <br>Make sure you leave a space or add an underscore between the code and number. 


#### Expected Columns:
- `ID`: Unique student identifier (e.g., university ID)
- `Status`: Only rows with `"Add"` in this column will be considered enrolled

#### File Naming:
The **course code** is extracted from the filename. For example, a file named `CSAI 385.csv` will be interpreted as course `CSAI 385`.

### Example:
```csv
ID,Status
12345678,Add
23456789,Add
34567890,Drop
```

## 2. Exam Schedule File (Excel format)

This is a single Excel file containing the complete exam schedule.

### 🗂 Sheet Structure

- Data must start on the **second row** (i.e., first row is assumed to be a header/label row).
- The column names must include the following (but there may be other fields):

| Column Name         | Description                                 |
|---------------------|---------------------------------------------|
| Course ID           | Course identifier (e.g., CSAI385)           |
| Preferred Date      | Date of the exam (DD/MM/YYYY)               |
| Preferred Time      | Time range (e.g., "9:30 AM - 11:30 AM")     |
| Duration by Hour    | Duration in hours (e.g., 2)                 |




### 🧾 Example

![image](https://github.com/user-attachments/assets/3748779e-b2ac-46cd-8b10-f2d5844c6f22)


> ⚠️ **Note:** The program automatically parses the start time from the `Preferred Time` column and calculates the end time using `Duration by Hour` (not the end time).

---

## 🧠 Functionality

- Load student-course mappings from uploaded class list CSVs
- Parse exam schedule from the Excel file
- Compute exam start and end datetimes
- Detect overlapping exam slots for students enrolled in multiple courses

---

## ✅ Output

A table of **conflicts** with:

- Student ID  
- Conflicting courses  
- Date and time details  
- Option to download results as an Excel file
