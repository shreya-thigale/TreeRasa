"""Database-backed CRUD for TreeRasa's operational workspace modules.

Module definitions describe forms; they are not example records. All records returned
by these endpoints are saved in the configured database and scoped to the signed-in user.
"""
from datetime import datetime, timezone
from typing import Any
from io import BytesIO, StringIO
import csv
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.workspace import WorkspaceRecord
from app.services.audit import record_audit_event

router = APIRouter(prefix="/workspace", tags=["Workspace modules"])

# Field definitions are used to render consistent React forms. They do not pre-populate data.
MODULES: dict[str, dict[str, Any]] = {
    "farms": {"title": "Farm & field management", "description": "Keep track of farms, fields, crops and inspection routines.", "roles": ["farmer", "agronomist", "doctor"], "fields": [
        {"name":"owner_name","label":"Farm owner","type":"text"}, {"name":"area_acres","label":"Area (acres)","type":"number"}, {"name":"crop_type","label":"Main crop","type":"text"}, {"name":"irrigation_method","label":"Irrigation method","type":"text"}, {"name":"organic_certified","label":"Organic certification status","type":"text"}, {"name":"location","label":"Location / coordinates","type":"text"}, {"name":"last_inspection","label":"Last inspection date","type":"date"}]},
    "nurseries": {"title": "Nursery management", "description": "Record nursery species, seedling counts and care schedules.", "roles": ["farmer", "gardener", "vendor", "agronomist"], "fields": [
        {"name":"species","label":"Plant species","type":"text"}, {"name":"seedlings","label":"Seedling count","type":"number"}, {"name":"germination_rate","label":"Germination rate (%)","type":"number"}, {"name":"health_status","label":"Health status","type":"text"}, {"name":"pest_incidents","label":"Pest incidents","type":"number"}, {"name":"growth_stage","label":"Growth stage","type":"text"}, {"name":"care_schedule","label":"Care schedule","type":"text"}]},
    "pest-lifecycle": {"title": "Pest lifecycle intelligence", "description": "Track locally observed pest lifecycle stages and seasonal patterns.", "roles": ["farmer", "gardener", "agronomist", "doctor", "student"], "fields": [
        {"name":"pest_name","label":"Pest name","type":"text"}, {"name":"egg_stage_days","label":"Egg stage (days)","type":"number"}, {"name":"larval_stage_days","label":"Larval / nymph stage (days)","type":"number"}, {"name":"pupal_stage_days","label":"Pupal stage (days)","type":"number"}, {"name":"adult_stage_days","label":"Adult stage (days)","type":"number"}, {"name":"peak_season","label":"Peak season","type":"text"}, {"name":"host_plants","label":"Host plants","type":"text"}]},
    "environment": {"title": "Environmental monitoring", "description": "Enter readings from your own sensors or field observations.", "roles": ["farmer", "gardener", "agronomist", "doctor", "student"], "fields": [
        {"name":"temperature_c","label":"Temperature (°C)","type":"number"}, {"name":"humidity_pct","label":"Humidity (%)","type":"number"}, {"name":"soil_moisture_pct","label":"Soil moisture (%)","type":"number"}, {"name":"soil_ph","label":"Soil pH","type":"number"}, {"name":"rainfall_mm","label":"Rainfall (mm)","type":"number"}, {"name":"sunlight_hours","label":"Sunlight (hours)","type":"number"}, {"name":"wind_speed_kmh","label":"Wind speed (km/h)","type":"number"}, {"name":"leaf_wetness","label":"Leaf wetness / observation","type":"text"}]},
    "drone-surveys": {"title": "Drone surveillance", "description": "Record real survey missions and the results reported by your drone workflow.", "roles": ["farmer", "agronomist", "doctor", "forest_officer", "research_scientist"], "fields": [
        {"name":"flight_status","label":"Flight status","type":"text"}, {"name":"coverage_area_acres","label":"Coverage area (acres)","type":"number"}, {"name":"ndvi_index","label":"NDVI index","type":"number"}, {"name":"hotspot_count","label":"Hotspots found","type":"number"}, {"name":"captured_at","label":"Capture date","type":"date"}, {"name":"flight_notes","label":"Flight notes","type":"textarea"}]},
    "gis-observations": {"title": "GIS pest distribution", "description": "Store geolocated observations; a live map provider can be connected later.", "roles": ["farmer", "agronomist", "doctor", "forest_officer", "research_scientist"], "fields": [
        {"name":"observation_type","label":"Observation type","type":"text"}, {"name":"latitude","label":"Latitude","type":"number"}, {"name":"longitude","label":"Longitude","type":"number"}, {"name":"crop_type","label":"Crop / habitat","type":"text"}, {"name":"severity","label":"Severity","type":"text"}, {"name":"notes","label":"Observation notes","type":"textarea"}]},
    "soil-analyses": {"title": "Soil health", "description": "Save measured lab values and keep a traceable record of soil conditions.", "roles": ["farmer", "gardener", "agronomist", "doctor", "student"], "fields": [
        {"name":"sample_date","label":"Sample date","type":"date"}, {"name":"lab_name","label":"Laboratory","type":"text"}, {"name":"soil_ph","label":"Soil pH","type":"number"}, {"name":"organic_carbon_pct","label":"Organic carbon (%)","type":"number"}, {"name":"nitrogen","label":"Nitrogen (lab units)","type":"number"}, {"name":"phosphorus","label":"Phosphorus (lab units)","type":"number"}, {"name":"potassium","label":"Potassium (lab units)","type":"number"}, {"name":"moisture_pct","label":"Moisture (%)","type":"number"}, {"name":"notes","label":"Lab notes / questions","type":"textarea"}]},
    "crop-plans": {"title": "Crop protection planner", "description": "Create your own monitoring, irrigation and care schedule.", "roles": ["farmer", "gardener", "agronomist"], "fields": [
        {"name":"crop_name","label":"Crop / plant","type":"text"}, {"name":"activity","label":"Planned activity","type":"text"}, {"name":"scheduled_date","label":"Scheduled date","type":"date"}, {"name":"recurrence","label":"Repeat / frequency","type":"text"}, {"name":"status","label":"Status","type":"text"}, {"name":"notes","label":"Notes","type":"textarea"}]},
    "explainability": {"title": "AI explainability notes", "description": "Document model outputs, supporting observations and expert review.", "roles": ["farmer", "gardener", "agronomist", "doctor", "student", "research_scientist"], "fields": [
        {"name":"scan_id","label":"Scan record ID","type":"number"}, {"name":"predicted_label","label":"Model class","type":"text"}, {"name":"supporting_factors","label":"Observed factors","type":"textarea"}, {"name":"expert_review","label":"Expert review status","type":"text"}, {"name":"notes","label":"Review notes","type":"textarea"}]},
    "biodiversity": {"title": "Biodiversity monitoring", "description": "Record field observations of pollinators and other beneficial organisms.", "roles": ["farmer", "gardener", "agronomist", "forest_officer", "research_scientist", "student"], "fields": [
        {"name":"observation_date","label":"Observation date","type":"date"}, {"name":"beneficial_insects","label":"Beneficial insects observed","type":"text"}, {"name":"pollinator_activity","label":"Pollinator activity","type":"text"}, {"name":"bird_species_count","label":"Bird species count","type":"number"}, {"name":"soil_organisms","label":"Soil organisms observed","type":"text"}, {"name":"companion_plants","label":"Companion plants","type":"text"}, {"name":"notes","label":"Notes","type":"textarea"}]},
    "recommendations": {"title": "AI recommendation centre", "description": "Save recommendations and follow-up actions linked to your own observations.", "roles": ["farmer", "gardener", "agronomist", "doctor"], "fields": [
        {"name":"crop_name","label":"Crop / plant","type":"text"}, {"name":"issue","label":"Observed issue","type":"text"}, {"name":"recommendation_type","label":"Recommendation type","type":"text"}, {"name":"action","label":"Suggested action","type":"textarea"}, {"name":"schedule","label":"Follow-up schedule","type":"text"}, {"name":"status","label":"Status","type":"text"}]},
    "sdg15": {"title": "SDG 15 sustainability tracker", "description": "Track measurements your team actually records; unmeasured values are not fabricated.", "roles": ["farmer", "agronomist", "forest_officer", "research_scientist", "student"], "fields": [
        {"name":"reporting_period","label":"Reporting period","type":"text"}, {"name":"chemical_reduction_pct","label":"Chemical pesticide reduction (%)","type":"number"}, {"name":"organic_adoption_pct","label":"Organic treatment adoption (%)","type":"number"}, {"name":"crop_survival_pct","label":"Crop survival (%)","type":"number"}, {"name":"biodiversity_score","label":"Biodiversity indicator / score","type":"number"}, {"name":"soil_health_score","label":"Soil health indicator / score","type":"number"}, {"name":"notes","label":"Method / evidence notes","type":"textarea"}]},
    "learning-progress": {"title": "Learning centre progress", "description": "Keep your own learning and quiz progress records.", "roles": ["farmer", "gardener", "vendor", "doctor", "agronomist", "student", "research_scientist"], "fields": [
        {"name":"course_name","label":"Course / topic","type":"text"}, {"name":"completion_pct","label":"Completion (%)","type":"number"}, {"name":"quiz_score","label":"Quiz score (%)","type":"number"}, {"name":"certificate_issued","label":"Certificate status","type":"text"}, {"name":"notes","label":"Notes","type":"textarea"}]},
    "reports": {"title": "Reports register", "description": "Track report requests and exported reports generated from real TreeRasa records.", "roles": ["farmer", "gardener", "vendor", "doctor", "agronomist", "delivery_partner", "student", "forest_officer", "research_scientist"], "fields": [
        {"name":"report_type","label":"Report type","type":"text"}, {"name":"period","label":"Period","type":"text"}, {"name":"summary","label":"Summary / scope","type":"textarea"}, {"name":"file_name","label":"Export file name","type":"text"}, {"name":"status","label":"Status","type":"text"}]},
    "notifications": {"title": "Notification centre", "description": "Maintain notification records and their delivery status.", "roles": ["farmer", "gardener", "vendor", "doctor", "agronomist", "delivery_partner", "student"], "fields": [
        {"name":"message","label":"Message","type":"textarea"}, {"name":"channel","label":"Channel","type":"text"}, {"name":"priority","label":"Priority","type":"text"}, {"name":"status","label":"Status","type":"text"}]},
    "audit-logs": {"title": "Audit logs", "description": "Read-only history of workspace record changes performed through this module API.", "roles": ["farmer", "gardener", "vendor", "doctor", "agronomist", "delivery_partner", "student", "forest_officer", "research_scientist", "nursery_manager", "agricultural_extension_officer", "plant_pathologist"], "fields": [
        {"name":"action","label":"Action","type":"text"}, {"name":"module","label":"Module","type":"text"}, {"name":"record_id","label":"Record ID","type":"number"}, {"name":"actor_email","label":"Actor","type":"text"}, {"name":"occurred_at","label":"Occurred at","type":"text"}]},
    "settings": {"title": "Workspace settings", "description": "Save per-account preferences. Secret credentials must not be stored here.", "roles": ["farmer", "gardener", "vendor", "doctor", "agronomist", "delivery_partner", "student"], "fields": [
        {"name":"setting_name","label":"Setting name","type":"text"}, {"name":"setting_value","label":"Setting value","type":"text"}, {"name":"description","label":"Description","type":"textarea"}]},
}

