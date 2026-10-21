"""
Phase 2 — Configuration Snapshot Manager

Purpose:
    Save an identifiable record of the prompt and model
    configuration used during an LLM evaluation.

Why:
    Help engineers trace configuration changes and reproduce
    evaluation runs.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml


def create_snapshot(
    prompt_path: str,
    model_config: dict,
    output_path: str,
) -> dict:
    """
    Create and save a configuration snapshot.

    Args:
        prompt_path: Location of our YAML prompt.
        model_config: Model settings used for evaluation.
        output_path: Destination JSON file.

    Returns:
        The snapshot as a Python dictionary.
    """

    # STEP 1: Locate the prompt file.
    prompt_file = Path(prompt_path)

    # STEP 2: Read its exact contents.
    # We hash the original bytes so even formatting changes
    # can be identified.
    prompt_bytes = prompt_file.read_bytes()

    # STEP 3: Generate the prompt's digital fingerprint.
    prompt_hash = hashlib.sha256(
        prompt_bytes
    ).hexdigest()

    # STEP 4: Parse YAML to extract its version.
    prompt_data = yaml.safe_load(prompt_bytes)

    if not isinstance(prompt_data, dict):
        raise ValueError(
            "Prompt YAML must contain a configuration dictionary."
        )

    # STEP 5: Build our snapshot.
    snapshot = {
        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "prompt_file": str(prompt_file),

        "prompt_version": prompt_data.get("version"),

        "prompt_sha256": prompt_hash,

        "model_config": model_config,
    }

    # STEP 6: Prepare the destination folder.
    destination = Path(output_path)

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # STEP 7: Save the snapshot as readable JSON.
    destination.write_text(
        json.dumps(snapshot, indent=2),
        encoding="utf-8",
    )

    # STEP 8: Return the result.
    return snapshot