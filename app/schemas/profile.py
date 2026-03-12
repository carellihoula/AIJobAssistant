from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class UserJobProfileCreate(BaseModel):
    target_role: str
    location: str
    remote_preference: str = "any"
    contract_preference: list[str] = []
    min_salary: Optional[int] = None
    skills: list[str] = []
    years_experience: int = 0


class UserJobProfileOut(BaseModel):
    id: UUID
    user_id: UUID
    target_role: str
    location: str
    remote_preference: str
    contract_preference: list[str]
    min_salary: Optional[int] = None
    skills: list[str]
    years_experience: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True