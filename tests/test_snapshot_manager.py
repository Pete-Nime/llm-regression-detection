"""
Phase 2 — Snapshot Manager Unit Tests

Purpose:
    Verify that configuration snapshots are created correctly
    and that prompt changes produce different SHA-256 hashes.
"""

import hashlib
import json

from src.snapshot_manager import create_snapshot


def test_snapshot_creation(tmp_path):
    """Test that a valid snapshot is saved correctly."""

    # Create a temporary YAML prompt for testing.
    prompt_file = tmp_path / "test_prompt.yaml"

    prompt_file.write_text(
        'version: "1.0"\nsystem_prompt: "Classify emails"\n',
        encoding="utf-8",
    )

    # Choose a temporary destination for our snapshot.
    output_file = tmp_path / "snapshots" / "test.json"

    # Run the Snapshot Manager.
    snapshot = create_snapshot(
        prompt_path=str(prompt_file),
        model_config={
            "model": "gpt-4o-mini",
            "temperature": 0,
        },
        output_path=str(output_file),
    )

    # Verify that the JSON file was created.
    assert output_file.exists()

    # Verify the saved prompt version.
    assert snapshot["prompt_version"] == "1.0"

    # Verify the saved model name.
    assert snapshot["model_config"]["model"] == "gpt-4o-mini"

    # Verify that the hash matches the prompt's actual contents.
    expected_hash = hashlib.sha256(
        prompt_file.read_bytes()
    ).hexdigest()

    assert snapshot["prompt_sha256"] == expected_hash

    # Verify that the JSON file contains our snapshot.
    saved_snapshot = json.loads(
        output_file.read_text(encoding="utf-8")
    )

    assert saved_snapshot == snapshot


def test_prompt_change_produces_new_hash(tmp_path):
    """Test that modifying a prompt changes its fingerprint."""

    prompt_file = tmp_path / "test_prompt.yaml"

    # First version of the prompt.
    prompt_file.write_text(
        'version: "1.0"\nsystem_prompt: "Classify emails"\n',
        encoding="utf-8",
    )

    # Save the first snapshot.
    original = create_snapshot(
        str(prompt_file),
        {"model": "gpt-4o-mini"},
        str(tmp_path / "original.json"),
    )

    # Modify the prompt instructions.
    prompt_file.write_text(
        'version: "1.0"\nsystem_prompt: "Classify emails carefully"\n',
        encoding="utf-8",
    )

    # Save another snapshot.
    modified = create_snapshot(
        str(prompt_file),
        {"model": "gpt-4o-mini"},
        str(tmp_path / "modified.json"),
    )

    # Even though the version number stayed the same,
    # the SHA-256 hashes should differ.
    assert original["prompt_sha256"] != modified["prompt_sha256"]