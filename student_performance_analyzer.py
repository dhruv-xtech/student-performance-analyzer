"""Core logic for Engineering Student Performance Analyzer.

Backward-compatible default formula:
- SubjectAverage = mean of all supplied subject columns.
- Overall Average = mean(SubjectAverage, Assignment) when Assignment exists;
  otherwise Overall Average = SubjectAverage.
- Categories default to Excellent >= 80, Good >= 60, Average >= 40,
  otherwise Needs Improvement.
- Support flag = Attendance below 75% OR overall average below 40%.
At least one subject-mark column is required; other subjects are optional.
"""
import csv
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

IDENTITY_COLUMNS = ("Name", "RollNo")
OPTIONAL_COLUMNS = ("Assignment", "Attendance")
DEFAULT_SUBJECTS = ("Maths", "Physics", "Python")
NON_SUBJECT_COLUMNS = set(IDENTITY_COLUMNS) | set(OPTIONAL_COLUMNS) | {
    "SubjectAverage", "Average", "Category", "LowAttendance", "SupportNeeded"
}
LOW_ATTENDANCE_LIMIT = 75
REPORT_FILE = "analysis_report.csv"


def detect_subject_columns(columns):
    """Return numeric mark columns other than known metadata/optional columns."""
    return [c for c in columns if c not in NON_SUBJECT_COLUMNS]


def validate_and_normalize_rows(rows, columns=None):
    """Validate rows with Name, RollNo, and at least one subject mark column."""
    if not rows:
        raise ValueError("No student records found.")
    columns = list(columns or rows[0].keys())
    missing = [c for c in IDENTITY_COLUMNS if c not in columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))
    subjects = detect_subject_columns(columns)
    if not subjects:
        raise ValueError("Add at least one subject column with marks from 0 to 100.")
    numeric_columns = subjects + [c for c in OPTIONAL_COLUMNS if c in columns]
    clean, errors = [], []
    for index, row in enumerate(rows, start=2):
        try:
            item = {"Name": str(row.get("Name", "")).strip(),
                    "RollNo": str(row.get("RollNo", "")).strip()}
            if not item["Name"] or item["Name"].lower() == "nan":
                raise ValueError("Name cannot be empty.")
            if not item["RollNo"] or item["RollNo"].lower() == "nan":
                raise ValueError("RollNo cannot be empty.")
            for col in numeric_columns:
                raw = row.get(col, "")
                if raw is None or str(raw).strip() == "":
                    if col in subjects:
                        raise ValueError(f"{col} mark is required for this row.")
                    continue
                value = float(raw)
                if not 0 <= value <= 100:
                    raise ValueError(f"{col} must be between 0 and 100.")
                item[col] = value
            clean.append(item)
        except (ValueError, TypeError) as exc:
            errors.append(f"Row {index}: {exc}")
    if not clean:
        raise ValueError("No valid student rows. " + "; ".join(errors[:5]))
    return clean, subjects, numeric_columns, errors


def load_students(filename="students.csv", strict=False):
    with open(filename, "r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            raise ValueError("CSV file has no header row.")
        rows = list(reader)
        students, subjects, numeric_columns, errors = validate_and_normalize_rows(rows, reader.fieldnames)
    if strict and errors:
        raise ValueError("Invalid CSV data:\n" + "\n".join(errors))
    return students, errors


def analyze_students(students, subject_columns=None, low_attendance_limit=LOW_ATTENDANCE_LIMIT,
                     support_average_limit=40, excellent_limit=80, good_limit=60,
                     average_limit=40):
    if not students:
        return []
    if not (0 <= average_limit <= good_limit <= excellent_limit <= 100):
        raise ValueError("Grade thresholds must satisfy 0 <= Average <= Good <= Excellent <= 100.")
    if subject_columns is None:
        subject_columns = [c for c in students[0].keys() if c not in NON_SUBJECT_COLUMNS]
    if not subject_columns:
        raise ValueError("At least one subject column is required.")
    results = []
    for student in students:
        available = [float(student[c]) for c in subject_columns if c in student and student[c] is not None]
        if not available:
            continue
        subject_average = float(np.mean(available))
        # Preserve the original formula when Assignment is present.
        if "Assignment" in student and student["Assignment"] is not None:
            overall_average = float(np.mean([subject_average, float(student["Assignment"])]))
        else:
            overall_average = subject_average
        if overall_average >= excellent_limit:
            category = "Excellent"
        elif overall_average >= good_limit:
            category = "Good"
        elif overall_average >= average_limit:
            category = "Average"
        else:
            category = "Needs Improvement"
        attendance = student.get("Attendance")
        low_attendance = attendance is not None and float(attendance) < low_attendance_limit
        result = dict(student)
        result["SubjectAverage"] = round(subject_average, 2)
        result["Average"] = round(overall_average, 2)
        result["Category"] = category
        result["LowAttendance"] = bool(low_attendance)
        result["SupportNeeded"] = bool(low_attendance or overall_average < support_average_limit)
        results.append(result)
    return results


def save_report(results, filename=REPORT_FILE):
    if not results:
        raise ValueError("No results to save.")
    fields = list(results[0].keys())
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)
    return filename


def create_graphs(results, output_dir="."):
    if not results:
        raise ValueError("No results available for graphs.")
    os.makedirs(output_dir, exist_ok=True)
    names = [r["RollNo"] for r in results]
    averages = [r["Average"] for r in results]
    paths = [os.path.join(output_dir, "student_averages.png")]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(names, averages)
    ax.set(title="Overall Academic Average by Student", xlabel="Roll number",
           ylabel="Average (%)", ylim=(0, 100))
    fig.tight_layout()
    fig.savefig(paths[0], dpi=150)
    plt.close(fig)
    if any(r.get("Attendance") is not None for r in results):
        attendance_rows = [r for r in results if r.get("Attendance") is not None]
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar([r["RollNo"] for r in attendance_rows], [r["Attendance"] for r in attendance_rows])
        ax.axhline(LOW_ATTENDANCE_LIMIT, linestyle="--", label=f"Default threshold ({LOW_ATTENDANCE_LIMIT}%)")
        ax.set(title="Attendance by Student", xlabel="Roll number", ylabel="Attendance (%)", ylim=(0, 100))
        ax.legend()
        fig.tight_layout()
        paths.append(os.path.join(output_dir, "student_attendance.png"))
        fig.savefig(paths[-1], dpi=150)
        plt.close(fig)
    return paths


def main():
    print("ENGINEERING STUDENT PERFORMANCE ANALYZER")
    try:
        students, errors = load_students()
    except (OSError, ValueError) as exc:
        print(f"Unable to load data: {exc}")
        return
    for error in errors:
        print("Warning:", error)
    columns = list(students[0].keys())
    subjects = detect_subject_columns(columns)
    results = analyze_students(students, subjects)
    print(f"Students: {len(results)} | Subjects detected: {', '.join(subjects)}")
    print(f"Class average: {np.mean([r['Average'] for r in results]):.2f}%")
    while True:
        print("\\n1. Save analysis CSV\\n2. Generate graphs\\n3. Show students needing support\\n4. Exit")
        choice = input("Choose 1-4: ").strip()
        if choice == "1":
            print("Saved:", save_report(results))
        elif choice == "2":
            print("Saved graphs:", ", ".join(create_graphs(results)))
        elif choice == "3":
            flagged = [r for r in results if r["SupportNeeded"]]
            if not flagged:
                print("No students flagged by current rules.")
            for r in flagged:
                print(f"{r['RollNo']} {r['Name']}: average {r['Average']}%")
        elif choice == "4":
            break
        else:
            print("Enter 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()
