from datetime import datetime
from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    NonNegativeFloat,
    NonNegativeInt)

from app.internal.schemas import (
    PaymentCreate, PaymentSchema, ProductCreate, UserSchema)

total_round = lambda value: round(value, 2)


class InvoiceProductAssociationCreate(ProductCreate):
    quantity: NonNegativeInt = 1


class InvoiceProductAssociationSchema(InvoiceProductAssociationCreate):
    unit_price: Annotated[NonNegativeFloat, AfterValidator(total_round)]
    total: Annotated[NonNegativeFloat, AfterValidator(total_round)]


class InvoiceCreate(BaseModel):
    products: list[InvoiceProductAssociationCreate]
    payment: PaymentCreate | None
    

class InvoiceSchema(BaseModel):
    id: int
    products: list[InvoiceProductAssociationSchema]
    payment: PaymentSchema | None
    total: Annotated[NonNegativeFloat, AfterValidator(total_round)]
    rest: Annotated[NonNegativeFloat, AfterValidator(total_round)]
    created_at: datetime
    created_by: UserSchema


class PaginationInfo(BaseModel):
    current_page: NonNegativeInt = 0
    limit: NonNegativeInt | None
    last_page: NonNegativeInt = 0


class InvoicesSchema(PaginationInfo):
    invoices: list[InvoiceSchema]
