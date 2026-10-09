
"""
Phase 10A: Automated Regression Comparator Tests

Purpose:
Verify that our regression detection engine correctly identifies:
1. Regressions
2. Improvements
3. Unchanged results
4. Accuracy thresholds
5. Summary quality and latency warnings
"""

from src.comparator import (
    compare_test_cases,
    determine_status,
    compare_evaluations,
)


# ============================================================
# TEST 1: PASS -> FAIL = REGRESSION
# ============================================================

def test_detect_regression():
    """A previously correct answer becomes incorrect."""

    baseline = {
        "results": [
            {
                "test_id": "TC001",
                "category_correct": True,
                "predicted_category": "billing",
            }
        ]
    }

    current = {
        "results": [
            {
                "test_id": "TC001",
                "category_correct": False,
                "predicted_category": "account",
            }
        ]
    }

    result = compare_test_cases(baseline, current)

    assert len(result["regressions"]) == 1
    assert result["regressions"][0]["test_id"] == "TC001"
    assert result["regressions"][0]["change"] == "REGRESSION"


# ============================================================
# TEST 2: FAIL -> PASS = IMPROVEMENT
# ============================================================

def test_detect_improvement():
    """A previously incorrect answer becomes correct."""

    baseline = {
        "results": [
            {"test_id": "TC002", "category_correct": False}
        ]
    }

    current = {
        "results": [
            {"test_id": "TC002", "category_correct": True}
        ]
    }

    result = compare_test_cases(baseline, current)

    assert len(result["improvements"]) == 1
    assert result["improvements"][0]["change"] == "IMPROVEMENT"


# ============================================================
# TEST 3: UNCHANGED RESULTS
# ============================================================

def test_unchanged_results():
    """Detect cases that remain correct or incorrect."""

    baseline = {
        "results": [
            {"test_id": "TC003", "category_correct": True},
            {"test_id": "TC004", "category_correct": False},
        ]
    }

    current = {
        "results": [
            {"test_id": "TC003", "category_correct": True},
            {"test_id": "TC004", "category_correct": False},
        ]
    }

    result = compare_test_cases(baseline, current)

    assert len(result["unchanged_passes"]) == 1
    assert len(result["unchanged_failures"]) == 1
    assert len(result["regressions"]) == 0


# ============================================================
# TEST 4: HEALTHY ACCURACY = PASS
# ============================================================

def test_status_pass():
    """Good performance should pass."""

    status, drop, reasons = determine_status(
        baseline_accuracy=95.0,
        current_accuracy=95.0,
        current_summary_score=4.5,
        current_latency_ms=1000,
    )

    assert status == "PASS"
    assert drop == 0
    assert "No regression thresholds were exceeded." in reasons


# ============================================================
# TEST 5: 5% ACCURACY DROP = WARNING
# ============================================================

def test_status_warning():
    """A moderate accuracy drop triggers a warning."""

    status, drop, reasons = determine_status(
        baseline_accuracy=95.0,
        current_accuracy=90.0,
        current_summary_score=4.5,
        current_latency_ms=1000,
    )

    assert status == "WARNING"
    assert round(drop, 2) == 0.05


# ============================================================
# TEST 6: 10% ACCURACY DROP = CRITICAL
# ============================================================

def test_status_critical():
    """A large accuracy drop must be critical."""

    status, drop, reasons = determine_status(
        baseline_accuracy=95.0,
        current_accuracy=85.0,
        current_summary_score=4.5,
        current_latency_ms=1000,
    )

    assert status == "CRITICAL"
    assert round(drop, 2) == 0.10


# ============================================================
# TEST 7: LOW SUMMARY QUALITY = WARNING
# ============================================================

def test_low_summary_score():
    """Low-quality summaries trigger a warning."""

    status, _, reasons = determine_status(
        baseline_accuracy=95.0,
        current_accuracy=95.0,
        current_summary_score=3.2,
        current_latency_ms=1000,
    )

    assert status == "WARNING"
    assert any("Summary score" in reason for reason in reasons)


# ============================================================
# TEST 8: HIGH LATENCY = WARNING
# ============================================================

def test_high_latency():
    """Slow AI responses trigger a warning."""

    status, _, reasons = determine_status(
        baseline_accuracy=95.0,
        current_accuracy=95.0,
        current_summary_score=4.5,
        current_latency_ms=2500,
    )

    assert status == "WARNING"
    assert any("latency" in reason for reason in reasons)


# ============================================================
# TEST 9: FULL EVALUATION COMPARISON
# ============================================================

def test_complete_comparison():
    """Test the complete comparison engine."""

    baseline = {
        "prompt_version": "v1",
        "metrics": {
            "accuracy_percent": 100.0,
            "average_summary_score": 4.5,
            "average_latency_ms": 900,
        },
        "results": [
            {"test_id": "TC001", "category_correct": True}
        ],
    }

    current = {
        "prompt_version": "v2",
        "metrics": {
            "accuracy_percent": 0.0,
            "average_summary_score": 4.5,
            "average_latency_ms": 1000,
        },
        "results": [
            {"test_id": "TC001", "category_correct": False}
        ],
    }

    report = compare_evaluations(baseline, current)

    assert report["baseline_prompt"] == "v1"
    assert report["current_prompt"] == "v2"
    assert report["regression_count"] == 1
    assert report["accuracy_delta"] == -100.0
    assert report["status"] == "CRITICAL"
