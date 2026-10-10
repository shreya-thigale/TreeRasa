from pydantic import BaseModel, Field

class PlantCreate(BaseModel):
    """Validated fields accepted when a user creates a plant record."""
    name: str = Field(min_length=1, max_length=120)
    species: str | None = None
    crop_type: str | None = None
    location: str | None = None
    notes: str | None = None
