from __future__ import annotations

import os
import re
from collections.abc import AsyncGenerator, Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import app.models  # noqa: F401
from app.core.config import get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db_session
from app.main import create_app
from app.models.admin_user import AdminUser
from app.models.attachment import Attachment
from app.models.enums import AdminRole, ReportStatus, SubmitMode
from app.models.report import Report
from app.models.user import User

# Keep security-related test settings deterministic and fast.
os.environ.setdefault("ADMIN_JWT_SECRET", "integration-test-secret-0123456789abcdef")
os.environ.setdefault("ADMIN_PASSWORD_HASH_ITERATIONS", "1000")
get_settings.cache_clear()

_DB_NAME_RE = re.compile(r"^[A-Za-z0-9_]+$")


@pytest.fixture(scope="session")
def test_database_url() -> str:
    explicit = os.getenv("TEST_DATABASE_URL")
    if explicit:
        test_url = explicit
    else:
        base_url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://aerotrust:aerotrust@localhost:5432/aerotrust",
        )
        parsed = make_url(base_url)
        database_name = parsed.database or "aerotrust"
        test_url = parsed.set(database=f"{database_name}_test").render_as_string(hide_password=False)

    _ensure_database_exists(test_url)
    return test_url


def _ensure_database_exists(test_database_url: str) -> None:
    test_url = make_url(test_database_url)
    database_name = test_url.database
    if not database_name or not _DB_NAME_RE.fullmatch(database_name):
        raise RuntimeError(
            "Invalid test database name. Set TEST_DATABASE_URL with a safe DB name, e.g. aerotrust_test.",
        )

    admin_url = _to_sync_url(test_url.set(database="postgres"))
    engine = create_engine(
        admin_url.render_as_string(hide_password=False),
        isolation_level="AUTOCOMMIT",
        future=True,
    )
    try:
        with engine.connect() as connection:
            exists = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": database_name},
            ).scalar()
            if not exists:
                connection.execute(text(f'CREATE DATABASE "{database_name}"'))
    finally:
        engine.dispose()


def _to_sync_url(url: URL) -> URL:
    if url.drivername == "postgresql+asyncpg":
        return url.set(drivername="postgresql+psycopg")
    if url.drivername == "postgresql":
        return url.set(drivername="postgresql+psycopg")
    if url.drivername.startswith("postgresql+"):
        return url.set(drivername="postgresql+psycopg")
    raise RuntimeError("Integration tests require a PostgreSQL DATABASE_URL/TEST_DATABASE_URL.")


@pytest.fixture(scope="session", autouse=True)
def prepare_test_database(test_database_url: str) -> None:
    sync_url = _to_sync_url(make_url(test_database_url))
    engine = create_engine(sync_url.render_as_string(hide_password=False), future=True)
    try:
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
    finally:
        engine.dispose()


@pytest_asyncio.fixture
async def test_engine(test_database_url: str):
    engine = create_async_engine(
        test_database_url,
        pool_pre_ping=True,
        poolclass=NullPool,
    )
    yield engine
    await engine.dispose()


