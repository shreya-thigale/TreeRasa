from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Literal

Role = Literal["farmer", "vendor", "user"]

class RegisterIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Role
    phone: str | None = None
    location: str | None = None
    farm_name: str | None = None

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    phone: str | None = None
    location: str | None = None
    farm_name: str | None = None
    model_config = ConfigDict(from_attributes=True)

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class ProductIn(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    description: str = ""
    listing_type: Literal["produce", "supply"]
    category: str = Field(min_length=2, max_length=60)
    price: float = Field(ge=0)
    unit: str = "kg"
    stock: int = Field(ge=0)

class ProductOut(BaseModel):
    id: int
    seller_id: int
    title: str
    description: str
    listing_type: str
    category: str
    price: float
    unit: str
    stock: int
    seller_name: str = ""
    seller_role: str = ""
    seller_location: str | None = None
    average_rating: float = 0
    review_count: int = 0

class CheckoutItem(BaseModel):
    product_id: int
    quantity: int = Field(gt=0, le=10000)

class CheckoutIn(BaseModel):
    items: list[CheckoutItem] = Field(min_length=1)
    shipping_address: str = Field(min_length=5, max_length=500)

class OrderStatusIn(BaseModel):
    status: Literal["confirmed", "packed", "shipped", "delivered", "cancelled"]

class ReviewIn(BaseModel):
    order_item_id: int
    rating: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=2000)

class ProfileIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    phone: str | None = None
    location: str | None = None
    farm_name: str | None = None
