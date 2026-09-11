from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from app.api.health import router as health_router
from app.config import settings
from app.constants import API_PREFIX
from app.database import async_engine, initialize_database
from app.logging_config import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Управляет ресурсами приложения при его запуске и остановке."""
    logger.info('Запуск приложения...')
    try:
        logger.info('Инициализация БД.')
        await initialize_database(async_engine)
        logger.info('БД успешно инициализирована.')
        yield
        logger.info('Завершение работы приложения.')
    except Exception:
        logger.exception('Приложение не запущено: ошибка инициализации БД.')
        raise
    finally:
        await async_engine.dispose()


app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    root_path=settings.root_path,
    lifespan=lifespan,
)

api_router = APIRouter(prefix=API_PREFIX)
api_router.include_router(health_router, tags=['Health'])

app.include_router(api_router)
