"""
AI-based CV enricher using OpenAI GPT-4.
Receives raw text from PDF/Image OCR and returns structured CVSchema.
"""

import re
from app.schemas.cv import CVSchema, Experience, Education
from typing import Optional
import json
from app.utils.prompts import generate_cv_parsing_prompt
from app.core.config import settings
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def _clean_json(text: str) -> str:
    """
    Remove markdown fences ```json ... ``` from LLM output.
    """
    text = text.strip()
    text = re.sub(r"^```json", "", text)
    text = re.sub(r"^```", "", text)
    text = re.sub(r"```$", "", text)
    return text.strip()


def enrich_cv_with_llm(raw_text: str, email: Optional[str] = None) -> CVSchema:
    """
    Call OpenAI GPT-4 to extract structured CV information.
    """
    prompt = generate_cv_parsing_prompt(raw_text)

    client = OpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

    # Call OpenAI ChatCompletion
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    # Get text output
    ai_output = response.choices[0].message.content

    # 🔍 DEBUG (IMPORTANT)
    print("===== LLM RAW OUTPUT =====")
    print(ai_output)
    print("===== END LLM OUTPUT =====")

    ai_output = _clean_json(ai_output)

    # Parse JSON safely
    try:
        ai_json = json.loads(ai_output)
    except json.JSONDecodeError:
        # fallback: empty CVSchema
        ai_json = {}

    # Build CVSchema object
    cv = CVSchema(
        full_name=ai_json.get("full_name") or "Unknown",
        email=email or ai_json.get("email"),
        phone=ai_json.get("phone"),
        location=ai_json.get("location"),
        summary=ai_json.get("summary"),
        skills=ai_json.get("skills", []),
        experiences=[
            Experience(**exp) for exp in ai_json.get("experience", [])
        ],
        education=[
            Education(**edu) for edu in ai_json.get("education", [])
        ]
    )

    return cv
