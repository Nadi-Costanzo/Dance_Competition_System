from importlib.metadata import PackageNotFoundError, version

from pydantic_settings import BaseSettings, SettingsConfigDict


def _resolve_app_version() -> str:
    """Возвращает значение version из метаданных приложения.

    При отсутствии установленного пакета (окружение не синхронизировано)
    возвращает '0.0.0+unknown', чтобы импорт конфига не падал.
    """
    try:
        return version('dcs')
    except PackageNotFoundError:  # окружение не синхронизировано
        return '0.0.0+unknown'


class Settings(BaseSettings):
    """Настройки приложения."""

    app_name: str = 'Dance Competition System'
    app_description: str = 'Dance Competition System API'
    app_version: str = _resolve_app_version()
    database_url: str = 'sqlite+aiosqlite:///./dcs.db'
    model_config = SettingsConfigDict(env_file='.env', env_prefix='DCS_')
    log_level: str = 'INFO'


settings = Settings()
