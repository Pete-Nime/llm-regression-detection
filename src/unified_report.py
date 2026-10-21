"""
Phase 2 — Unified Regression and Drift Report

Purpose:
    Combine configuration drift findings with
    existing LLM regression evaluation results.

No OpenAI API calls are made here.
"""

import json
from pathlib import Path

from src.comparator import (
    load_evaluation_report,
    compare_evaluations,
)

from src.drift_detector import detect_configuration_drift


def generate_unified_report(
    baseline_evaluation_path: str,
    candidate_evaluation_path: str,
    baseline_snapshot_path: str,
    candidate_snapshot_path: str,
    output_path: str,
) -> dict:
    """
    Combine two independent checks:

    1. Configuration drift:
       What changed in the prompt or model settings?

    2. Behavioural regression:
       Did any previously passing test start failing?
    """

    # STEP 1: Load the existing evaluation reports.
    baseline_evaluation = load_evaluation_report(
        baseline_evaluation_path
    )

    candidate_evaluation = load_evaluation_report(
        candidate_evaluation_path
    )

    # STEP 2: Reuse the existing regression engine.
    regression = compare_evaluations(
        baseline_evaluation,
        candidate_evaluation,
    )

    # STEP 3: Compare the configuration snapshots.
    drift = detect_configuration_drift(
        baseline_snapshot_path,
        candidate_snapshot_path,
    )

    # STEP 4: Combine both results.
    unified_report = {
        "baseline_prompt": regression["baseline_prompt"],
        "candidate_prompt": regression["current_prompt"],
        "configuration_drift": drift,
        "regression_analysis": regression,
        "release_status": regression["status"],
    }

    # STEP 5: Save the combined JSON report.
    destination = Path(output_path)

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination.write_text(
        json.dumps(
            unified_report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return unified_report