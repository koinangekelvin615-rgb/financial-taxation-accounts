
import json
import os
from datetime import datetime
import uuid

FILE = "maths_leakage_reports.json"

def submit_report():
    print("\n--- KCSE MATHEMATICS REPORT ---")

    paper = input("Select paper (Paper 1 or Paper 2): ")
    source = input("Where was the suspected leak found? ")
    description = input("Describe what happened: ")

    report = {
        "Reference": str(uuid.uuid4())[:8],
        "Date": str(datetime.now()),
        "Subject": "Mathematics",
        "Paper": paper,
        "Source": source,
        "Description": description,
        "Status": "Pending investigation"
    }

    if os.path.exists(FILE):
        with open(FILE, "r") as file:
            reports = json.load(file)
    else:
        reports = []

    reports.append(report)

    with open(FILE, "w") as file:
        json.dump(reports, file, indent=4)

    print("\nReport successfully saved!")
    print("Reference:", report["Reference"])


def view_reports():
    if not os.path.exists(FILE):
        print("No reports found.")
        return

    with open(FILE, "r") as file:
        reports = json.load(file)

    for report in reports:
        print("\n----------------------")
        for key, value in report.items():
            print(key, ":", value)


while True:
    print("\n===== KCSE MATHEMATICS =====")
    print("1. Report suspected leakage")
    print("2. View reports")
    print("3. Exit")

    choice = input("Enter choice: ")