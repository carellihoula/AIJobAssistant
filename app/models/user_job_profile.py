import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


class UserJobProfile(Base):
    __tablename__ = "user_job_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    target_role = Column(String, nullable=False)
    location = Column(String, nullable=False)
    remote_preference = Column(String, default="any")  # any|remote|on_site|hybrid
    contract_preference = Column(JSON, default=list)   # ["CDI", "CDD", ...]
    min_salary = Column(Integer, nullable=True)
    skills = Column(JSON, default=list)
    years_experience = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)