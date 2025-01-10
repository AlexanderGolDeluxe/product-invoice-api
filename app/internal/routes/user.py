from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import API_PREFIX
from app.configuration.db_helper import db_helper
from app.internal.crud.user import create_user, validate_creating_user
from app.internal.routes.auth import get_current_auth_user
from app.internal.schemas import UserCreate, UserSchema

router = APIRouter(prefix=API_PREFIX + "/user", tags=["user"])


@router.post("/register", response_model=UserSchema, status_code=201)
async def register_user(
        user_in: UserCreate = Depends(validate_creating_user),
        session: AsyncSession = Depends(
            db_helper.scoped_session_dependency)):

    return await create_user(session, user_in)


@router.get("/details", response_model=UserSchema)
async def get_user_data(
        user: UserSchema = Depends(get_current_auth_user)):

    return user
