def generate_ats_prompt(cv: dict, job: dict) -> str:
    experiences = cv.get("experiences") or []
    experience_text = " | ".join(
        f"{e.get('title', '')} @ {e.get('company', '')}: {(e.get('description') or '')[:200]}"
        for e in experiences[:3]
    )
    education_text = " | ".join(
        f"{e.get('degree', '')} - {e.get('school', '')}"
        for e in (cv.get("education") or [])[:2]
    )
    return f"""You are an expert ATS (Applicant Tracking System) specialist and HR consultant.
Evaluate how well this CV matches the job offer from an ATS perspective.
Perform SEMANTIC analysis: recognize synonyms, related technologies, and equivalent concepts.
NEVER invent skills or experiences not present in the CV.
Return ONLY a valid JSON object with no markdown fences.

CV:
- Summary: {cv.get("summary", "")}
- Skills: {", ".join(cv.get("skills") or [])}
- Experience: {experience_text}
- Education: {education_text}

JOB OFFER:
- Title: {job.get("title")}
- Company: {job.get("company")}
- Required skills: {", ".join(job.get("skills_required") or [])}
- Description: {(job.get("description") or "")[:1500]}

Return this JSON:
{{
  "ats_score": <integer 0-100>,
  "keyword_match_rate": <float 0.0-1.0, ratio of job keywords present in CV>,
  "present_keywords": [<keywords from job semantically present in CV>],
  "missing_keywords": [<important keywords from job absent from CV>],
  "format_issues": [<CV structural issues that hurt ATS parsing, empty list if none>],
  "improvement_suggestions": [<concrete actionable steps to improve ATS score>],
  "tailored_summary": "<rewritten CV summary 3-4 sentences, using ONLY skills and experiences present in the CV above — NEVER mention missing_keywords or technologies not in the CV>"
}}"""


def generate_cv_parsing_prompt(raw_text: str) -> str:
    prompt = f"""
You are a CV parser assistant. 

Your task:
1. Determine whether the provided text is a CV / resume.
2. If it is NOT a CV, return STRICT JSON matching this schema:
{{
    "is_cv": false,
    "data": null,
    "error": "The provided document is not a CV."
}}
3. If it IS a CV, return STRICT JSON matching this schema **AND include `"is_cv": true`**:
{{
    "is_cv": true,
    "data": {{
        "full_name": null,
        "email": null,
        "phone": null,
        "location": null,
        "summary": null,
        "skills": [],
        "experience": [],
        "education": []
    }},
    "error": null
}}

Fill in all available information in the `data` object.  
- full_name  
- email  
- phone  
- location  
- summary  
- skills (list of strings)  
- experience (list of objects: title, company, role, start_date, end_date, description)  
- education (list of objects: degree, school, start_date, end_date)

Do NOT invent any information. If a field is missing, set it to null or empty list.

EXAMPLE OUTPUT:
{{
    "is_cv": true,
    "data": {{
        "full_name": "Jane Doe",
        "email": "jane.doe@example.com",
        "phone": "+1 555 123 4567",
        "location": "New York, USA",
        "summary": "Experienced software engineer specializing in backend development and cloud architecture.",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
        "experience": [
            {{
                "title": "Senior Backend Engineer",
                "company": "Tech Corp",
                "role": "Backend Engineer",
                "start_date": "2021-06",
                "end_date": "2023-01",
                "description": "Developed scalable APIs using FastAPI and managed PostgreSQL databases."
            }}
        ],
        "education": [
            {{
                "degree": "Bachelor of Science in Computer Science",
                "school": "MIT",
                "start_date": "2016",
                "end_date": "2020"
            }}
        ]
    }},
    "error": null
}}

CV TEXT TO PARSE:
{raw_text}
"""
    return prompt
