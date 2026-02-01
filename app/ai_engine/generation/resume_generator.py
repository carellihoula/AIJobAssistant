"""
Generate CV text from structured data.
"""

from app.schemas.cv import CVSchema


def generate_cv_text(cv: CVSchema) -> str:
    """
    Generate a clean CV text from CVSchema.
    """
    text = f"{cv.full_name}\n{cv.email}\n\n"

    if cv.summary:
        text += f"{cv.summary}\n\n"

    text += "Skills:\n"
    text += ", ".join(cv.skills) + "\n\n"

    text += "Experience:\n"
    for exp in cv.experiences:
        text += f"- {exp.title} at {exp.company} ({exp.start_date} - {exp.end_date})\n"
        if exp.description:
            text += f"  {exp.description}\n"

    text += "\nEducation:\n"
    for edu in cv.education:
        text += f"- {edu.degree} at {edu.school} ({edu.start_date} - {edu.end_date})\n"

    return text
