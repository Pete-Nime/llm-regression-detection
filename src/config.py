
"""
Central configuration for the LLM Regression Detection system.

Purpose:
    Keep model settings in one place so the classifier
    and configuration snapshots use consistent values.
"""

from copy import deepcopy


# Settings used to create the OpenAI client.
OPENAI_CLIENT_CONFIG = {
    "max_retries": 3,
    "timeout": 30.0,
}

# Settings used for each classification request.
LLM_REQUEST_CONFIG = {
    "model": "gpt-4o-mini",
    "temperature": 0,
    "response_format": {
        "type": "json_object",
    },
}


def get_model_config() -> dict:
    """
    Return a fresh copy of all model settings.

    A deep copy prevents callers from accidentally changing
    the shared configuration.
    """
    return deepcopy({
        **OPENAI_CLIENT_CONFIG,
        **LLM_REQUEST_CONFIG,
    })
