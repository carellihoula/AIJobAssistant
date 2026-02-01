from typing import Optional, List
from pydantic import BaseModel, EmailStr

class Experience(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None

class Education(BaseModel):
    degree: Optional[str] = None
    school: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class CVSchema(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None

    skills: List[str] = []
    experiences: List[Experience] = []
    education: List[Education] = []
