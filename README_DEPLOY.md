# Engineering Student Performance Analyzer — Version 2.0

A Python-based student analytics project with a Streamlit dashboard. It supports **one or more subject columns**; you do not need to provide Maths, Physics, and Python all together.

## Required and optional columns

Required:
- `Name`
- `RollNo`
- At least **one subject marks column**, with values from 0 to 100. Subject column names can be customized, e.g. `Chemistry`, `Biology`, `English`.

Optional:
- `Assignment` (0–100)
- `Attendance` (0–100)

Example minimal one-subject CSV:

```csv
Name,RollNo,Chemistry
Aarav Sharma,101,86
Diya Verma,102,74
Kabir Singh,103,42
```

## Calculation rules

- `SubjectAverage` = mean of the subject columns present in the file.
- `Average` = mean of `SubjectAverage` and `Assignment` when Assignment is provided; otherwise it equals `SubjectAverage`.
- Default bands: Excellent ≥ 80, Good ≥ 60, Average ≥ 40, otherwise Needs Improvement.
- Support flag: Average below 40% OR Attendance below 75%, if Attendance is supplied.
- The dashboard lets users adjust the thresholds.

With the original Maths, Physics, Python, Assignment columns, this retains the original formula: mean of the three-subject average and assignment mark. If only one subject is provided, that subject is analyzed without requiring the other subjects.

## Run locally on macOS

```bash
cd Engineering_Student_Performance_Analyzer_V2
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Browser address: `http://localhost:8501`

To run the terminal version:

```bash
python student_performance_analyzer.py
```

## Tests

```bash
python -m pytest -q
```

## Publish on Streamlit Community Cloud

1. Create a GitHub repository named `student-performance-analyzer`.
2. Upload `app.py`, `student_performance_analyzer.py`, `students.csv`, `requirements.txt`, `README.md` (this file), and `tests/`.
3. In Streamlit Community Cloud, choose **Create app**, select your repository, branch `main`, and main file path `app.py`.
4. Deploy. The app uses the sample file if no upload is provided.

Do not commit private student data to a public repository. Use synthetic/demo data in public deployments.

## Project limitations

- This is an academic support tool, not a validated predictive model.
- Flags are rule-based and should be reviewed by a teacher.
- Records uploaded through the dashboard are analyzed for the current session; this version does not provide a database or long-term storage.
