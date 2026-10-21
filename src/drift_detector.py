"""
Phase 2 — Configuration Drift Detector

Purpose:
    Compare two configuration snapshots and identify changes.
"""

import json
from pathlib import Path


def detect_configuration_drift(
    baseline_path: str,
    candidate_path: str,
) -> dict:
    """
    Compare baseline and candidate configuration snapshots.
    """

    # STEP 1: Load both JSON snapshots.
    baseline = json.loads(
        Path(baseline_path).read_text(encoding="utf-8")
    )

    candidate = json.loads(
        Path(candidate_path).read_text(encoding="utf-8")
    )

    # STEP 2: Check whether the prompt contents changed.
    prompt_changed = (
        baseline["prompt_sha256"]
        != candidate["prompt_sha256"]
    )

    # STEP 3: Check whether the prompt version changed.
    version_changed = (
        baseline["prompt_version"]
        != candidate["prompt_version"]
    )

    # STEP 4: Compare model configuration settings.
    baseline_config = baseline["model_config"]
    candidate_config = candidate["model_config"]

    config_changes = {}

    # Check every configuration key from both snapshots.
    all_keys = set(baseline_config) | set(candidate_config)

    for key in sorted(all_keys):

        old_value = baseline_config.get(key)
        new_value = candidate_config.get(key)

        if old_value != new_value:
            config_changes[key] = {
                "baseline": old_value,
                "candidate": new_value,
            }

    # STEP 5: Determine whether any drift occurred.
    drift_detected = (
        prompt_changed
        or version_changed
        or bool(config_changes)
    )

    # STEP 6: Return a structured report.
    return {
        "drift_detected": drift_detected,
        "prompt_changed": prompt_changed,
        "version_changed": version_changed,
        "model_config_changes": config_changes,
    }