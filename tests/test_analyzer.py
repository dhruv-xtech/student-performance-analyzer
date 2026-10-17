import pytest
from student_performance_analyzer import analyze_students, validate_and_normalize_rows

def test_single_subject_without_assignment_works():
    rows = [{"Name": "A", "RollNo": "1", "Chemistry": 86}]
    students, subjects, _, errors = validate_and_normalize_rows(rows, ["Name", "RollNo", "Chemistry"])
    result = analyze_students(students, subjects)[0]
    assert result["Average"] == 86
    assert result["Category"] == "Excellent"
    assert result["SupportNeeded"] is False

def test_one_subject_with_assignment_uses_original_formula():
    rows = [{"Name": "A", "RollNo": "1", "Maths": 80, "Assignment": 60, "Attendance": 90}]
    students, subjects, _, _ = validate_and_normalize_rows(rows, list(rows[0]))
    result = analyze_students(students, subjects)[0]
    assert result["SubjectAverage"] == 80
    assert result["Average"] == 70

def test_multiple_subjects_preserve_original_formula():
    rows = [{"Name": "A", "RollNo": "1", "Maths": 80, "Physics": 70, "Python": 90, "Assignment": 60, "Attendance": 90}]
    students, subjects, _, _ = validate_and_normalize_rows(rows, list(rows[0]))
    result = analyze_students(students, subjects)[0]
    assert result["SubjectAverage"] == 80
    assert result["Average"] == 70

def test_attendance_is_optional():
    rows = [{"Name": "A", "RollNo": "1", "Biology": 35}]
    students, subjects, _, _ = validate_and_normalize_rows(rows, list(rows[0]))
    result = analyze_students(students, subjects)[0]
    assert result["LowAttendance"] is False
    assert result["SupportNeeded"] is True

def test_marks_out_of_range_are_rejected():
    rows = [{"Name": "A", "RollNo": "1", "Maths": 120}]
    with pytest.raises(ValueError, match="No valid student rows"):
        validate_and_normalize_rows(rows, list(rows[0]))
