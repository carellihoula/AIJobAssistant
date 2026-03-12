from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    remote: Optional[str] = None
    contract: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    description: Optional[str] = None
    skills_required: list[str] = []
    url: Optional[str] = None
    apply_type: str
    match_score: float
    match_details: Optional[dict] = None
    source: str
    is_seen: bool
    is_saved: bool
    published_at: Optional[datetime] = None
    created_at: datetime

    # class Config:
    #     orm_mode = True


class JobListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    total: int
    jobs: list[JobOut]


class JobStatsOut(BaseModel):
    total: int
    seen: int
    saved: int
    avg_score: float
    by_source: dict[str, int]
    by_contract: dict[str, int]