"""
LLM Regression Detection System
Phase 4B

Runs the comparison engine and generates
the final HTML report.

Usage:

python -m src.run_comparison \
    reports/evaluation_v1.json \
    reports/evaluation_v2.json
"""

import json
import sys
from pathlib import Path

from src.comparator import (
    load_evaluation_report,
    compare_evaluations,
    print_comparison_report,
)

from src.reporter import generate_html_report


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"

COMPARISON_JSON_PATH = (
    REPORTS_DIR / "comparison_report.json"
)


def save_comparison_json(report):
    """
    Save the machine-readable comparison report.
    """

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        COMPARISON_JSON_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False
        )


def main():

    # --------------------------------------------------------
    # CHECK TERMINAL ARGUMENTS
    # --------------------------------------------------------

    if len(sys.argv) != 3:

        print(
            "\nUsage:"
        )

        print(
            "python -m src.run_comparison "
            "reports/evaluation_v1.json "
            "reports/evaluation_v2.json"
        )

        return

    # --------------------------------------------------------
    # FILES
    # --------------------------------------------------------

    baseline_path = sys.argv[1]
    current_path = sys.argv[2]

    print("\nLoading evaluation reports...")

    print(
        f"Baseline: {baseline_path}"
    )

    print(
        f"Current : {current_path}"
    )

    # --------------------------------------------------------
    # LOAD REPORTS
    # --------------------------------------------------------

    baseline_report = load_evaluation_report(
        baseline_path
    )

    current_report = load_evaluation_report(
        current_path
    )

    # --------------------------------------------------------
    # COMPARE
    # --------------------------------------------------------

    comparison = compare_evaluations(
        baseline_report,
        current_report
    )

    # --------------------------------------------------------
    # TERMINAL REPORT
    # --------------------------------------------------------

    print_comparison_report(
        comparison
    )

    # --------------------------------------------------------
    # SAVE JSON REPORT
    # --------------------------------------------------------

    save_comparison_json(
        comparison
    )

    print(
        "Comparison JSON saved:"
    )

    print(
        COMPARISON_JSON_PATH
    )

    # --------------------------------------------------------
    # GENERATE HTML
    # --------------------------------------------------------

    html_path = generate_html_report(
        comparison
    )

    print(
        "\nPhase 4 complete."
    )

    print(
        f"Open this file in your browser:\n{html_path}"
    )


if __name__ == "__main__":
    main()
