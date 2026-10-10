"""Small helper for recording account actions in the database audit log."""
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.workspace import WorkspaceRecord


def record_audit_event(
    db: Session,
    user: User,
    action: str,
    module_key: str,
    record_id: int | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """Add an audit row to the current transaction; the caller commits it with the action."""
    db.add(WorkspaceRecord(
        owner_id=user.id,
        module_key="audit-logs",
        title=f"{action}: {module_key}",
        data={
            "action": action,
            "module": module_key,
            "record_id": record_id,
            "actor_id": user.id,
            "actor_email": user.email,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            **(details or {}),
        },
    ))
