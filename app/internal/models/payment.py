from typing import TYPE_CHECKING, Literal

from sqlalchemy import Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.internal.models import Base

if TYPE_CHECKING:
    from app.internal.models import Invoice


class Payment(Base):
    __tablename__ = "payment"

    type: Mapped[Literal["cash", "cashless"]]
    amount: Mapped[float] = mapped_column(
        Float(asdecimal=True, decimal_return_scale=2)
    )
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoice.id"))
    invoice: Mapped["Invoice"] = relationship(back_populates="payment")
