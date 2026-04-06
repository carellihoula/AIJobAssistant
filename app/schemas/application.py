from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class ApplicationCreate(BaseModel):
    job_id: UUID


class ApplicationStatusUpdate(BaseModel):
    status: str  # submitted | interview | rejected | offer


class ApplicationOut(BaseModel):
    id: UUID
    user_id: UUID
    job_id: UUID
    tailored_cv: Optional[dict] = None
    cover_letter: Optional[str] = None
    apply_type: str
    status: str
    form_data: Optional[dict] = None
    submitted_at: Optional[datetime] = None
    created_at: datetime
    notes: Optional[str] = None

    class Config:
        orm_mode = True