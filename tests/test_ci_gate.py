
"""
Phase 9A: Automated tests for our CI regression gate.

We test:
1. PASS     -> Exit code 0
2. WARNING  -> Exit code 0
3. CRITICAL -> Exit code 1

No OpenAI API calls are needed.
"""

import pytest

from src import ci_gate


# --------------------------------------------------
# TEST 1: PASS
# --------------------------------------------------
def test_ci_gate_pass(monkeypatch, capsys):

    # Pretend the comparison report returned PASS.
    fake_report = {
        "status": "PASS",
        "regression_count": 0,
        "accuracy_delta": 0.0,
    }

    # Replace the real report loader with fake data.
    monkeypatch.setattr(
        ci_gate,
        "load_comparison_report",
        lambda: fake_report,
    )

    # Our CI gate calls sys.exit(0).
    with pytest.raises(SystemExit) as result:
        ci_gate.run_ci_gate()

    # Exit 0 means success.
    assert result.value.code == 0

    # Check the printed message.
    output = capsys.readouterr().out
    assert "CI RESULT: PASS" in output


# --------------------------------------------------
# TEST 2: WARNING
# --------------------------------------------------
def test_ci_gate_warning(monkeypatch, capsys):

    fake_report = {
        "status": "WARNING",
        "regression_count": 1,
        "accuracy_delta": -2.0,
    }

    monkeypatch.setattr(
        ci_gate,
        "load_comparison_report",
        lambda: fake_report,
    )

    with pytest.raises(SystemExit) as result:
        ci_gate.run_ci_gate()

    # WARNING is allowed by our current policy.
    assert result.value.code == 0

    output = capsys.readouterr().out
    assert "PASS WITH WARNING" in output


# --------------------------------------------------
# TEST 3: CRITICAL
# --------------------------------------------------
def test_ci_gate_critical(monkeypatch, capsys):

    fake_report = {
        "status": "CRITICAL",
        "regression_count": 4,
        "accuracy_delta": -10.0,
    }

    monkeypatch.setattr(
        ci_gate,
        "load_comparison_report",
        lambda: fake_report,
    )

    with pytest.raises(SystemExit) as result:
        ci_gate.run_ci_gate()

    # Critical regressions must fail CI.
    assert result.value.code == 1

    output = capsys.readouterr().out
    assert "CI RESULT: FAIL" in output
