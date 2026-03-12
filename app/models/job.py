import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    external_id = Column(String, nullable=True)
    source = Column(String, nullable=False)  # france_travail|adzuna|arbeitnow|remotive|indeed|glassdoor
    title = Column(String, nullable=True)
    company = Column(String, nullable=True)
    location = Column(String, nullable=True)
    remote = Column(String, nullable=True)
    contract = Column(String, nullable=True)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    skills_required = Column(JSON, default=list)
    url = Column(String, nullable=True)
    apply_type = Column(String, default="external")
    match_score = Column(Float, default=0.0)
    match_details = Column(JSON, nullable=True)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_seen = Column(Boolean, default=False)
    is_saved = Column(Boolean, default=False)

    applications = relationship("Application", back_populates="job")

    __table_args__ = (
        UniqueConstraint("user_id", "external_id", "source", name="uq_job_user_external_source"),
    )