@pytest.fixture
def session_factory(test_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture(autouse=True)
async def clear_database(session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[None, None]:
    table_names = ", ".join(f'"{table.name}"' for table in Base.metadata.sorted_tables)
    async with session_factory() as session:
        await session.execute(text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"))
        await session.commit()

    yield


@pytest.fixture
def app(session_factory: async_sessionmaker[AsyncSession]):
    app = create_app()

    async def _override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db_session] = _override_get_db_session
    yield app
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http_client:
        yield http_client


@pytest_asyncio.fixture
async def seeded_data(session_factory: async_sessionmaker[AsyncSession]) -> dict[str, Any]:
    now = datetime(2026, 4, 20, 12, 0, tzinfo=UTC)

    admin_password = "AdminPass123!"
    resolver_password = "ResolverPass123!"

    async with session_factory() as session:
        admin = AdminUser(
            email="admin@example.com",
            password_hash=hash_password(admin_password),
            role=AdminRole.ADMIN,
            zone=None,
            is_active=True,
        )
        resolver = AdminUser(
            email="resolver@example.com",
            password_hash=hash_password(resolver_password),
            role=AdminRole.RESOLVER,
            zone="process",
            is_active=True,
        )
        session.add_all([admin, resolver])

        author_open = User(
            telegram_id=1001,
            telegram_username="open_author",
            telegram_first_name="Open",
            telegram_last_name="Author",
            is_authorized=True,
        )
        author_anon = User(
            telegram_id=1002,
            telegram_username="anon_author",
            telegram_first_name="Anon",
            telegram_last_name="Author",
            is_authorized=True,
        )
        session.add_all([author_open, author_anon])
        await session.flush()

        reports: list[Report] = [
            Report(
                public_number="AERO-0001",
                submit_mode=SubmitMode.OPEN,
                category="safety",
                zone="process",
                status=ReportStatus.NEW,
                text="Open report in process zone",
                author_user_id=author_open.id,
                created_at=now - timedelta(days=3),
                updated_at=now - timedelta(days=3),
            ),
            Report(
                public_number="AERO-0002",
                submit_mode=SubmitMode.ANONYMOUS,
                category="quality",
                zone="process",
                status=ReportStatus.NEW,
                text="Anonymous report in process zone",
                author_user_id=author_anon.id,
                created_at=now - timedelta(days=2),
                updated_at=now - timedelta(days=2),
            ),
            Report(
                public_number="AERO-0003",
                submit_mode=SubmitMode.OPEN,
                category="finance",
                zone="finance",
                status=ReportStatus.IN_PROGRESS,
                text="Finance report in progress",
                author_user_id=author_open.id,
                created_at=now - timedelta(days=2),
                updated_at=now - timedelta(days=1, hours=12),
            ),
            Report(
                public_number="AERO-0004",
                submit_mode=SubmitMode.OPEN,
                category="safety",
                zone="finance",
                status=ReportStatus.CLOSED,
                text="Closed finance report",
                author_user_id=author_open.id,
                created_at=now - timedelta(days=1, hours=6),
                updated_at=now - timedelta(days=1, hours=1),
                closed_at=now - timedelta(days=1, hours=1),
            ),
            Report(
                public_number="AERO-0005",
                submit_mode=SubmitMode.OPEN,
                category="hr",
                zone="process",
                status=ReportStatus.CLOSED,
                text="Closed process report",
                author_user_id=author_open.id,
                created_at=now - timedelta(hours=20),
                updated_at=now - timedelta(hours=18),
                closed_at=now - timedelta(hours=18),
            ),
        ]
        session.add_all(reports)
        await session.flush()

        session.add(
            Attachment(
                report_id=reports[0].id,
                file_name="evidence.pdf",
                file_type="application/pdf",
                file_path="/tmp/evidence.pdf",
                file_size=1024,
            ),
        )
        await session.commit()

    return {
        "admin": {
            "email": "admin@example.com",
            "password": admin_password,
        },
        "resolver": {
            "email": "resolver@example.com",
            "password": resolver_password,
        },
        "report_ids": {
            "process_open": 1,
            "process_anonymous": 2,
            "finance_in_progress": 3,
            "finance_closed": 4,
            "process_closed": 5,
        },
    }


@pytest_asyncio.fixture
async def auth_headers(
    client: AsyncClient,
) -> Callable[[str, str], Awaitable[dict[str, str]]]:
    async def _login(email: str, password: str) -> dict[str, str]:
        response = await client.post(
            "/admin/auth/login",
            json={"email": email, "password": password},
        )
        assert response.status_code == 200
        access_token = response.json()["access_token"]
        return {"Authorization": f"Bearer {access_token}"}

    return _login
