from fastapi import FastAPI
from app.api.router import api_router
from app.db.session import engine, Base
from dotenv import load_dotenv
from app.core.config import settings

# Load environment variables
load_dotenv()

# Create all tables (for dev)
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME)

# Register global API router
app.include_router(api_router)


@app.get("/")
def health_check():
    return {"message": f"{settings.APP_NAME} operational!"}
