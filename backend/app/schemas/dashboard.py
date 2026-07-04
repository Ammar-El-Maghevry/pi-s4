"""Schémas Pydantic pour le tableau de bord administrateur."""
from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import EventType


class RecentEvent(BaseModel):
    """Un événement récent enrichi du nom de l'étudiant."""
    id: int
    student_id: int
    student_name: str
    event_type: EventType
    timestamp: datetime


class DashboardSummary(BaseModel):
    """Chiffres clés affichés sur le tableau de bord."""
    date: date
    total_students: int
    present_today: int
    absent_today: int
    recent_events: list[RecentEvent]
