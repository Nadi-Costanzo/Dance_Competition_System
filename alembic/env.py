import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.config import settings
from app.models.base import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
config.set_main_option('sqlalchemy.url', settings.database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Другие значения из конфигурации могут быть получены:
# my_important_option = config.get_main_option('my_important_option')


def run_migrations_offline() -> None:
    """выполняет миграции в 'offline' режиме.

    При этом не создается Engine, отсутствует соединение с БД.
    Выводит SQL-выражения в консоль.
    """
    url = config.get_main_option('sqlalchemy.url')
    assert url is not None, 'Не указан URL для подключения к БД'
    render_as_batch = url.startswith('sqlite')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
        render_as_batch=render_as_batch,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Выполняет миграции."""
    render_as_batch = connection.dialect.name == 'sqlite'
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=render_as_batch,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Для асинхронного выполнения миграций.

    Создает асинхронный движок и выполняет миграции в 'online' режиме.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
