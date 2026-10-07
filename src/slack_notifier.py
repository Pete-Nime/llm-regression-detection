import json
import os
import sys
from pathlib import Path

import requests


# ---------------------------------------------------------
# Locate our comparison report
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

REPORT_PATH = (
    PROJECT_ROOT
    / "reports"
    / "comparison_report.json"
)


def load_comparison_report():
    """
    Load the regression comparison produced by comparator.py.
    """

    if not REPORT_PATH.exists():
        print("ERROR: comparison_report.json was not found.")
        sys.exit(1)

    with open(REPORT_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def send_slack_alert():
    """
    Send the regression result to Slack.
    """

    # GitHub Actions will provide this secret.
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    if not webhook_url:
        print("ERROR: SLACK_WEBHOOK_URL is not set.")
        sys.exit(1)

    report = load_comparison_report()

    # These already exist in our comparison report.
    status = report.get("status", "UNKNOWN")
    regressions = report.get("regression_count", 0)
    accuracy_delta = report.get("accuracy_delta", 0)

    # Choose an icon based on severity.
    if status == "PASS":
        icon = "✅"
    elif status == "WARNING":
        icon = "⚠️"
    elif status == "CRITICAL":
        icon = "🚨"
    else:
        icon = "ℹ️"

    message = (
        f"{icon} *LLM Regression Detection: {status}*\n\n"
        f"*Accuracy Delta:* {accuracy_delta:+.2f}%\n"
        f"*Regressions:* {regressions}\n\n"
        f"Repository: `llm-regression-detection`"
    )

    response = requests.post(
        webhook_url,
        json={"text": message},
        timeout=10,
    )

    response.raise_for_status()

    print("Slack alert sent successfully.")


if __name__ == "__main__":
    send_slack_alert()