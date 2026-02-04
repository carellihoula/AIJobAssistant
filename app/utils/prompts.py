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
