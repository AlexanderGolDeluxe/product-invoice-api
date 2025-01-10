from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, Form, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import SecretStr

from app.config import (
    API_PREFIX,
    AUTH_JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    AUTH_JWT_ALGORITHM,
    AUTH_JWT_PRIVATE_KEY,
    AUTH_JWT_PUBLIC_KEY
)
from app.configuration.db_helper import db_helper
from app.internal.crud.user import get_user_by_login

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=API_PREFIX + "/auth/jwt/login")


@logger.catch(reraise=True)
def encode_jwt(
        payload: dict,
        private_key: str = AUTH_JWT_PRIVATE_KEY,
        algorithm: str = AUTH_JWT_ALGORITHM,
        expire_minutes: int = AUTH_JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        expire_timedelta: timedelta | None = None
    ):
    """Encodes data to JWT token"""
    now = datetime.now(tz=timezone.utc)
    payload_to_encode = payload.copy()
    payload_to_encode.update(
        iat=now,
        exp=now + (
            timedelta(minutes=expire_minutes) if expire_timedelta is None
            else expire_timedelta))

    return jwt.encode(payload_to_encode, private_key, algorithm)


@logger.catch(reraise=True)
def decode_jwt(
        token: str,
        public_key: str = AUTH_JWT_PUBLIC_KEY,
        algorithm: str = AUTH_JWT_ALGORITHM
    ):
    """Decodes data from JWT token"""
    return jwt.decode(token, public_key, algorithms=[algorithm])


@logger.catch(reraise=True)
def hash_password(password: SecretStr | str):
    """Hashes password string into bytes"""
    if isinstance(password, SecretStr):
        password = password.get_secret_value()

    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())


@logger.catch(reraise=True)
def validate_password(password: SecretStr | str, hashed_password: bytes):
    """Compares password string with the hashed password"""
    if isinstance(password, SecretStr):
        password = password.get_secret_value()

    return bcrypt.checkpw(password.encode(), hashed_password)


@logger.catch(reraise=True)
def get_current_token_payload(token: str = Depends(oauth2_scheme)):
    """
    Retrieves data encrypted in JWT token
    or raises an exception about invalidity of the token
    """
    try:
        payload = decode_jwt(token=token)
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token error")

    return payload


@logger.catch(reraise=True)
async def validate_auth_user(
        username: str = Form(),
        password: SecretStr = Form(),
        session: AsyncSession = Depends(
            db_helper.scoped_session_dependency)
    ):
    """
    Checks username and password entered by user.
    Returns a record about the user from DB if the check is successful
    """
    logged_user = await get_user_by_login(session, username)
    if logged_user and validate_password(password, logged_user.password):
        return logged_user

    await session.close()
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid login or password")
