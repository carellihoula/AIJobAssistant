import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, String, DateTime
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    google_id = Column(String, unique=True, nullable=True)
    reset_token = Column(String, nullable=True, unique=True)
    reset_token_expires = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User(email='{self.email}', full_name='{self.full_name}')>"