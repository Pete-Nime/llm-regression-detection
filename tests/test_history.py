import json
import sqlite3

from src import history


def test_model_config_saved_to_sqlite(monkeypatch, tmp_path):
    # Use a temporary database so our real history stays safe.
    test_db = tmp_path / "test_evaluations.db"
    monkeypatch.setattr(history, "DATABASE_PATH", test_db)

    # These are the AI settings we want to remember.
    config = {
        "model": "gpt-4o-mini",
        "temperature": 0,
        "max_retries": 3,
        "timeout": 30.0,
        "response_format": {"type": "json_object"},
    }

    # Save one evaluation with its model settings.
    history.save_evaluation_run(
        prompt_version="test-v3",
        model=config["model"],
        total_tests=15,
        correct=14,
        incorrect=1,
        accuracy_percent=93.33,
        average_summary_score=0.9,
        average_latency_ms=250.0,
        model_config=config,
    )

    # Read the configuration directly from SQLite.
    connection = sqlite3.connect(test_db)
    try:
        row = connection.execute(
            "SELECT model_config FROM evaluation_runs"
        ).fetchone()
    finally:
        connection.close()

    # Confirm the saved settings match the original settings.
    assert row is not None
    assert json.loads(row[0]) == config


def test_legacy_database_migration(monkeypatch, tmp_path):
    # Create a temporary database representing our old system.
    test_db = tmp_path / "legacy_evaluations.db"
    monkeypatch.setattr(history, "DATABASE_PATH", test_db)

    connection = sqlite3.connect(test_db)

    # The old table does not contain model_config.
    connection.execute("""
        CREATE TABLE evaluation_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            prompt_version TEXT NOT NULL,
            model TEXT NOT NULL,
            total_tests INTEGER NOT NULL,
            correct INTEGER NOT NULL,
            incorrect INTEGER NOT NULL,
            accuracy_percent REAL NOT NULL,
            average_summary_score REAL,
            average_latency_ms REAL
        )
    """)

    # Save one historical evaluation before migration.
    connection.execute("""
        INSERT INTO evaluation_runs (
            created_at, prompt_version, model,
            total_tests, correct, incorrect,
            accuracy_percent, average_summary_score,
            average_latency_ms
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "2026-10-01T10:00:00+00:00",
        "v1",
        "gpt-4o-mini",
        15,
        14,
        1,
        93.33,
        0.9,
        250.0
    ))

    connection.commit()
    connection.close()

    # Run our migration on the old database.
    history.initialize_database()

    connection = sqlite3.connect(test_db)

    columns = [
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(evaluation_runs)"
        )
    ]

    old_record = connection.execute("""
        SELECT prompt_version, accuracy_percent, model_config
        FROM evaluation_runs
        WHERE prompt_version = 'v1'
    """).fetchone()

    connection.close()

    # The new column exists.
    assert "model_config" in columns

    # The original evaluation is preserved.
    assert old_record[0] == "v1"
    assert old_record[1] == 93.33

    # Historical configuration remains unknown.
    assert old_record[2] is None