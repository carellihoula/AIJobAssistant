from uuid import UUID
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str | None = None
    password: str

class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None = None

    class Config:
        orm_mode = True
