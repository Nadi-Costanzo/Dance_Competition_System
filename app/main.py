from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import async_engine, initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Управляет ресурсами приложения при его запуске и остановке."""
    try:
        await initialize_database(async_engine)
        yield
    finally:
        await async_engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version='0.1.0',
    description='Dance Competition System API',
    lifespan=lifespan,
)
