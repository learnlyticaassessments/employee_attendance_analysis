import importlib.util
import datetime
import os
import pandas as pd
import inspect
import random

def test_student_code(solution_path):
    report_dir = os.path.join(os.path.dirname(__file__), "..", "student_workspace")
    report_path = os.path.join(report_dir, "report.txt")
    os.makedirs(report_dir, exist_ok=True)

    spec = importlib.util.spec_from_file_location("student_module", solution_path)
    student_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(student_module)

    analyzer = student_module.AttendanceAnalyzer()
    report_lines = [f"\n=== Attendance Analysis Test Run at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ==="]

    visible_cases = [
        {
            "desc": "Creating structured attendance DataFrame",
            "func": "create_attendance_df",
            "input": [[201, "Sales", "2024-06-01", "Present"], [202, "HR", "2024-06-01", "Absent"], [201, "Sales", "2024-06-02", "Leave"]],
            "expected": pd.DataFrame([[201, "Sales", "2024-06-01", "Present"], [202, "HR", "2024-06-01", "Absent"], [201, "Sales", "2024-06-02", "Leave"]],
                                     columns=["EmployeeID", "Department", "Date", "Attendance"])
        },
        {
            "desc": "Calculating monthly attendance rate",
            "func": "compute_monthly_attendance_rate",
            "input": pd.DataFrame([[201, "Sales", "2024-06-01", "Present"], [201, "Sales", "2024-06-02", "Absent"], [202, "HR", "2024-06-01", "Absent"]],
                                  columns=["EmployeeID", "Department", "Date", "Attendance"]),
            "expected": pd.DataFrame({"EmployeeID": [201, 202], "Month": ["2024-06", "2024-06"], "Attendance Rate": [50.0, 0.0]})
        },
        {
            "desc": "Adding correct absence flag",
            "func": "add_absence_flag",
            "input": pd.DataFrame([[201, "Sales", "2024-06-01", "Present"], [202, "HR", "2024-06-01", "Absent"], [201, "Sales", "2024-06-02", "Leave"]],
                                  columns=["EmployeeID", "Department", "Date", "Attendance"]),
            "expected": pd.DataFrame([[201, "Sales", "2024-06-01", "Present", 0], [202, "HR", "2024-06-01", "Absent", 1], [201, "Sales", "2024-06-02", "Leave", 0]],
                                     columns=["EmployeeID", "Department", "Date", "Attendance", "IsAbsent"])
        },
        {
            "desc": "Identifying high absentee employees",
            "func": "high_absentees",
            "input": (pd.DataFrame([[201, "Sales", "2024-06-01", "Absent"], [202, "HR", "2024-06-01", "Absent"], [202, "HR", "2024-06-02", "Absent"]],
                                   columns=["EmployeeID", "Department", "Date", "Attendance"]), 1),
            "expected": pd.DataFrame({"EmployeeID": [202], "Absence Count": [2]})
        }
    ]

    hidden_cases = [
        {
            "desc": "Departments with only one attendance type",
            "func": "department_attendance_summary",
            "input": pd.DataFrame([[401, "Legal", "2024-06-01", "Leave"], [402, "Legal", "2024-06-02", "Leave"]],
                                  columns=["EmployeeID", "Department", "Date", "Attendance"]),
            "expected": pd.DataFrame({"Department": ["Legal"], "Present": [0], "Absent": [0], "Leave": [2]})
        }
    ]

    keyword_checks = {
        "create_attendance_df": ["pd.dataframe"],
        "compute_monthly_attendance_rate": ["groupby", "size", "fillna", "reset_index"],
        "add_absence_flag": ["astype", "=="],
        "high_absentees": ["groupby", "size", "reset_index"],
        "department_attendance_summary": ["groupby", "unstack", "reset_index", "crosstab"],
        "clean_attendance_data": ["isin"]
    }

    # def detect_hardcoded_or_pass(src, expected):
    #     flat = src.replace(" ", "").replace("\n", "")
    #     return 'pass' in flat or str(expected).replace(" ", "") in flat

    def validate_keywords(src, required):
        return any(k in src for k in required)

    def random_check(func_name):
        # Random check: Generate random input/output and validate logic is not hardcoded
        data = [[random.randint(100, 999), random.choice(["HR", "Sales", "IT", "Finance"]),
                 f"2024-0{random.randint(1,6)}-{random.randint(1,28):02d}",
                 random.choice(["Present", "Absent", "Leave"])] for _ in range(20)]
        df = pd.DataFrame(data, columns=["EmployeeID", "Department", "Date", "Attendance"])

        if func_name == "department_attendance_summary":
            expected = pd.crosstab(df["Department"], df["Attendance"])
            expected.columns.name = None
            for col in ["Present", "Absent", "Leave"]:
                if col not in expected.columns:
                    expected[col] = 0
            expected = expected.reset_index()
            expected = expected[["Department", "Present", "Absent", "Leave"]]

            try:
                result = getattr(analyzer, func_name)(df)
                pd.testing.assert_frame_equal(result.sort_index(axis=1), expected.sort_index(axis=1), check_dtype=False)
                return True
            except:
                return False
        return True

    all_cases = [("Visible", visible_cases), ("Hidden", hidden_cases)]

    for section, cases in all_cases:
        for i, case in enumerate(cases, 1):
            try:
                func = getattr(analyzer, case["func"])
                src = inspect.getsource(func).lower()

                # if detect_hardcoded_or_pass(src, case["expected"]):
                #     msg = f"❌ {section} Test Case {i} Failed: {case['desc']} | Reason: Hardcoded return or 'pass'"
                #     report_lines.append(msg)
                #     print(msg)
                #     continue

                if not validate_keywords(src, keyword_checks.get(case["func"], [])):
                    msg = f"❌ {section} Test Case {i} Failed: {case['desc']} | Reason: Missing logic keywords"
                    report_lines.append(msg)
                    print(msg)
                    continue

                # Run random check for logic (not logged in report)
                if not random_check(case["func"]):
                    msg = f"❌ {section} Test Case {i} Failed: {case['desc']} | Reason: Logic failed random check (potential hardcoding)"
                    report_lines.append(msg)
                    print(msg)
                    continue

                input_data = case["input"]
                result = func(*input_data) if isinstance(input_data, tuple) else func(input_data)
                expected = case["expected"]

                if isinstance(expected, pd.DataFrame):
                    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected.reset_index(drop=True), check_dtype=False)
                else:
                    assert result == expected

                msg = f"✅ {section} Test Case {i} Passed: {case['desc']}"
                report_lines.append(msg)
                print(msg)

            except Exception as e:
                msg = f"❌ {section} Test Case {i} Crashed: {case['desc']} | Error: {str(e)}"
                report_lines.append(msg)
                print(msg)

    with open(report_path, "a", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")

if __name__ == "__main__":
    solution_file = os.path.join(os.path.dirname(__file__), "..", "student_workspace", "solution.py")
    test_student_code(solution_file)