class RecordInput(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    data: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = Field(default=None, max_length=4000)


def module_for(key: str, user: User) -> dict[str, Any]:
    module = MODULES.get(key)
    if not module:
        raise HTTPException(status_code=404, detail="Workspace module not found.")
    if user.role != "administrator" and user.role not in module["roles"]:
        raise HTTPException(status_code=403, detail="This module is not enabled for your account role.")
    return module


def record_payload(record: WorkspaceRecord) -> dict[str, Any]:
    return {"id": record.id, "module_key": record.module_key, "title": record.title,
            "data": record.data or {}, "notes": record.notes, "created_at": record.created_at,
            "updated_at": record.updated_at}


@router.get("/modules")
def list_modules(user: User = Depends(get_current_user)):
    """Return module form definitions filtered by role; no demo records are returned."""
    return [{"key": key, "title": value["title"], "description": value["description"], "fields": value["fields"]}
            for key, value in MODULES.items() if user.role == "administrator" or user.role in value["roles"]]

@router.get("/{module_key}/export")
def export_records(module_key: str, format: str = Query(default="csv", pattern="^(csv|xlsx|pdf)$"),
                   db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Export this account's real records in CSV, Excel or PDF format."""
    module_for(module_key, user)
    records = db.query(WorkspaceRecord).filter(WorkspaceRecord.owner_id == user.id, WorkspaceRecord.module_key == module_key).order_by(WorkspaceRecord.created_at.desc()).all()
    field_names = [field["name"] for field in MODULES[module_key]["fields"]]
    headers = ["id", "title", *field_names, "notes", "created_at"]
    rows = []
    for record in records:
        row = {"id": record.id, "title": record.title, "notes": record.notes or "", "created_at": record.created_at.isoformat() if record.created_at else ""}
        for field_name in field_names:
            value = (record.data or {}).get(field_name, "")
            row[field_name] = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else ("" if value is None else value)
        rows.append(row)
    filename = f"treerasa_{module_key}_{datetime.now(timezone.utc).date().isoformat()}.{format}"
    buffer = BytesIO()
    if format == "csv":
        text_buffer = StringIO(newline="")
        writer = csv.DictWriter(text_buffer, fieldnames=headers, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)
        return StreamingResponse(iter([text_buffer.getvalue().encode("utf-8-sig")]), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    if format == "xlsx":
        from openpyxl import Workbook
        workbook = Workbook(); sheet = workbook.active; sheet.title = module_key[:31]
        sheet.append(headers)
        for row in rows:
            sheet.append([row.get(header, "") for header in headers])
        sheet.freeze_panes = "A2"; sheet.auto_filter.ref = sheet.dimensions
        for column in sheet.columns:
            letter = column[0].column_letter
            sheet.column_dimensions[letter].width = min(36, max(12, max(len(str(cell.value or "")) for cell in column) + 2))
        workbook.save(buffer); buffer.seek(0)
        return StreamingResponse(buffer, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from xml.sax.saxutils import escape
    styles = getSampleStyleSheet()
    document = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=0.35*inch, leftMargin=0.35*inch, topMargin=0.35*inch, bottomMargin=0.35*inch)
    story = [Paragraph(f"TreeRasa — {escape(MODULES[module_key]['title'])}", styles["Title"]), Spacer(1, 10), Paragraph(f"Exported {datetime.now(timezone.utc).isoformat()} · {len(rows)} saved records", styles["Normal"]), Spacer(1, 12)]
    visible_headers = headers[:8] if len(headers) > 8 else headers
    table_data = [[Paragraph(escape(str(header)), styles["BodyText"]) for header in visible_headers]]
    for row in rows:
        table_data.append([Paragraph(escape(str(row.get(header, "")))[:180], styles["BodyText"]) for header in visible_headers])
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#e7f1e5")), ("TEXTCOLOR", (0,0), (-1,0), colors.HexColor("#244c32")), ("GRID", (0,0), (-1,-1), 0.35, colors.HexColor("#d8e2d6")), ("VALIGN", (0,0), (-1,-1), "TOP"), ("FONTSIZE", (0,0), (-1,-1), 7), ("BOTTOMPADDING", (0,0), (-1,-1), 5), ("TOPPADDING", (0,0), (-1,-1), 5)]))
    story.append(table); document.build(story); buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}"'})

@router.get("/{module_key}/records")
def list_records(module_key: str, q: str | None = Query(default=None, max_length=120), limit: int = Query(default=100, ge=1, le=250),
                 db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    module_for(module_key, user)
    query = db.query(WorkspaceRecord).filter(WorkspaceRecord.owner_id == user.id, WorkspaceRecord.module_key == module_key)
    if q:
        query = query.filter(WorkspaceRecord.title.ilike(f"%{q.strip()}%"))
    return [record_payload(record) for record in query.order_by(WorkspaceRecord.created_at.desc()).limit(limit).all()]

@router.post("/{module_key}/records", status_code=201)
def create_record(module_key: str, payload: RecordInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    module = module_for(module_key, user)
    if module_key == "audit-logs":
        raise HTTPException(status_code=405, detail="Audit log entries are generated by the system and cannot be edited manually.")
    allowed_fields = {field["name"] for field in module["fields"]}
    unknown = set(payload.data) - allowed_fields
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown field(s): {', '.join(sorted(unknown))}")
    record = WorkspaceRecord(owner_id=user.id, module_key=module_key, title=payload.title.strip(), data=payload.data, notes=payload.notes)
    db.add(record)
    db.flush()
    record_audit_event(db, user, "created", module_key, record.id)
    db.commit(); db.refresh(record)
    return record_payload(record)

@router.patch("/{module_key}/records/{record_id}")
def update_record(module_key: str, record_id: int, payload: RecordInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    module = module_for(module_key, user)
    if module_key == "audit-logs":
        raise HTTPException(status_code=405, detail="Audit log entries are read-only.")
    allowed_fields = {field["name"] for field in module["fields"]}
    unknown = set(payload.data) - allowed_fields
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown field(s): {', '.join(sorted(unknown))}")
    record = db.query(WorkspaceRecord).filter(WorkspaceRecord.id == record_id, WorkspaceRecord.owner_id == user.id,
        WorkspaceRecord.module_key == module_key).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found in your workspace.")
    record.title = payload.title.strip(); record.data = payload.data; record.notes = payload.notes
    record.updated_at = datetime.now(timezone.utc)
    record_audit_event(db, user, "updated", module_key, record.id)
    db.commit(); db.refresh(record)
    return record_payload(record)

@router.delete("/{module_key}/records/{record_id}", status_code=204)
def delete_record(module_key: str, record_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    module_for(module_key, user)
    if module_key == "audit-logs":
        raise HTTPException(status_code=405, detail="Audit log entries are read-only.")
    record = db.query(WorkspaceRecord).filter(WorkspaceRecord.id == record_id, WorkspaceRecord.owner_id == user.id,
        WorkspaceRecord.module_key == module_key).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found in your workspace.")
    record_audit_event(db, user, "deleted", module_key, record.id)
    db.delete(record); db.commit()
