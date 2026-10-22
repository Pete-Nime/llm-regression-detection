
import json
import os

from dotenv import load_dotenv
from openai import OpenAI

# Import our shared model configuration.
from src.config import get_model_config

# Import our Pydantic model for validating AI responses.
from src.models import ClassificationResult


# ============================================================
# LLM REGRESSION DETECTION
# Customer Email Classification
# ============================================================

def classify_email(
    email_text: str,
    prompt_config: dict
) -> ClassificationResult:
    """
    Classify a customer email using an OpenAI language model.

    Args:
        email_text:
            The customer's email or message.

        prompt_config:
            Instructions loaded from a YAML prompt file.

    Returns:
        ClassificationResult containing:
            - category
            - summary
    """

    # ========================================================
    # STEP 1 — Read the system prompt
    # ========================================================

    # Retrieve the system instructions from our YAML file.
    system_prompt = prompt_config["system_prompt"]

    # ========================================================
    # STEP 2 — Define JSON response instructions
    # ========================================================

    # Tell the AI exactly how to structure its response.
    json_instruction = """
    Return your answer as JSON using exactly this structure:

    {
        "category": "billing | technical | account | general",
        "summary": "short summary of the customer's issue"
    }

    Do not include markdown.
    Do not include extra text outside the JSON object.
    """

    # Combine the original prompt with JSON instructions.
    full_system_prompt = (
        system_prompt + "\n\n" + json_instruction
    )

    # ========================================================
    # STEP 3 — Load environment variables
    # ========================================================

    # Load the OPENAI_API_KEY from our .env file.
    # This happens only when classification is called.
    load_dotenv()

    # ========================================================
    # STEP 4 — Load shared model configuration
    # ========================================================

    # Read the settings from src/config.py.
    #
    # This prevents us from manually defining model
    # settings in multiple Python files.
    #
    # Our snapshot manager will also use this configuration.

    config = get_model_config()

    # ========================================================
    # STEP 5 — Create the OpenAI client
    # ========================================================

    # Use the shared reliability settings.
    #
    # max_retries:
    # Number of automatic retries for supported failures.
    #
    # timeout:
    # Request timeout configuration.

    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        max_retries=config["max_retries"],
        timeout=config["timeout"],
    )

    # ========================================================
    # STEP 6 — Send the classification request
    # ========================================================

    # Use the shared model and generation settings.
    response = client.chat.completions.create(
        model=config["model"],
        temperature=config["temperature"],

        # Require a JSON object response.
        response_format=config["response_format"],

        messages=[
            {
                "role": "system",
                "content": full_system_prompt,
            },
            {
                "role": "user",
                "content": email_text,
            },
        ],
    )

    # ========================================================
    # STEP 7 — Read the AI response
    # ========================================================

    # Extract the response content.
    raw_output = response.choices[0].message.content

    # Convert the JSON string into a Python dictionary.
    result = json.loads(raw_output)

    # ========================================================
    # STEP 8 — Validate the AI response
    # ========================================================

    # Pydantic validates the expected result structure.
    #
    # category:
    # billing, technical, account or general
    #
    # summary:
    # A short text description of the issue.

    return ClassificationResult(**result)
