from typing import Annotated

from pydantic import (
    AfterValidator, BaseModel, ConfigDict, Field, SecretStr)


class UserBase(BaseModel):
    model_config = ConfigDict(strict=True)

    name: Annotated[str, Field(min_length=3, max_length=40)]
    login: Annotated[
        str,
        Field(min_length=3, max_length=40),
        AfterValidator(str.lower)
    ]
    password: Annotated[bytes, Field(exclude=True)]


class UserCreate(UserBase):
    password: Annotated[SecretStr, Field(min_length=8)]


class UserSchema(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class TokenInfo(BaseModel):
    access_token: str
    token_type: str = "Bearer"
