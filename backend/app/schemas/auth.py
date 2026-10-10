from pydantic import BaseModel, EmailStr, Field

class RegisterInput(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="farmer", pattern="^(farmer|gardener|vendor|doctor|plant_pathologist|nursery_manager|agricultural_extension_officer|forest_officer|research_scientist|delivery_partner|agronomist|student)$")

class LoginInput(BaseModel):
    email: EmailStr
    password: str
