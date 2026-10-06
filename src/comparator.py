"""
LLM Regression Detection System
Phase 3C: Regression Comparison Engine

Purpose:
Compare a BASELINE evaluation with a CURRENT evaluation.

Detect:
    PASS -> FAIL = REGRESSION
    FAIL -> PASS = IMPROVEMENT
    PASS -> PASS = UNCHANGED PASS
    FAIL -> FAIL = UNCHANGED FAIL

Also applies thresholds to determine:

    PASS
    WARNING
    CRITICAL
"""

import json
from pathlib import Path


# ============================================================
# DEFAULT THRESHOLDS
# ============================================================

DEFAULT_THRESHOLDS = {
    "warning_accuracy_drop": 0.03,
    "critical_accuracy_drop": 0.08,
    "minimum_summary_score": 4.0,
    "maximum_latency_ms": 2000,
}


# ============================================================
# LOAD EVALUATION REPORT
# ============================================================

def load_evaluation_report(file_path):
    """
    Load an evaluation JSON report.

    Example:

        reports/evaluation_v1.json
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Evaluation report not found: {path}"
        )

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


# ============================================================
# TURN RESULTS INTO LOOKUP TABLE
# ============================================================

def build_result_lookup(report):
    """
    Convert:

        [
            {"test_id": "TC001", ...},
            {"test_id": "TC002", ...}
        ]

    into:

        {
            "TC001": {...},
            "TC002": {...}
        }

    This makes comparison easier.
    """

    lookup = {}

    for result in report.get("results", []):

        test_id = result.get("test_id")

        if test_id:
            lookup[test_id] = result

    return lookup


# ============================================================
# COMPARE INDIVIDUAL TEST CASES
# ============================================================

def compare_test_cases(baseline_report, current_report):
    """
    Compare every test case between two evaluation runs.

    PASS -> FAIL = REGRESSION
    FAIL -> PASS = IMPROVEMENT
    """

    baseline_results = build_result_lookup(
        baseline_report
    )

    current_results = build_result_lookup(
        current_report
    )

    regressions = []
    improvements = []
    unchanged_passes = []
    unchanged_failures = []

    # Tests appearing in both reports
    common_test_ids = sorted(
        set(baseline_results.keys())
        & set(current_results.keys())
    )

    for test_id in common_test_ids:

        baseline = baseline_results[test_id]
        current = current_results[test_id]

        baseline_passed = bool(
            baseline.get("category_correct", False)
        )

        current_passed = bool(
            current.get("category_correct", False)
        )

        comparison = {
            "test_id": test_id,

            "baseline_category": baseline.get(
                "predicted_category"
            ),

            "current_category": current.get(
                "predicted_category"
            ),

            "expected_category": current.get(
                "expected_category"
            ),

            "baseline_passed": baseline_passed,

            "current_passed": current_passed,
        }

        # --------------------------------------------
        # PASS -> FAIL
        # --------------------------------------------

        if baseline_passed and not current_passed:

            comparison["change"] = "REGRESSION"

            regressions.append(comparison)

        # --------------------------------------------
        # FAIL -> PASS
        # --------------------------------------------

        elif not baseline_passed and current_passed:

            comparison["change"] = "IMPROVEMENT"

            improvements.append(comparison)

        # --------------------------------------------
        # PASS -> PASS
        # --------------------------------------------

        elif baseline_passed and current_passed:

            comparison["change"] = "UNCHANGED_PASS"

            unchanged_passes.append(comparison)

        # --------------------------------------------
        # FAIL -> FAIL
        # --------------------------------------------

        else:

            comparison["change"] = "UNCHANGED_FAIL"

            unchanged_failures.append(comparison)

    return {
        "regressions": regressions,
        "improvements": improvements,
        "unchanged_passes": unchanged_passes,
        "unchanged_failures": unchanged_failures,
    }


# ============================================================
# APPLY THRESHOLDS
# ============================================================

def determine_status(
    baseline_accuracy,
    current_accuracy,
    current_summary_score,
    current_latency_ms,
    thresholds=None,
):
    """
    Decide whether the new evaluation is:

        PASS
        WARNING
        CRITICAL

    Accuracy values in our reports are percentages:

        94.0
        89.0

    Thresholds are decimals:

        0.03 = 3%
        0.08 = 8%
    """

    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    # Convert percentage-point difference to decimal.
    #
    # Example:
    #
    # 94% -> 89%
    #
    # drop = 5 / 100
    #      = 0.05
    #      = 5%
    #
    accuracy_drop = max(
        0.0,
        (baseline_accuracy - current_accuracy) / 100
    )

    reasons = []

    status = "PASS"

    # --------------------------------------------
    # CRITICAL accuracy regression
    # --------------------------------------------

    if accuracy_drop > thresholds[
        "critical_accuracy_drop"
    ]:

        status = "CRITICAL"

        reasons.append(
            f"Accuracy dropped by "
            f"{accuracy_drop * 100:.2f}%."
        )

    # --------------------------------------------
    # WARNING accuracy regression
    # --------------------------------------------

    elif accuracy_drop > thresholds[
        "warning_accuracy_drop"
    ]:

        status = "WARNING"

        reasons.append(
            f"Accuracy dropped by "
            f"{accuracy_drop * 100:.2f}%."
        )

    # --------------------------------------------
    # SUMMARY QUALITY
    # --------------------------------------------

    if (
        current_summary_score
        < thresholds["minimum_summary_score"]
    ):

        if status == "PASS":
            status = "WARNING"

        reasons.append(
            f"Summary score "
            f"{current_summary_score:.2f} "
            f"is below minimum "
            f"{thresholds['minimum_summary_score']:.2f}."
        )

    # --------------------------------------------
    # LATENCY
    # --------------------------------------------

    if (
        current_latency_ms
        > thresholds["maximum_latency_ms"]
    ):

        if status == "PASS":
            status = "WARNING"

        reasons.append(
            f"Average latency "
            f"{current_latency_ms:.2f} ms "
            f"exceeds maximum "
            f"{thresholds['maximum_latency_ms']} ms."
        )

    if not reasons:
        reasons.append(
            "No regression thresholds were exceeded."
        )

    return status, accuracy_drop, reasons


# ============================================================
# COMPARE TWO COMPLETE EVALUATIONS
# ============================================================

def compare_evaluations(
    baseline_report,
    current_report,
    thresholds=None,
):
    """
    Main comparison function.
    """

    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    baseline_metrics = baseline_report["metrics"]
    current_metrics = current_report["metrics"]

    baseline_accuracy = baseline_metrics[
        "accuracy_percent"
    ]

    current_accuracy = current_metrics[
        "accuracy_percent"
    ]

    current_summary_score = current_metrics[
        "average_summary_score"
    ]

    current_latency_ms = current_metrics[
        "average_latency_ms"
    ]

    # --------------------------------------------
    # Test-by-test comparison
    # --------------------------------------------

    test_changes = compare_test_cases(
        baseline_report,
        current_report
    )

    # --------------------------------------------
    # Overall status
    # --------------------------------------------

    status, accuracy_drop, reasons = determine_status(
        baseline_accuracy,
        current_accuracy,
        current_summary_score,
        current_latency_ms,
        thresholds,
    )

    accuracy_delta = (
        current_accuracy - baseline_accuracy
    )

    comparison_report = {

        "baseline_prompt": baseline_report.get(
            "prompt_version"
        ),

        "current_prompt": current_report.get(
            "prompt_version"
        ),

        "baseline_accuracy": baseline_accuracy,

        "current_accuracy": current_accuracy,

        "accuracy_delta": round(
            accuracy_delta,
            2
        ),

        "accuracy_drop_percent": round(
            accuracy_drop * 100,
            2
        ),

        "regression_count": len(
            test_changes["regressions"]
        ),

        "improvement_count": len(
            test_changes["improvements"]
        ),

        "unchanged_pass_count": len(
            test_changes["unchanged_passes"]
        ),

        "unchanged_fail_count": len(
            test_changes["unchanged_failures"]
        ),

        "status": status,

        "reasons": reasons,

        "regressions": test_changes[
            "regressions"
        ],

        "improvements": test_changes[
            "improvements"
        ],
    }

    return comparison_report


# ============================================================
# PRINT HUMAN-READABLE REPORT
# ============================================================

def print_comparison_report(report):
    """
    Display the regression report in the terminal.
    """

    print("\n========================================")
    print("      REGRESSION COMPARISON")
    print("========================================")

    print(
        f"\nBaseline prompt : "
        f"{report['baseline_prompt']}"
    )

    print(
        f"Current prompt  : "
        f"{report['current_prompt']}"
    )

    print(
        f"\nBaseline accuracy : "
        f"{report['baseline_accuracy']:.2f}%"
    )

    print(
        f"Current accuracy  : "
        f"{report['current_accuracy']:.2f}%"
    )

    print(
        f"Delta             : "
        f"{report['accuracy_delta']:+.2f}%"
    )

    print(
        f"\nRegressions       : "
        f"{report['regression_count']}"
    )

    print(
        f"Improvements      : "
        f"{report['improvement_count']}"
    )

    print(
        f"\nSTATUS            : "
        f"{report['status']}"
    )

    # --------------------------------------------
    # Regression details
    # --------------------------------------------

    if report["regressions"]:

        print("\nREGRESSIONS:")

        for regression in report["regressions"]:

            print(
                f"  {regression['test_id']}: "
                f"PASS -> FAIL"
            )

    # --------------------------------------------
    # Improvement details
    # --------------------------------------------

    if report["improvements"]:

        print("\nIMPROVEMENTS:")

        for improvement in report["improvements"]:

            print(
                f"  {improvement['test_id']}: "
                f"FAIL -> PASS"
            )

    print("\nReasons:")

    for reason in report["reasons"]:

        print(
            f"  - {reason}"
        )

    print("\n========================================\n")