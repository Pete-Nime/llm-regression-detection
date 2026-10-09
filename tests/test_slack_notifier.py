
"""
Phase 10B: Slack Notification Unit Tests

Purpose:
Test Slack alerts without making real HTTP requests.

We test:
1. Successful PASS notification
2. Successful WARNING notification
3. Successful CRITICAL notification
4. Missing Slack webhook
5. Slack API failure
6. Missing comparison report
"""

import pytest
import requests

from src import slack_notifier


# ============================================================
# HELPER: CREATE A FAKE SLACK RESPONSE
# ============================================================

class FakeResponse:
    """Pretend to be a successful Slack HTTP response."""

    def raise_for_status(self):
        pass


# ============================================================
# TEST 1-3: SLACK ALERTS FOR EACH STATUS
# ============================================================

@pytest.mark.parametrize(
    "status, expected_icon",
    [
        ("PASS", "✅"),
        ("WARNING", "⚠️"),
        ("CRITICAL", "🚨"),
    ],
)
def test_slack_alert_success(
    monkeypatch,
    capsys,
    status,
    expected_icon,
):
    """Check that the correct message is sent to Slack."""

    sent_requests = []

    # Set a fake webhook, not a real secret.
    monkeypatch.setenv(
        "SLACK_WEBHOOK_URL",
        "https://example.invalid/fake-slack-webhook",
    )

    # Replace the real report loader with fake test data.
    monkeypatch.setattr(
        slack_notifier,
        "load_comparison_report",
        lambda: {
            "status": status,
            "regression_count": 2,
            "accuracy_delta": -5.0,
        },
    )

    # Replace requests.post to prevent network calls.
    def fake_post(url, json, timeout):
        sent_requests.append(
            {
                "url": url,
                "json": json,
                "timeout": timeout,
            }
        )
        return FakeResponse()

    monkeypatch.setattr(
        slack_notifier.requests,
        "post",
        fake_post,
    )

    # Run the real notification function.
    slack_notifier.send_slack_alert()

    # Check the fake request.
    assert len(sent_requests) == 1

    request = sent_requests[0]

    assert request["timeout"] == 10
    assert request["url"].startswith("https://example.invalid/")

    message = request["json"]["text"]

    assert expected_icon in message
    assert f"LLM Regression Detection: {status}" in message
    assert "Accuracy Delta:* -5.00%" in message
    assert "Regressions:* 2" in message

    assert "Slack alert sent successfully." in capsys.readouterr().out


# ============================================================
# TEST 4: MISSING SLACK WEBHOOK
# ============================================================

def test_missing_webhook(monkeypatch, capsys):
    """A missing webhook must stop the notification."""

    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)

    # If an HTTP request occurs, the test must fail.
    def unexpected_post(*args, **kwargs):
        pytest.fail("HTTP request should not be made.")

    monkeypatch.setattr(
        slack_notifier.requests,
        "post",
        unexpected_post,
    )

    with pytest.raises(SystemExit) as error:
        slack_notifier.send_slack_alert()

    assert error.value.code == 1
    assert "SLACK_WEBHOOK_URL is not set" in capsys.readouterr().out


# ============================================================
# TEST 5: SLACK API RETURNS AN ERROR
# ============================================================

def test_slack_api_failure(monkeypatch):
    """HTTP errors must not be silently ignored."""

    monkeypatch.setenv(
        "SLACK_WEBHOOK_URL",
        "https://example.invalid/fake-slack-webhook",
    )

    monkeypatch.setattr(
        slack_notifier,
        "load_comparison_report",
        lambda: {
            "status": "CRITICAL",
            "regression_count": 3,
            "accuracy_delta": -10.0,
        },
    )

    class FailedResponse:
        def raise_for_status(self):
            raise requests.HTTPError("Fake Slack server error")

    monkeypatch.setattr(
        slack_notifier.requests,
        "post",
        lambda *args, **kwargs: FailedResponse(),
    )

    with pytest.raises(requests.HTTPError):
        slack_notifier.send_slack_alert()


# ============================================================
# TEST 6: MISSING COMPARISON REPORT
# ============================================================

def test_missing_comparison_report(monkeypatch, tmp_path, capsys):
    """Missing report files must be detected."""

    missing_file = tmp_path / "comparison_report.json"

    monkeypatch.setattr(
        slack_notifier,
        "REPORT_PATH",
        missing_file,
    )

    with pytest.raises(SystemExit) as error:
        slack_notifier.load_comparison_report()

    assert error.value.code == 1
    assert "comparison_report.json was not found" in capsys.readouterr().out
