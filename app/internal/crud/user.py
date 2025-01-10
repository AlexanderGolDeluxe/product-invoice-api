from fastapi import Form, HTTPException, status
from loguru import logger
from pydantic import SecretStr
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.internal.models import User
from app.internal.schemas import UserCreate
from app.utils import auth_jwt as auth_utils


@logger.catch(reraise=True)
def validate_creating_user(
        name: str = Form(min_length=3),
        login: str = Form(min_length=3),
        password: SecretStr = Form(min_length=8)
    ):
    """Validates auth data entered by user using the pydantic model"""
    return UserCreate(name=name, login=login, password=password)


@logger.catch(reraise=True)
async def create_user(session: AsyncSession, user_in: UserCreate):
    """
    Inserts new user into database (table `user`)
    or raises exception if user with the same login already exists
    """
    user = User(
        name=user_in.name,
        login=user_in.login,
        password=auth_utils.hash_password(user_in.password)
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"User with login «{user_in.login}» already exists. "
                "Please, choose another one"))
    finally:
        await session.close()

    return user


@logger.catch(reraise=True)
async def get_user_by_login(session: AsyncSession, login: str):
    """Retrieves record about user from database using specified login"""
    stmt = select(User).where(func.lower(User.login) == login.lower())
    return await session.scalar(stmt)
