from fastapi import FastAPI

from app.config import Settings

settings = Settings()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Dance Competition System API",
)
