"""
CV parsing logic using AI (LLM).
"""

from app.schemas.cv import CVSchema


def parse_cv_text(raw_text: str) -> CVSchema:
    """
    Convert raw CV text into structured CVSchema.
    NOTE: This is a placeholder.
    Replace this with an LLM call (OpenAI, Gemini, etc.).
    """

    # ⚠️ TEMPORARY SIMPLE LOGIC
    return CVSchema(
        full_name="Unknown",
        email="unknown@example.com",
        skills=[],
        experiences=[],
        education=[]
    )
