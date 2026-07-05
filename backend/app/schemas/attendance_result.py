"""Schémas Pydantic pour les résultats de présence calculés."""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AttendanceStatus


class AttendanceResultRead(BaseModel):
    """Représentation d'un résultat de présence renvoyée par l'API."""
    id: int
    student_id: int
    schedule_id: int
    result_date: date
    status: AttendanceStatus
    entry_time: datetime | None = None
    exit_time: datetime | None = None
    computed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComputeReportRead(BaseModel):
    """Bilan renvoyé après un déclenchement de calcul."""
    result_date: date
    students_processed: int
    sessions_per_student: int
    results_written: int
