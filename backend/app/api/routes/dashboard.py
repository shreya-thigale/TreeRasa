from collections import Counter
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.plant import Plant, PlantScan
from app.models.marketplace import Product
from app.models.care import LabReport, Appointment

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # These values are calculated from this account's real database records.
    return {
        "plants": db.query(func.count(Plant.id)).filter(Plant.owner_id == user.id).scalar() or 0,
        "scans": db.query(func.count(PlantScan.id)).filter(PlantScan.owner_id == user.id).scalar() or 0,
        "products_listed": db.query(func.count(Product.id)).filter(Product.vendor_id == user.id).scalar() or 0,
        "lab_reports": db.query(func.count(LabReport.id)).filter(LabReport.owner_id == user.id).scalar() or 0,
        "appointments": db.query(func.count(Appointment.id)).filter(Appointment.requester_id == user.id).scalar() or 0,
        "trained_model_available": _model_available(),
    }

def _model_available() -> bool:
    from app.services.plant_model import load_model_bundle
    try: return load_model_bundle() is not None
    except Exception: return False


@router.get("/analytics")
def dashboard_analytics(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Build charts from this user's actual scan records; no demo values are inserted."""
    scans = db.query(PlantScan).filter(PlantScan.owner_id == user.id).order_by(PlantScan.created_at.asc()).all()
    today = datetime.now(timezone.utc).date()
    days = [(today - timedelta(days=offset)) for offset in range(13, -1, -1)]
    daily_counts = Counter(scan.created_at.date().isoformat() for scan in scans if scan.created_at)
    class_counts = Counter(scan.predicted_label for scan in scans if scan.predicted_label)
    status_counts = Counter(scan.status for scan in scans)
    return {
        "total_scans": len(scans),
        "predicted_scans": sum(1 for scan in scans if scan.status == "predicted"),
        "needs_review": sum(1 for scan in scans if scan.status in {"low_confidence", "unsupported_part", "model_not_trained"}),
        "scans_by_day": [{"date": day.isoformat(), "count": daily_counts.get(day.isoformat(), 0)} for day in days],
        "class_distribution": [{"label": label, "count": count} for label, count in class_counts.most_common(12)],
        "status_distribution": [{"label": label, "count": count} for label, count in status_counts.most_common()],
        "source": "account database records",
    }
