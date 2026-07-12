"""Schémas de réponse pour l'import en masse de l'emploi du temps."""
from pydantic import BaseModel


class ScheduleImportRowError(BaseModel):
    row: int
    reason: str


class ScheduleImportCreated(BaseModel):
    """
    Séance créée côté backend, accompagnée des champs "extras" (teacher/room/
    day/fenêtres de pointage) que le frontend doit persister localement — voir
    app/services/schedules_import.py.
    """
    schedule_id: int
    name: str
    teacher: str
    room: str
    day: str
    start_time: str
    end_time: str
    check_in_offset_minutes: int
    check_out_offset_minutes: int


class ScheduleImportResult(BaseModel):
    total_rows: int
    created: list[ScheduleImportCreated]
    invalid: int
    errors: list[ScheduleImportRowError]
