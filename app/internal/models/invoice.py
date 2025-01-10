from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Computed, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.internal.models import Base

if TYPE_CHECKING:
    from app.internal.models import Payment, Product, User


class InvoiceProductAssociation(Base):
    __tablename__ = "invoice_product_association"
    __table_args__ = (
        UniqueConstraint(
            "invoice_id",
            "product_id",
            name="idx_unique_invoice_product"),
    )

    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoice.id", ondelete="CASCADE")
    )
    invoice: Mapped["Invoice"] = relationship(back_populates="products")
    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"))
    product: Mapped["Product"] = relationship(back_populates="invoices")
    quantity: Mapped[int] = mapped_column(default=1, server_default="1")
    unit_price: Mapped[float] = mapped_column(
        Float(asdecimal=True, decimal_return_scale=2)
    )
    total: Mapped[float] = mapped_column(Computed("unit_price * quantity"))


class Invoice(Base):
    __tablename__ = "invoice"

    products: Mapped[list[InvoiceProductAssociation]] = relationship(
        back_populates="invoice"
    )
    payment: Mapped["Payment"] = relationship(back_populates="invoice")
    total: Mapped[float] = mapped_column(
        Float(asdecimal=True, decimal_return_scale=2)
    )
    rest: Mapped[float] = mapped_column(
        Float(asdecimal=True, decimal_return_scale=2)
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    created_by: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user_owner: Mapped["User"] = relationship(back_populates="invoices")
