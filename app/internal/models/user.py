from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.internal.models import Base

if TYPE_CHECKING:
    from app.internal.models import Invoice


class User(Base):
    __tablename__ = "user"

    name: Mapped[str] = mapped_column(String(40))
    login: Mapped[str] = mapped_column(
        String(40), unique=True, index=True
    )
    password: Mapped[bytes]
    invoices: Mapped[list["Invoice"]] = relationship(
        back_populates="user_owner")

    def __str__(self):
        return (
            f"{self.__class__.__name__}"
            f"(id={self.id}, name={self.name!r})")

    def __repr__(self):
        return str(self)
