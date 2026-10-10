from pydantic import BaseModel, Field

class DoctorProfileInput(BaseModel):
    specialty: str = Field(min_length=2, max_length=160)
    qualifications: str | None = None
    region: str | None = None
    bio: str | None = None

class AppointmentInput(BaseModel):
    doctor_id: int = Field(gt=0)
    requested_time: str = Field(min_length=2, max_length=100)
    message: str | None = None
