from fastapi import APIRouter
from app.api.routers import auth, users, cv

api_router = APIRouter()

# Include all sub-routers here
api_router.include_router(users.router)
api_router.include_router(cv.router)
api_router.include_router(auth.router)
