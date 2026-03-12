from fastapi import FastAPI
from app.api.v1.router import api_router
from app.api.v1 import jobs, applications, profile
from app.db.session import engine, Base
from dotenv import load_dotenv
from app.core.config import settings
from logging_config import LogLevels, configure_logging

# Load environment variables
load_dotenv()

# Create all tables (for dev)
Base.metadata.create_all(bind=engine)

configure_logging(LogLevels.info)

app = FastAPI(title=settings.APP_NAME)

# Existing routers
app.include_router(api_router)

# New routers
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(applications.router, prefix="/api/v1")
app.include_router(profile.router, prefix="/api/v1")


@app.get("/")
def health_check():
    return {"message": f"{settings.APP_NAME} operational!"}
