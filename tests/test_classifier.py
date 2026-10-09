"""
Phase 10F — OpenAI Classifier Reliability Tests

Purpose:
Verify our classifier configures API retries and timeouts
without making real OpenAI API calls.
"""

import json
from unittest.mock import MagicMock

from src import classifier


def test_classifier_retry_configuration(monkeypatch):
    """
    Check that the OpenAI client uses:
    - 3 retries
    - 30-second timeout
    """

    # Step 1: Create a fake OpenAI client.
    fake_client = MagicMock()

    # Step 2: Create a fake AI response.
    fake_response = MagicMock()
    fake_response.choices[0].message.content = json.dumps({
        "category": "billing",
        "summary": "Customer needs help with an invoice",
    })

    fake_client.chat.completions.create.return_value = fake_response

    # Step 3: Replace the real OpenAI client with our fake.
    fake_openai = MagicMock(return_value=fake_client)

    monkeypatch.setattr(classifier, "OpenAI", fake_openai)

    # Step 4: Run the classifier using a sample email.
    result = classifier.classify_email(
        email_text="I need help with my invoice.",
        prompt_config={
            "system_prompt": "Classify customer emails."
        },
    )

    # Step 5: Verify production reliability settings.
    fake_openai.assert_called_once_with(
        api_key=classifier.os.getenv("OPENAI_API_KEY"),
        max_retries=3,
        timeout=30.0,
    )

    # Step 6: Verify the classifier returned valid data.
    assert result.category == "billing"
    assert result.summary == "Customer needs help with an invoice"

    # Step 7: Verify the fake API was called once.
    fake_client.chat.completions.create.assert_called_once()