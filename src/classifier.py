import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from src.models import ClassificationResult


# ============================================================
# Load Environment Variables
# ============================================================

# Load OPENAI_API_KEY from the .env file.
load_dotenv()

# Create the OpenAI client.
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


# ============================================================
# Email Classification Function
# ============================================================

def classify_email(
    email_text: str,
    prompt_config: dict
) -> ClassificationResult:
    """
    Classify a customer email using an LLM.

    Input:
        email_text:
            The customer's email/message.

        prompt_config:
            Instructions loaded from our YAML prompt file.

    Output:
        ClassificationResult containing:
            - category
            - summary
    """

    # Get the system prompt from our YAML configuration.
    system_prompt = prompt_config["system_prompt"]

    # --------------------------------------------------------
    # JSON Instructions
    # --------------------------------------------------------
    # Because we are using response_format={"type": "json_object"},
    # we explicitly tell the model to return JSON.
    json_instruction = """
Return your answer as JSON using exactly this structure:

{
    "category": "billing | technical | account | general",
    "summary": "short summary of the customer's issue"
}

Do not include markdown.
Do not include extra text outside the JSON object.
"""

    # Combine our original prompt with the JSON instructions.
    full_system_prompt = system_prompt + "\n\n" + json_instruction

    # --------------------------------------------------------
    # Send request to OpenAI
    # --------------------------------------------------------
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,

        # Force the model to return a JSON object.
        response_format={"type": "json_object"},

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

    # --------------------------------------------------------
    # Read AI Response
    # --------------------------------------------------------

    # Get the JSON text returned by the AI.
    raw_output = response.choices[0].message.content

    # Convert JSON text into a Python dictionary.
    result = json.loads(raw_output)

    # --------------------------------------------------------
    # Validate Response
    # --------------------------------------------------------

    # Pydantic checks that:
    # category = billing / technical / account / general
    # summary = string
    return ClassificationResult(**result)