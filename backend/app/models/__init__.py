"""Import all SQLAlchemy models so metadata can create their tables."""
from app.models.user import User
from app.models.plant import Plant, PlantScan
from app.models.marketplace import Product, ProductReview
from app.models.care import LabReport, LabInterpretation, DoctorProfile, Appointment
from app.models.workspace import WorkspaceRecord
from app.models.order import Order
from app.models.scan_analysis import ScanAnalysis

__all__ = [
    "User", "Plant", "PlantScan", "Product", "ProductReview", "LabReport",
    "DoctorProfile", "Appointment", "LabInterpretation", "WorkspaceRecord", "Order", "ScanAnalysis",
]
