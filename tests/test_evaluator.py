
"""
Phase 10D: Evaluation Engine Unit Tests

All model calls and database writes are mocked.
No OpenAI credits are used.
"""

import json
from types import SimpleNamespace

import pytest

from src import evaluator


# ============================================================
# TEST 1: SUMMARY SCORING
# ============================================================

@pytest.mark.parametrize(
    "predicted, expected_score",
    [
        ("refund invoice payment account", 5),
        ("refund invoice payment", 4),  # 75% overlap
        ("refund invoice", 3),          # 50% overlap
        ("refund", 2),                  # 25% overlap
        ("unrelated words", 1),         # 0% overlap
    ],
)
def test_summary_score(predicted, expected_score):
    """Check our word-overlap scoring system."""

    score = evaluator.calculate_summary_score(
        "refund invoice payment account",
        predicted,
    )

    assert score == expected_score


# ============================================================
# TEST 2: EMPTY EXPECTED SUMMARY
# ============================================================

def test_empty_expected_summary():
    """An empty reference summary scores 1."""

    assert evaluator.calculate_summary_score(
        "",
        "some predicted text",
    ) == 1


# ============================================================
# TEST 3: CORRECT CLASSIFICATION
# ============================================================

def test_correct_classification(monkeypatch):
    """The AI correctly predicts the email category."""

    monkeypatch.setattr(
        evaluator,
        "classify_email",
        lambda email, config: SimpleNamespace(
            category="billing",
            summary="Customer requests refund",
        ),
    )

    test_case = {
        "id": "TC001",
        "difficulty": "easy",
        "email": "Please refund my payment.",
        "expected_category": "billing",
        "expected_summary": "Customer requests refund",
    }

    result = evaluator.evaluate_test_case(
        test_case,
        {"version": "test"},
    )

    assert result["test_id"] == "TC001"
    assert result["category_correct"] is True
    assert result["summary_score"] == 5
    assert result["latency_ms"] >= 0


# ============================================================
# TEST 4: INCORRECT CLASSIFICATION
# ============================================================

def test_incorrect_classification(monkeypatch):
    """The AI predicts the wrong category."""

    monkeypatch.setattr(
        evaluator,
        "classify_email",
        lambda email, config: SimpleNamespace(
            category="technical",
            summary="Customer requests refund",
        ),
    )

    test_case = {
        "id": "TC002",
        "difficulty": "medium",
        "email": "I need a refund.",
        "expected_category": "billing",
        "expected_summary": "Customer requests refund",
    }

    result = evaluator.evaluate_test_case(
        test_case,
        {"version": "test"},
    )

    assert result["category_correct"] is False
    assert result["predicted_category"] == "technical"


# ============================================================
# TEST 5: FULL EVALUATION REPORT
# ============================================================

def test_full_evaluation(monkeypatch, tmp_path):
    """Verify report metrics and JSON generation."""

    monkeypatch.setattr(
        evaluator,
        "REPORTS_DIR",
        tmp_path,
    )

    monkeypatch.setattr(
        evaluator,
        "load_golden_dataset",
        lambda: [
            {"id": "TC001"},
            {"id": "TC002"},
        ],
    )

    monkeypatch.setattr(
        evaluator,
        "load_prompt_config",
        lambda version: {"version": version},
    )

    def fake_evaluate(test_case, config):
        passed = test_case["id"] == "TC001"

        return {
            "test_id": test_case["id"],
            "category_correct": passed,
            "predicted_category": "billing",
            "expected_category": "billing" if passed else "account",
            "summary_score": 5 if passed else 3,
            "latency_ms": 100.0 if passed else 200.0,
        }

    monkeypatch.setattr(
        evaluator,
        "evaluate_test_case",
        fake_evaluate,
    )

    saved_history = []

    monkeypatch.setattr(
        evaluator,
        "save_evaluation_run",
        lambda **kwargs: saved_history.append(kwargs),
    )

    evaluator.run_evaluation("test")

    report_path = tmp_path / "evaluation_test.json"

    assert report_path.exists()

    report = json.loads(report_path.read_text())

    assert report["metrics"]["total_tests"] == 2
    assert report["metrics"]["correct"] == 1
    assert report["metrics"]["incorrect"] == 1
    assert report["metrics"]["accuracy_percent"] == 50.0
    assert report["metrics"]["average_summary_score"] == 4.0
    assert report["metrics"]["average_latency_ms"] == 150.0

    assert len(saved_history) == 1


# ============================================================
# TEST 6: INDIVIDUAL TEST CASE ERROR
# ============================================================

def test_evaluation_handles_error(monkeypatch, tmp_path):
    """One failed model call must be recorded."""

    monkeypatch.setattr(
        evaluator,
        "REPORTS_DIR",
        tmp_path,
    )

    monkeypatch.setattr(
        evaluator,
        "load_golden_dataset",
        lambda: [{"id": "TC001"}],
    )

    monkeypatch.setattr(
        evaluator,
        "load_prompt_config",
        lambda version: {},
    )

    def fake_evaluate(test_case, config):
        raise RuntimeError("Simulated model failure")

    monkeypatch.setattr(
        evaluator,
        "evaluate_test_case",
        fake_evaluate,
    )

    monkeypatch.setattr(
        evaluator,
        "save_evaluation_run",
        lambda **kwargs: None,
    )

    evaluator.run_evaluation("test")

    report = json.loads(
        (tmp_path / "evaluation_test.json").read_text()
    )

    assert report["metrics"]["correct"] == 0
    assert report["metrics"]["accuracy_percent"] == 0
    assert report["results"][0]["category_correct"] is False
    assert report["results"][0]["error"] == "Simulated model failure"
