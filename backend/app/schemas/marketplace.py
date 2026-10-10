from pydantic import BaseModel, Field

class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    category: str = Field(default="plant_care", max_length=80)
    description: str = Field(min_length=5)
    price: float = Field(gt=0)
    stock_quantity: int = Field(ge=0)
    unit: str = Field(default="item", max_length=40)

class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = None

class OrderCreate(BaseModel):
    quantity: int = Field(default=1, ge=1)
