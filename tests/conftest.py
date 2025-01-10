from typing import AsyncGenerator

import pytest
from asyncpg.exceptions import InvalidCatalogNameError
from httpx import ASGITransport, AsyncClient, Headers
from sqlalchemy import text

from app import create_app
from app.config import API_PREFIX, BASE_DIR, DB_URL
from app.configuration.db_helper import DatabaseHelper, db_helper
from app.internal.models import Base

DB_NAME_TEST = "test_db"
DB_URL_TEST = (
    f"{DB_URL}/{DB_NAME_TEST}" if DB_URL.startswith("postgresql")
    else DB_URL.replace(
        f"{BASE_DIR.stem}.sqlite3", f"{DB_NAME_TEST}.sqlite3"))

db_test = DatabaseHelper(DB_URL_TEST)

test_users = [
    dict(name="Test User", login="test", password="abcdefgh"),
    dict(name="Albert", login="albert", password="qwertyui"),
    dict(name="Bernard", login="bernard", password="12345678"),
    dict(name="Cheryl", login="cheryl", password="secretpassword")
]


async def create_db_test():
    async with db_helper.engine.connect() as conn:
        await conn.execution_options(isolation_level="AUTOCOMMIT")
        await conn.execute(text(f"CREATE DATABASE {DB_NAME_TEST}"))
        await conn.commit()
        await conn.execution_options(
            isolation_level=conn.default_isolation_level)


async def manage_db_models_test(is_create: bool):
    try:
        async with db_test.engine.begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all if is_create
                else Base.metadata.drop_all)
    except InvalidCatalogNameError:
        await create_db_test()
        await manage_db_models_test(is_create)


@pytest.fixture(autouse=True, scope='session')
async def prepare_database():
    await manage_db_models_test(True)
    yield
    await manage_db_models_test(False)
    await db_test.engine.dispose()


app = create_app()
app.dependency_overrides[db_helper.scoped_session_dependency] = (
    db_test.scoped_session_dependency)

@pytest.fixture(scope="session")
async def ac() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
            transport=ASGITransport(app),
            base_url="http://test"
        ) as ac:
        yield ac


@pytest.fixture(scope="session")
async def headers(ac: AsyncClient) -> Headers:
    user_params = test_users[0].copy()
    user_params["username"] = user_params.pop("login")
    del user_params["name"]
    response = await ac.post(
        API_PREFIX + "/auth/jwt/login", data=user_params)

    token_data = response.json()
    return Headers(dict(Authorization=
        f"{token_data['token_type']} {token_data['access_token']}"))
