import os
import sqlite3
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_alembic(db_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Запускает `uv run alembic <args>` на временной БД.

    Возвращает CompletedProcess. Вызывающий сам проверяет returncode
    и состояние БД.
    """
    env = os.environ.copy()
    env['DCS_DATABASE_URL'] = f'sqlite+aiosqlite:///{db_path.as_posix()}'

    return subprocess.run(
        ['uv', 'run', 'alembic', *args],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


def get_head_revision() -> str:
    """Возвращает ревизию HEAD из alembic."""
    # Используем фиктивный путь, т.к. мы не создаем БД
    result = run_alembic(Path('unused.db'), 'heads')
    assert result.returncode == 0, result.stderr
    for line in result.stdout.splitlines():
        if '(head)' in line:
            return line.split()[0]
    raise AssertionError(
        f'Не удалось получить ревизию HEAD, вывод alembic: {result.stdout}'
    )


def read_current_revision(db_path: Path) -> str | None:
    """Читает текущую revision из alembic_version.

    Если в таблице пусто возвращает None
    """
    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            'SELECT version_num FROM alembic_version LIMIT 1'
        ).fetchone()
    return row[0] if row else None


def test_fresh_database_reaches_head(tmp_path: Path) -> None:
    """Проверяет, что свежая база данных может быть обновлена до HEAD."""
    db_path = tmp_path / 'test.db'
    result = run_alembic(db_path, 'upgrade', 'head')
    assert result.returncode == 0, (
        f'Ошибка при обновлении БД до HEAD: {result.stderr}'
    )

    expected_revision = get_head_revision()
    current_revision = read_current_revision(db_path)
    assert current_revision == expected_revision, (
        f'Ожидалась ревизия {expected_revision}, получена {current_revision}'
    )


def test_roundtrip_upgrade_downgrade_upgrade(tmp_path: Path) -> None:
    """Upgrade -> downgrade -> upgrade возвращает БД к головной revision."""
    db_path = tmp_path / 'test.db'
    expected_revision = get_head_revision()

    # upgrade
    result = run_alembic(db_path, 'upgrade', 'head')
    assert result.returncode == 0, result.stderr
    assert read_current_revision(db_path) == expected_revision

    # downgrade до базы
    result = run_alembic(db_path, 'downgrade', 'base')
    assert result.returncode == 0, result.stderr
    assert read_current_revision(db_path) is None

    # повторный upgrade
    result = run_alembic(db_path, 'upgrade', 'head')
    assert result.returncode == 0, result.stderr
    assert read_current_revision(db_path) == expected_revision
