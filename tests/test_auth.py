from pprint import pprint
from random import choice

from httpx import AsyncClient, Headers

from app.config import API_PREFIX
from tests.conftest import test_users


async def test_register(ac: AsyncClient):
    for user_params in test_users:
        response = await ac.post(
            API_PREFIX + "/user/register", data=user_params)

        pprint(response.json())
        assert response.status_code == 201


async def test_register_with_same_login(ac: AsyncClient):
    response = await ac.post(
        API_PREFIX + "/user/register", data=choice(test_users))

    pprint(response.json())
    assert response.status_code == 409


async def test_register_short_password(ac: AsyncClient):
    user_params = choice(test_users).copy()
    user_params["password"] = user_params["password"][:5]
    response = await ac.post(
        API_PREFIX + "/user/register", data=user_params)

    pprint(response.json()["detail"][0]["msg"])
    assert response.status_code == 422


async def test_auth_and_get_token(ac: AsyncClient):
    user_params = choice(test_users)
    response = await ac.post(API_PREFIX + "/auth/jwt/login", data=dict(
        username=user_params["login"], password=user_params["password"]))

    token_data = response.json()
    pprint(token_data)
    assert response.status_code == 200
    assert token_data["access_token"]


async def test_invalid_auth_data(ac: AsyncClient):
    user_params = choice(test_users)
    response = await ac.post(API_PREFIX + "/auth/jwt/login", data=dict(
        username=user_params["login"],
        password=user_params["password"] + "0"))

    pprint(response.json())
    assert response.status_code == 401


async def test_unauthorized(ac: AsyncClient):
    response = await ac.get(API_PREFIX + "/user/details")

    pprint(response.json())
    assert response.status_code == 401


async def test_get_user_data(ac: AsyncClient, headers: Headers):
    response = await ac.get(
        API_PREFIX + "/user/details", headers=headers)

    pprint(response.json())
    assert response.status_code == 200


async def test_index_redirect(ac: AsyncClient):
    response = await ac.get("/")

    assert response.status_code == 307
