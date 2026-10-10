"""Plant repository and image-analysis endpoints."""
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.plant import Plant, PlantScan
from app.models.scan_analysis import ScanAnalysis
from app.models.user import User
from app.schemas.plants import PlantCreate
from app.services.audit import record_audit_event
from app.services.plant_model import predict_image
from app.services.treatments import general_guidance

router = APIRouter(tags=["Plants and AI scans"])
ALLOWED_PARTS = {"leaf", "stem", "fruit", "flower", "root", "whole_plant", "other"}
ALLOWED_ANALYSES = {"disease", "pest"}
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


def plant_payload(plant: Plant) -> dict:
    return {"id": plant.id, "name": plant.name, "species": plant.species, "crop_type": plant.crop_type,
            "location": plant.location, "notes": plant.notes, "created_at": plant.created_at}


def scan_payload(scan: PlantScan, analysis: ScanAnalysis | None = None) -> dict:
    return {
        "id": scan.id, "plant_id": scan.plant_id, "plant_part": scan.plant_part,
        "predicted_label": scan.predicted_label, "confidence": scan.confidence,
        "status": scan.status, "analysis_type": analysis.analysis_type if analysis else "disease",
        "analysis_id": analysis.id if analysis else None,
        "created_at": scan.created_at,
    }


@router.get("/plants")
def list_plants(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    plants = db.query(Plant).filter(Plant.owner_id == user.id).order_by(Plant.created_at.desc()).all()
    return [plant_payload(plant) for plant in plants]


@router.post("/plants", status_code=201)
def create_plant(payload: PlantCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    plant = Plant(owner_id=user.id, **payload.model_dump())
    db.add(plant)
    db.flush()
    record_audit_event(db, user, "created", "plants", plant.id)
    db.commit()
    db.refresh(plant)
    return plant_payload(plant)


@router.delete("/plants/{plant_id}", status_code=204)
def delete_plant(plant_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    plant = db.query(Plant).filter(Plant.id == plant_id, Plant.owner_id == user.id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant record not found.")
    record_audit_event(db, user, "deleted", "plants", plant.id)
    db.delete(plant)
    db.commit()


@router.post("/scans", status_code=201)
async def create_scan(
    image: UploadFile = File(...),
    plant_part: str = Form("leaf"),
    analysis_type: str = Form("disease"),
    plant_id: int | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=415, detail="Please upload a JPG, PNG or WebP image.")
    if plant_part not in ALLOWED_PARTS:
        raise HTTPException(status_code=422, detail="Choose a supported plant part.")
    if analysis_type not in ALLOWED_ANALYSES:
        raise HTTPException(status_code=422, detail="Choose disease or pest analysis.")
    if plant_id is not None and not db.query(Plant).filter(Plant.id == plant_id, Plant.owner_id == user.id).first():
        raise HTTPException(status_code=404, detail="The selected plant does not belong to your account.")

    contents = await image.read()
    if not contents or len(contents) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Image must be smaller than {settings.max_upload_mb} MB.")

    upload_folder = settings.backend_path(settings.upload_dir) / "scans"
    upload_folder.mkdir(parents=True, exist_ok=True)
    image_path = upload_folder / f"{user.id}_{uuid4().hex}.jpg"
    try:
        with Image.open(BytesIO(contents)) as image_to_check:
            image_to_check.verify()
        with Image.open(BytesIO(contents)) as decoded_image:
            decoded_image.convert("RGB").save(image_path, format="JPEG", quality=92)
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=422, detail="The uploaded file is not a valid image.")

    # The first supported model is a leaf-image classifier. Do not apply it to other plant parts.
    if plant_part != "leaf":
        prediction = None
        status = "unsupported_part"
    else:
        prediction = predict_image(image_path, analysis_type)
        if prediction is None:
            status = "model_not_trained"
        elif prediction[1] < settings.prediction_min_confidence:
            status = "low_confidence"
        else:
            status = "predicted"

    predicted_label, confidence = prediction if prediction else (None, None)
    if status in {"low_confidence", "unsupported_part", "model_not_trained"}:
        # Do not present an uncertain class as a diagnosis. The raw confidence remains recorded for review.
        predicted_label = None

    scan = PlantScan(
        owner_id=user.id,
        plant_id=plant_id,
        image_path=str(image_path),
        plant_part=plant_part,
        predicted_label=predicted_label,
        confidence=confidence,
        status=status,
    )
    db.add(scan)
    db.flush()
    analysis = ScanAnalysis(
        scan_id=scan.id,
        owner_id=user.id,
        analysis_type=analysis_type,
        predicted_label=predicted_label,
        confidence=confidence,
        status=status,
    )
    db.add(analysis)
    record_audit_event(db, user, "created", "plant-scans", scan.id,
                       {"analysis_type": analysis_type, "plant_part": plant_part, "status": status})
    db.commit()
    db.refresh(scan)
    db.refresh(analysis)

    guidance = general_guidance(predicted_label, analysis_type)
    if status == "unsupported_part":
        guidance = {
            "title": f"No trained {plant_part} classifier is installed",
            "summary": "The image was saved, but the current models have not been validated for this plant part. TreeRasa deliberately did not apply a leaf classifier to it.",
            "actions": [
                "If the symptoms are visible on a leaf, take a clear leaf photo and choose leaf analysis.",
                "Keep this image with the plant record and ask a qualified plant-health professional to review it.",
                "Build and validate a separate model with labelled examples of this plant part before enabling automatic predictions.",
            ],
            "safety_note": "No diagnosis or treatment prescription has been generated for this plant part.",
        }
    elif status == "low_confidence":
        guidance = {
            "title": "Result uncertain — please retake or seek review",
            "summary": "The model confidence was below TreeRasa's configured review threshold, so no predicted class is displayed as a diagnosis.",
            "actions": [
                "Retake a sharp image in natural light and include the affected area and nearby healthy tissue.",
                "Photograph the other side of the leaf and check whether the same symptoms occur on multiple plants.",
                "Ask a qualified agronomist or plant pathologist to review persistent symptoms.",
            ],
            "safety_note": "No treatment or fertilizer prescription has been generated from this uncertain result.",
        }
    return {"scan": scan_payload(scan, analysis), "analysis": scan_payload(scan, analysis), "guidance": guidance}


@router.get("/scans")
def list_scans(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    scans = db.query(PlantScan).filter(PlantScan.owner_id == user.id).order_by(PlantScan.created_at.desc()).limit(100).all()
    results = []
    for scan in scans:
        analysis = db.query(ScanAnalysis).filter(ScanAnalysis.scan_id == scan.id, ScanAnalysis.owner_id == user.id).order_by(ScanAnalysis.created_at.desc()).first()
        results.append(scan_payload(scan, analysis))
    return results
