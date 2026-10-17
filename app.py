"""Streamlit interface: accepts one or more subject columns, not all subjects."""
import io
import csv
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from student_performance_analyzer import (
    IDENTITY_COLUMNS, OPTIONAL_COLUMNS, NON_SUBJECT_COLUMNS,
    validate_and_normalize_rows, analyze_students
)

st.set_page_config(page_title="Student Performance Analyzer", page_icon="📊", layout="wide")
st.markdown("""
<style>
.block-container {padding-top: 1.5rem; max-width: 1450px;}
[data-testid="stMetric"] {background: rgba(120,120,120,.08); padding: 14px; border-radius: 12px; border: 1px solid rgba(128,128,128,.18);}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("📊 SPA")
    st.caption("Engineering Student Performance Analyzer")
    st.divider()
    upload = st.file_uploader("Upload student data", type=["csv", "xlsx"])
    st.caption("Required: Name, RollNo, and at least ONE subject column. Assignment and Attendance are optional.")
    st.subheader("Analysis rules")
    attendance_limit = st.slider("Low attendance threshold (%)", 0, 100, 75)
    support_average = st.slider("Support if average below (%)", 0, 100, 40)
    with st.expander("Performance categories"):
        excellent = st.slider("Excellent from (%)", 0, 100, 80)
        good = st.slider("Good from (%)", 0, excellent, min(60, excellent))
        average = st.slider("Average from (%)", 0, good, min(40, good))

st.title("Engineering Student Performance Analyzer")
st.markdown("**Flexible academic analytics — upload data for one subject or many.**")
st.caption("Original formula retained: mean(subject average, assignment) when Assignment exists; otherwise the subject average.")
st.info("The included records are fictional sample data. Avoid uploading identifiable student records to a public demo.")

def read_input(file):
    if file is None:
        path = "students.csv"
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            return validate_and_normalize_rows(list(reader), reader.fieldnames)
    if file.name.lower().endswith(".csv"):
        decoded = file.getvalue().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(decoded))
        return validate_and_normalize_rows(list(reader), reader.fieldnames)
    frame = pd.read_excel(file)
    return validate_and_normalize_rows(frame.where(pd.notnull(frame), None).to_dict("records"), list(frame.columns))

try:
    students, subjects, numeric_columns, warnings = read_input(upload)
    results = analyze_students(students, subjects, attendance_limit, support_average, excellent, good, average)
except Exception as exc:
    st.error(f"Could not analyze this file: {exc}")
    st.stop()

if warnings:
    with st.expander(f"Rows skipped due to validation errors ({len(warnings)})"):
        for warning in warnings:
            st.warning(warning)

df = pd.DataFrame(results)
flagged = df[df["SupportNeeded"]]
class_average = float(df["Average"].mean())
has_attendance = "Attendance" in df.columns and df["Attendance"].notna().any()
avg_attendance = float(df["Attendance"].dropna().mean()) if has_attendance else None
best = df.loc[df["Average"].idxmax()]
worst = df.loc[df["Average"].idxmin()]

metrics = st.columns(5)
metrics[0].metric("Students analyzed", len(df))
metrics[1].metric("Subjects detected", len(subjects))
metrics[2].metric("Class average", f"{class_average:.1f}%")
metrics[3].metric("Need support", len(flagged))
metrics[4].metric("Avg. attendance", f"{avg_attendance:.1f}%" if avg_attendance is not None else "Not provided")

overview, records, subjects_tab, support, export = st.tabs(["Overview", "Student records", "Subject analysis", "Support review", "Export reports"])

with overview:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Performance categories")
        counts = df["Category"].value_counts().reindex(["Excellent", "Good", "Average", "Needs Improvement"], fill_value=0)
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(counts.index, counts.values)
        ax.set_ylabel("Students")
        ax.tick_params(axis="x", rotation=15)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
    with col2:
        st.subheader("Student averages")
        sortdf = df.sort_values("Average", ascending=False)
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(sortdf["RollNo"].astype(str), sortdf["Average"])
        ax.set_ylim(0, 100)
        ax.set_xlabel("Roll number")
        ax.set_ylabel("Average (%)")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
    x, y = st.columns(2)
    x.success(f"Highest average: {best['Name']} ({best['Average']:.2f}%)")
    y.warning(f"Lowest average: {worst['Name']} ({worst['Average']:.2f}%)")

with records:
    st.subheader("Search and filter")
    c1, c2, c3 = st.columns([2, 1, 1])
    query = c1.text_input("Search name or roll number")
    category_filter = c2.selectbox("Category", ["All", "Excellent", "Good", "Average", "Needs Improvement"])
    support_filter = c3.selectbox("Support", ["All", "Needs support", "No support flag"])
    filtered = df.copy()
    if query:
        mask = filtered["Name"].astype(str).str.contains(query, case=False, na=False) | filtered["RollNo"].astype(str).str.contains(query, case=False, na=False)
        filtered = filtered[mask]
    if category_filter != "All":
        filtered = filtered[filtered["Category"] == category_filter]
    if support_filter == "Needs support":
        filtered = filtered[filtered["SupportNeeded"]]
    elif support_filter == "No support flag":
        filtered = filtered[~filtered["SupportNeeded"]]
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.caption(f"Showing {len(filtered)} of {len(df)} records.")

with subjects_tab:
    st.subheader("Subject-wise averages")
    means = df[subjects].mean(numeric_only=True).sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(means.index, means.values)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Class mean (%)")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
    st.dataframe(pd.DataFrame({"Subject": means.index, "Class mean (%)": means.values.round(2)}), use_container_width=True, hide_index=True)
    st.caption("Only subject columns present in your uploaded file are analyzed. One subject is enough.")

with support:
    st.subheader("Students flagged for review")
    if has_attendance:
        att = df[df["Attendance"].notna()].sort_values("Attendance")
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.bar(att["RollNo"].astype(str), att["Attendance"])
        ax.axhline(attendance_limit, linestyle="--", label=f"Threshold ({attendance_limit}%)")
        ax.set_ylim(0, 100)
        ax.set_ylabel("Attendance (%)")
        ax.legend()
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
    else:
        st.info("Attendance column was not supplied. Attendance-based flags are disabled; average-based support flags still work.")
    if len(flagged):
        st.dataframe(flagged, use_container_width=True, hide_index=True)
        st.caption("These flags are prompts for human review, not final judgments about a student.")
    else:
        st.success("No students meet the current support rules.")

with export:
    st.subheader("Download results")
    st.download_button("Download analysis CSV", df.to_csv(index=False).encode("utf-8"), "analysis_report.csv", "text/csv")
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Analysis")
        pd.DataFrame({"Metric": ["Students", "Subjects", "Class average (%)", "Support flags"],
                      "Value": [len(df), ", ".join(subjects), round(class_average, 2), len(flagged)]}).to_excel(writer, index=False, sheet_name="Summary")
    st.download_button("Download Excel workbook", excel_buffer.getvalue(), "analysis_report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(A4), rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
        styles = getSampleStyleSheet()
        story = [Paragraph("Engineering Student Performance Analyzer", styles["Title"]),
                 Paragraph(f"Generated {datetime.now().strftime('%d %b %Y, %H:%M')} · {len(df)} students", styles["Normal"]),
                 Spacer(1, 12),
                 Paragraph(f"Class average: {class_average:.2f}% · Subjects: {', '.join(subjects)} · Support flags: {len(flagged)}", styles["Normal"]),
                 Spacer(1, 12)]
        fields = ["Name", "RollNo"] + subjects + (["Assignment"] if "Assignment" in df.columns else []) + (["Attendance"] if has_attendance else []) + ["Average", "Category", "SupportNeeded"]
        data = [fields]
        for _, row in df.iterrows():
            data.append([str(row.get(col, "")) if col in ("Name", "RollNo", "Category", "SupportNeeded") else (f"{row[col]:.1f}" if pd.notna(row.get(col)) else "—") for col in fields])
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#20304A")), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("GRID", (0,0), (-1,-1), .4, colors.grey), ("FONTSIZE", (0,0), (-1,-1), 7), ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F1F5F9")]), ("VALIGN", (0,0), (-1,-1), "MIDDLE")]))
        story.append(table)
        story.append(Spacer(1, 8))
        story.append(Paragraph("Grade and support thresholds are configurable example rules; review flags with an educator.", styles["Italic"]))
        doc.build(story)
        st.download_button("Download PDF report", pdf_buffer.getvalue(), "student_performance_report.pdf", "application/pdf")
    except ImportError:
        st.warning("Install reportlab to enable PDF export.")
    template_cols = ["Name", "RollNo", "Maths", "Assignment", "Attendance"]
    template = pd.DataFrame(columns=template_cols)
    st.download_button("Download minimal CSV template (one subject)", template.to_csv(index=False).encode("utf-8"), "student_template_one_subject.csv", "text/csv")
    st.caption("To use another subject, replace Maths with any subject name, such as Chemistry or Biology.")

st.divider()
st.caption("Python · NumPy · Pandas · Matplotlib · Streamlit | Version 2.0")
st.markdown(
    "<div style='text-align:center; padding:18px 0 6px 0; color: #8b95a5; "
    "font-size: 13px;'>Developed by <strong>Dhruv Kumar</strong></div>",
    unsafe_allow_html=True,
)
