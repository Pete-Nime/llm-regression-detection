"""
Phase 2 — Configuration Drift Detector Tests

Purpose:
    Ensure our system correctly identifies configuration
    changes and unchanged configurations.
"""

import json

from src.drift_detector import detect_configuration_drift


def save_snapshot(path, prompt_hash, version, model_config):
    """
    Helper function:
    Create a fake snapshot for testing.
    """
    snapshot = {
        "prompt_sha256": prompt_hash,
        "prompt_version": version,
        "model_config": model_config,
    }

    path.write_text(
        json.dumps(snapshot),
        encoding="utf-8",
    )


def test_no_configuration_drift(tmp_path):
    """Identical configurations should produce no drift."""

    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"

    # Both snapshots have identical settings.
    save_snapshot(
        baseline, "abc123", "1.0",
        {"model": "gpt-4o-mini", "temperature": 0},
    )

    save_snapshot(
        candidate, "abc123", "1.0",
        {"model": "gpt-4o-mini", "temperature": 0},
    )

    result = detect_configuration_drift(
        str(baseline), str(candidate)
    )

    assert result["drift_detected"] is False
    assert result["prompt_changed"] is False
    assert result["version_changed"] is False
    assert result["model_config_changes"] == {}


def test_prompt_drift(tmp_path):
    """Changing prompt contents should trigger drift."""

    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"

    save_snapshot(
        baseline, "original_hash", "1.0",
        {"model": "gpt-4o-mini"},
    )

    save_snapshot(
        candidate, "modified_hash", "1.0",
        {"model": "gpt-4o-mini"},
    )

    result = detect_configuration_drift(
        str(baseline), str(candidate)
    )

    assert result["drift_detected"] is True
    assert result["prompt_changed"] is True
    assert result["version_changed"] is False


def test_model_configuration_drift(tmp_path):
    """Changing model settings should trigger drift."""

    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"

    save_snapshot(
        baseline, "same_hash", "1.0",
        {"model": "gpt-4o-mini", "temperature": 0},
    )

    save_snapshot(
        candidate, "same_hash", "1.0",
        {"model": "gpt-4o-mini", "temperature": 0.7},
    )

    result = detect_configuration_drift(
        str(baseline), str(candidate)
    )

    assert result["drift_detected"] is True
    assert result["prompt_changed"] is False

    assert result["model_config_changes"]["temperature"] == {
        "baseline": 0,
        "candidate": 0.7,
    }


def test_prompt_version_drift(tmp_path):
    """Changing the version number should trigger drift."""

    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"

    save_snapshot(
        baseline, "same_hash", "1.0",
        {"model": "gpt-4o-mini"},
    )

    save_snapshot(
        candidate, "same_hash", "2.0",
        {"model": "gpt-4o-mini"},
    )

    result = detect_configuration_drift(
        str(baseline), str(candidate)
    )

    assert result["drift_detected"] is True
    assert result["version_changed"] is True
    assert result["prompt_changed"] is False