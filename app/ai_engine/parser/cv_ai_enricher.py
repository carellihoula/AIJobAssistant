"""
AI-based CV enricher using OpenAI GPT-4.
Receives raw text from PDF/Image OCR and returns structured CVSchema.
"""

import re
from app.schemas.cv import CVParseResponse, CVSchema, Experience, Education
from typing import Optional
import json
from app.utils.prompts import generate_cv_parsing_prompt
from app.core.config import settings
from openai import OpenAI
from dotenv import load_dotenv
import logging

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


def enrich_cv_with_llm(raw_text: str, email: Optional[str] = None) -> CVParseResponse:
    """
    Call DEEPSEEK to extract structured CV information.
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

    # DEBUG
    # logging.info("===== LLM RAW OUTPUT =====")
    # logging.info(ai_output)
    # logging.info("===== END LLM OUTPUT =====")

    ai_output = _clean_json(ai_output)

    # Parse JSON safely
    try:
        ai_json = json.loads(ai_output)
        # print(ai_json)
    except json.JSONDecodeError:
        # fallback: empty CVSchema
        return CVParseResponse(
            is_cv=False,
            error="Invalid JSON returned by LLM"
        )

    if not ai_json.get("is_cv"):
        return CVParseResponse(
            is_cv=False,
            error=ai_json.get("error", "Document is not a CV")
        )

    # Build CVSchema object
    data_json = ai_json.get("data", {})

    cv = CVSchema(
        full_name=data_json.get("full_name"),
        email=email or data_json.get("email"),
        phone=data_json.get("phone"),
        location=data_json.get("location"),
        summary=data_json.get("summary"),
        skills=data_json.get("skills", []),
        experiences=[
            Experience(**exp) for exp in data_json.get("experience", [])
        ],
        education=[
            Education(**edu) for edu in data_json.get("education", [])
        ]
    )

    return CVParseResponse(
        is_cv=True,
        data=cv
    )

