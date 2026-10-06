"""
LLM Regression Detection System
Phase 5: CI Regression Gate

Purpose:
Convert our regression comparison result into a CI/CD decision.

PASS     -> Exit 0
WARNING  -> Exit 0
CRITICAL -> Exit 1
"""

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

COMPARISON_REPORT = (
    PROJECT_ROOT
    / "reports"
    / "comparison_report.json"
)


def load_comparison_report():
    """Load the regression comparison report."""

    if not COMPARISON_REPORT.exists():
        print("ERROR: comparison_report.json was not found.")
        print("Run the comparison pipeline first.")
        sys.exit(1)

    with open(
        COMPARISON_REPORT,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def run_ci_gate():
    """Decide whether CI should pass or fail."""

    report = load_comparison_report()

    status = report.get("status", "CRITICAL")

    regressions = report.get(
        "regression_count",
        0
    )

    accuracy_delta = report.get(
        "accuracy_delta",
        0
    )

    print("\n========================================")
    print("          LLM CI REGRESSION GATE")
    print("========================================")

    print(f"\nStatus         : {status}")
    print(f"Regressions    : {regressions}")
    print(f"Accuracy Delta : {accuracy_delta:+.2f}%")

    print("\n----------------------------------------")

    if status == "PASS":

        print("CI RESULT: PASS ✅")
        print("No regression thresholds were exceeded.")

        sys.exit(0)

    elif status == "WARNING":

        print("CI RESULT: PASS WITH WARNING ⚠️")
        print("Review the evaluation report before deployment.")

        sys.exit(0)

    else:

        print("CI RESULT: FAIL ❌")
        print("Critical LLM regression detected.")
        print("Deployment should be blocked.")

        sys.exit(1)


if __name__ == "__main__":
    run_ci_gate()