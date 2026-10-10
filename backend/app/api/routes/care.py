from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.care import LabReport, LabInterpretation, DoctorProfile, Appointment
from app.models.user import User
from app.services.audit import record_audit_event
from app.schemas.care import DoctorProfileInput, AppointmentInput

router = APIRouter(tags=["Lab reports and plant doctors"])

class LabValuesInput(BaseModel):
    crop_name: str | None = Field(default=None, max_length=120)
    soil_ph: float | None = Field(default=None, ge=0, le=14)
    organic_carbon_pct: float | None = Field(default=None, ge=0, le=100)
    nitrogen: float | None = None
    phosphorus: float | None = None
    potassium: float | None = None
    nutrient_units: str | None = Field(default=None, max_length=120)

def build_lab_guidance(values: dict) -> dict:
    """Return cautious rule-based comments, not an AI diagnosis or fertilizer dose."""
    suggestions = []
    soil_ph = values.get("soil_ph")
    organic_carbon = values.get("organic_carbon_pct")
    if soil_ph is not None and soil_ph < 5.5:
        suggestions.append("The entered pH is strongly acidic. Confirm the lab method and discuss crop-specific soil amendment options with a local agronomist before applying lime or other amendments.")
    elif soil_ph is not None and soil_ph > 7.5:
        suggestions.append("The entered pH is alkaline. Availability of some nutrients can change at higher pH; review crop-specific interpretation with the laboratory or an agronomist before adding micronutrients.")
    elif soil_ph is not None:
        suggestions.append("The entered pH is between 5.5 and 7.5. Whether it is suitable depends on the crop, soil type and regional guidance; compare it with the laboratory's crop-specific target range.")
    if organic_carbon is not None and organic_carbon < 0.5:
        suggestions.append("The entered organic-carbon value is below 0.5%. Interpretation depends on soil type and local laboratory standards; ask about locally suitable organic-matter practices and cover crops.")
    elif organic_carbon is not None:
        suggestions.append("Organic carbon has been recorded. Compare it with the soil type, local benchmark and previous tests to understand change over time.")
    if any(values.get(name) is not None for name in ("nitrogen", "phosphorus", "potassium")):
        if not values.get("nutrient_units"):
            suggestions.append("N, P and K values were recorded, but units and extraction methods are missing. Do not interpret them or calculate fertilizer rates until the report units and local crop recommendation method are confirmed.")
        else:
            suggestions.append(f"N, P and K values were recorded using the supplied units ({values['nutrient_units']}). Compare them with the original laboratory's crop-specific interpretation; this tool does not calculate fertilizer doses.")
    if not suggestions:
        suggestions.append("Enter the measured pH, organic carbon or nutrient values printed on the report to receive limited rule-based comments. The uploaded document has not been automatically read by OCR.")
    return {"title": "Educational lab notes", "suggestions": suggestions,
            "limitations": "This is a transparent rule-based summary of manually entered values, not OCR, an AI lab diagnosis or a fertilizer prescription. Lab units, soil type, crop, growth stage and regional guidance matter.",
            "requires_expert_review": True}

_ALLOWED_DOC_TYPES = {"application/pdf", "image/jpeg", "image/png"}

