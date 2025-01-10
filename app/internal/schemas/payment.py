from typing import Literal

from pydantic import BaseModel, NonNegativeFloat


class PaymentCreate(BaseModel):
    type: Literal["cash", "cashless"]
    amount: NonNegativeFloat


class PaymentSchema(PaymentCreate):
    id: int
