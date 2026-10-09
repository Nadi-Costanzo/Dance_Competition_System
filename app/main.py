from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.api.health import router as health_router
from app.config import settings
from app.constants import API_PREFIX
from app.database import async_engine, initialize_database
from app.exceptions import (
    DEFAULT_ERROR_STATUS,
    ERROR_HTTP_STATUS,
    INTEGRITY_ERROR_CODES,
    BusinessError,
)
from app.logging_config import get_logger, setup_logging
from app.schemas.errors import ErrorResponse

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


@app.exception_handler(BusinessError)
async def business_error_handler(
    _request: Request, error: BusinessError
) -> JSONResponse:
    """Собирает кастомный ответ для ошибок бизнес-логики."""
    content = ErrorResponse(code=error.code, detail=error.detail).model_dump(
        mode='json'
    )
    return JSONResponse(content=content, status_code=error.status_code)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(
    _request: Request, error: IntegrityError
) -> JSONResponse:
    """Собирает кастомный ответ для ошибки IntegrityError."""
    _, _, part = str(error.orig).partition(':')
    found = INTEGRITY_ERROR_CODES.get(part.strip())
    if found is None:
        raise error
    code, detail = found
    content = ErrorResponse(code=code, detail=detail).model_dump(mode='json')
    status_code = ERROR_HTTP_STATUS.get(code, DEFAULT_ERROR_STATUS)
    return JSONResponse(content=content, status_code=status_code)