@router.post("/lab-reports", status_code=201)
async def upload_lab_report(file: UploadFile = File(...), report_type: str = Form("soil_or_crop_lab"), notes: str = Form(""),
                            db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if file.content_type not in _ALLOWED_DOC_TYPES: raise HTTPException(status_code=415, detail="Upload a PDF, JPG or PNG lab report.")
    data = await file.read()
    if not data or len(data) > settings.max_upload_mb * 1024 * 1024: raise HTTPException(status_code=413, detail=f"File must be smaller than {settings.max_upload_mb} MB.")
    folder = settings.backend_path(settings.upload_dir) / "lab_reports"; folder.mkdir(parents=True, exist_ok=True)
    filename = Path(file.filename or "lab-report").name[:200]
    target = folder / f"{user.id}_{uuid4().hex}{Path(filename).suffix.lower()}"
    target.write_bytes(data)
    report = LabReport(owner_id=user.id, file_path=str(target), original_filename=filename, report_type=report_type, notes=notes.strip() or None)
    db.add(report); db.flush(); record_audit_event(db, user, "uploaded", "lab-reports", report.id, {"report_type": report_type}); db.commit(); db.refresh(report)
    return report_payload(report)

def report_payload(report: LabReport, interpretation: LabInterpretation | None = None) -> dict:
    return {"id": report.id, "original_filename": report.original_filename, "report_type": report.report_type,
            "notes": report.notes, "interpretation_status": report.interpretation_status, "created_at": report.created_at,
            "interpretation": ({"id": interpretation.id, "crop_name": interpretation.crop_name, "values": interpretation.values,
                "guidance": interpretation.guidance, "created_at": interpretation.created_at} if interpretation else None)}

@router.get("/lab-reports")
def list_lab_reports(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    reports = db.query(LabReport).filter(LabReport.owner_id == user.id).order_by(LabReport.created_at.desc()).all()
    result = []
    for report in reports:
        interpretation = db.query(LabInterpretation).filter(LabInterpretation.report_id == report.id, LabInterpretation.owner_id == user.id).order_by(LabInterpretation.created_at.desc()).first()
        result.append(report_payload(report, interpretation))
    return result


@router.post("/lab-reports/{report_id}/interpret", status_code=201)
def interpret_lab_report(report_id: int, payload: LabValuesInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    report = db.query(LabReport).filter(LabReport.id == report_id, LabReport.owner_id == user.id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Lab report not found in your account.")
    values = payload.model_dump(exclude_none=True, exclude={"crop_name"})
    guidance = build_lab_guidance(values)
    interpretation = LabInterpretation(report_id=report.id, owner_id=user.id, crop_name=payload.crop_name, values=values, guidance=guidance)
    report.interpretation_status = "values_reviewed"
    db.add(interpretation); db.flush(); record_audit_event(db, user, "interpreted_values", "lab-reports", report.id)
    db.commit(); db.refresh(interpretation)
    return {"id": interpretation.id, "report_id": report.id, "crop_name": interpretation.crop_name, "values": interpretation.values, "guidance": interpretation.guidance, "created_at": interpretation.created_at}

@router.post("/doctors/profile", status_code=201)
def create_doctor_profile(payload: DoctorProfileInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role not in {"doctor", "plant_pathologist", "agronomist"}: raise HTTPException(status_code=403, detail="Only doctor or agronomist accounts can publish a professional profile.")
    values = payload.model_dump()
    values["specialty"] = values["specialty"].strip()
    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == user.id).first()
    if profile:
        for key, value in values.items(): setattr(profile, key, value)
    else: profile = DoctorProfile(user_id=user.id, **values); db.add(profile)
    db.commit(); db.refresh(profile)
    return doctor_payload(profile)

def doctor_payload(profile: DoctorProfile) -> dict:
    return {"id": profile.id, "user_id": profile.user_id, "specialty": profile.specialty,
            "qualifications": profile.qualifications, "region": profile.region, "bio": profile.bio}

@router.get("/doctors")
def list_doctors(db: Session = Depends(get_db)):
    return [doctor_payload(d) for d in db.query(DoctorProfile).order_by(DoctorProfile.id.desc()).limit(200).all()]

@router.post("/appointments", status_code=201)
def request_appointment(payload: AppointmentInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not db.get(DoctorProfile, payload.doctor_id):
        raise HTTPException(status_code=404, detail="Plant doctor profile not found.")
    appointment = Appointment(requester_id=user.id, **payload.model_dump())
    db.add(appointment); db.flush(); record_audit_event(db, user, "requested", "doctor-appointments", appointment.id, {"doctor_id": payload.doctor_id}); db.commit(); db.refresh(appointment)
    return appointment_payload(appointment)

def appointment_payload(a: Appointment) -> dict:
    return {"id": a.id, "requester_id": a.requester_id, "doctor_id": a.doctor_id, "requested_time": a.requested_time,
            "message": a.message, "status": a.status, "created_at": a.created_at}

@router.get("/appointments")
def list_appointments(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Appointment)
    if user.role in {"doctor", "plant_pathologist", "agronomist"}:
        profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == user.id).first()
        if not profile: return []
        query = query.filter(Appointment.doctor_id == profile.id)
    else: query = query.filter(Appointment.requester_id == user.id)
    return [appointment_payload(a) for a in query.order_by(Appointment.created_at.desc()).all()]
