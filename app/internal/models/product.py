from typing import TYPE_CHECKING

from sqlalchemy import Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.internal.models import Base

if TYPE_CHECKING:
    from app.internal.models import InvoiceProductAssociation


class Product(Base):
    __tablename__ = "product"

    name: Mapped[str]
    price: Mapped[float] = mapped_column(
        Float(asdecimal=True, decimal_return_scale=2)
    )
    description: Mapped[str | None]
    invoices: Mapped[list["InvoiceProductAssociation"]] = relationship(
        back_populates="product")
