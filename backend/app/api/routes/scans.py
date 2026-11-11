from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.session import get_db
from app.api.deps import current_user
from app.models.user import User
from app.models.scan import PlantScan
from app.services.inference import predict_plant
from app.core.config import settings

router = APIRouter(prefix="/scans", tags=["Plant scans"])
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}

@router.post("")
async def create_scan(file: UploadFile = File(...), crop_name: str | None = None,
                      db: Session = Depends(get_db), user: User = Depends(current_user)):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(415, "Upload a JPG, PNG or WEBP image.")
    image = await file.read()
    if len(image) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"Image must be under {settings.max_upload_mb} MB.")
    result = predict_plant(image, file.filename, crop_name)
    scan = PlantScan(user_id=user.id, crop_name=crop_name or result.get("crop_name"),
        predicted_disease=result.get("predicted_disease", "Not analyzed"), confidence=result.get("confidence"),
        recommendations=result.get("recommendations", ""), status=result.get("status", "model_not_configured"),
        image_data=image, image_mime=file.content_type)
    db.add(scan); db.commit(); db.refresh(scan)
    return scan_out(scan)

def scan_out(s: PlantScan):
    return {"id": s.id, "crop_name": s.crop_name, "predicted_disease": s.predicted_disease,
            "confidence": s.confidence, "recommendations": s.recommendations, "status": s.status,
            "image_url": f"/api/scans/{s.id}/image" if s.image_data else None,
            "created_at": s.created_at.isoformat()}

@router.get("/{scan_id}/image")
def scan_image(scan_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    scan = db.get(PlantScan, scan_id)
    if not scan or scan.user_id != user.id or not scan.image_data:
        raise HTTPException(404, "Scan image not found.")
    return Response(content=scan.image_data, media_type=scan.image_mime or "application/octet-stream",
                    headers={"Cache-Control": "private, max-age=3600"})

@router.get("/mine")
def my_scans(db: Session = Depends(get_db), user: User = Depends(current_user)):
    scans = db.scalars(select(PlantScan).where(PlantScan.user_id == user.id).order_by(PlantScan.created_at.desc())).all()
    return [scan_out(s) for s in scans]
