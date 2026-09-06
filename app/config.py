from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения."""

    app_name: str = 'Dance Competition System'
    app_description: str = 'Dance Competition System API'
    app_version: str = '0.1.0'
    database_url: str = 'sqlite+aiosqlite:///./dcs.db'
    model_config = SettingsConfigDict(env_file='.env', env_prefix='DCS_')


settings = Settings()
