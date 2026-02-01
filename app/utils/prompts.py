def generate_cv_parsing_prompt(raw_text: str) -> str:
    
    prompt = f"""
    You are a CV parser assistant. Extract all information from this CV text into strict JSON:
    - full_name
    - email
    - phone
    - location
    - summary
    - skills (list of strings)
    - experience (list of objects: company, role, start_date, end_date, description)
    - education (list of objects: degree, school, start_date, end_date)

    Do NOT invent any information. If a field is missing, return null or empty list.

    EXAMPLE OUTPUT:
    {{
        "full_name": "Jane Doe",
        "email": "jane.doe@example.com",
        "phone": "+1 555 123 4567",
        "location": "New York, USA",
        "summary": "Experienced software engineer specializing in backend development and cloud architecture.",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
        "experience": [
            {{
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
    }}

    CV TEXT TO PARSE:
    {raw_text}
    """
    return prompt
