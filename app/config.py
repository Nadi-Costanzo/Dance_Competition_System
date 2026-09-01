from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Dance Competition System"
    database_url: str = "sqlite+aiosqlite:///./dcs.db"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="DCS_")
