"""
LLM Regression Detection System
Phase 3B: Evaluation History

Stores evaluation runs in SQLite so that we can compare
prompt/model performance over time.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


# ============================================================
# DATABASE LOCATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

HISTORY_DIR = PROJECT_ROOT / "history"

DATABASE_PATH = HISTORY_DIR / "evaluations.db"


# ============================================================
# CREATE DATABASE
# ============================================================

def initialize_database():
    """
    Create the SQLite database and evaluation_runs table
    if they do not already exist.
    """

    HISTORY_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(DATABASE_PATH)

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS evaluation_runs (

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
        """
    )

    connection.commit()
    connection.close()


# ============================================================
# SAVE EVALUATION
# ============================================================

def save_evaluation_run(
    prompt_version,
    model,
    total_tests,
    correct,
    incorrect,
    accuracy_percent,
    average_summary_score,
    average_latency_ms
):
    """
    Save one evaluation run into SQLite.

    Example:

        Prompt v1
        GPT model
        15 tests
        14 correct
        93.33% accuracy

    becomes one database row.
    """

    initialize_database()

    connection = sqlite3.connect(DATABASE_PATH)

    cursor = connection.cursor()

    created_at = datetime.now(timezone.utc).isoformat()

    cursor.execute(
        """
        INSERT INTO evaluation_runs (
            created_at,
            prompt_version,
            model,
            total_tests,
            correct,
            incorrect,
            accuracy_percent,
            average_summary_score,
            average_latency_ms
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            created_at,
            prompt_version,
            model,
            total_tests,
            correct,
            incorrect,
            accuracy_percent,
            average_summary_score,
            average_latency_ms
        )
    )

    connection.commit()
    connection.close()


# ============================================================
# READ HISTORY
# ============================================================

def get_evaluation_history():
    """
    Return all previous evaluation runs.
    """

    initialize_database()

    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM evaluation_runs
        ORDER BY id ASC
        """
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# TEST DATABASE
# ============================================================

if __name__ == "__main__":

    initialize_database()

    print("Evaluation history database ready.")
    print(f"Database: {DATABASE_PATH}")