"""
Phase 2 — Unified Report Integration Tests

Purpose:
    Verify that configuration drift and regression
    analysis are combined correctly.
"""

import json

from src.unified_report import generate_unified_report


def test_unified_report_integration(tmp_path):
    """Test the complete integration without OpenAI API calls."""

    # STEP 1: Create temporary file paths.
    baseline_eval = tmp_path / "baseline_eval.json"
    candidate_eval = tmp_path / "candidate_eval.json"

    baseline_snapshot = tmp_path / "baseline_snapshot.json"
    candidate_snapshot = tmp_path / "candidate_snapshot.json"

    output_file = tmp_path / "unified_report.json"

    # STEP 2: Create sample evaluation reports.
    def make_evaluation(version, passed):
        return {
            "prompt_version": version,
            "metrics": {
                "accuracy_percent": 100.0 if passed else 0.0,
                "average_summary_score": 5.0,
                "average_latency_ms": 100.0,
            },
            "results": [
                {
                    "test_id": "TC001",
                    "category_correct": passed,
                    "predicted_category": (
                        "billing" if passed else "general"
                    ),
                    "expected_category": "billing",
                }
            ],
        }

    baseline_eval.write_text(
        json.dumps(make_evaluation("v1", True)),
        encoding="utf-8",
    )

    candidate_eval.write_text(
        json.dumps(make_evaluation("v2", False)),
        encoding="utf-8",
    )

    # STEP 3: Create sample configuration snapshots.
    baseline_snapshot.write_text(
        json.dumps({
            "prompt_sha256": "original_hash",
            "prompt_version": "1.0",
            "model_config": {
                "model": "gpt-4o-mini",
                "temperature": 0,
            },
        }),
        encoding="utf-8",
    )

    candidate_snapshot.write_text(
        json.dumps({
            "prompt_sha256": "modified_hash",
            "prompt_version": "2.0",
            "model_config": {
                "model": "gpt-4o-mini",
                "temperature": 0.7,
            },
        }),
        encoding="utf-8",
    )

    # STEP 4: Generate the unified report.
    report = generate_unified_report(
        str(baseline_eval),
        str(candidate_eval),
        str(baseline_snapshot),
        str(candidate_snapshot),
        str(output_file),
    )

    # STEP 5: Verify configuration drift.
    assert report["configuration_drift"]["drift_detected"] is True
    assert report["configuration_drift"]["prompt_changed"] is True

    assert (
        report["configuration_drift"]["model_config_changes"]
        ["temperature"]["candidate"]
        == 0.7
    )

    # STEP 6: Verify regression detection.
    assert report["regression_analysis"]["regression_count"] == 1
    assert report["regression_analysis"]["improvement_count"] == 0

    # STEP 7: Verify release status.
    assert report["release_status"] == "CRITICAL"

    # STEP 8: Verify the JSON was saved correctly.
    assert output_file.exists()

    saved_report = json.loads(
        output_file.read_text(encoding="utf-8")
    )

    assert saved_report == report