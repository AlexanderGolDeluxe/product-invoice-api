from pydantic import BaseModel, NonNegativeFloat


class ProductCreate(BaseModel):
    name: str
    price: NonNegativeFloat
    description: str | None = None


class ProductSchema(ProductCreate):
    id: int
