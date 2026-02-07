import uuid
from sqlalchemy import Column, Integer, ForeignKey, DateTime, JSON, String
from sqlalchemy.sql import func
from app.db.session import Base
from sqlalchemy.dialects.postgresql import UUID

class CV(Base):
    __tablename__ = "cvs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    version = Column(Integer, default=1)
    source = Column(String, default="upload")  # upload | manual | ai
    data = Column(JSON, nullable=False)  # CVSchema stored as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
