"""
Import centralisé de tous les modèles.

Importer ce module garantit qu'Alembic (autogenerate) voit bien toutes les
tables lors de la génération des migrations.
"""
from app.models.attendance_event import AttendanceEvent
from app.models.attendance_result import AttendanceResult
from app.models.camera import Camera
from app.models.enums import (
    AttendanceStatus,
    CrossingDirection,
    EventType,
    SessionType,
)
from app.models.schedule import Schedule
from app.models.snapshot import Snapshot
from app.models.student import Student
from app.models.user import User

__all__ = [
    "User",
    "Student",
    "Schedule",
    "AttendanceEvent",
    "AttendanceResult",
    "Snapshot",
    "Camera",
    "EventType",
    "SessionType",
    "AttendanceStatus",
    "CrossingDirection",
]
