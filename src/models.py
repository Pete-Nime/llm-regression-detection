from typing import Literal
from pydantic import BaseModel, Field


class ClassificationResult(BaseModel):
    """
    Defines the exact structure that our LLM must return.
    """

    category: Literal[
        "billing",
        "technical",
        "account",
        "general"
    ] = Field(
        description="The customer email category"
    )

    summary: str = Field(
        description="A short summary of the customer's issue"
    )