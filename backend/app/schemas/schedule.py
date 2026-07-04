"""Schémas Pydantic pour l'emploi du temps (lecture seule)."""
from datetime import time

from pydantic import BaseModel, ConfigDict

from app.models.enums import SessionType


class ScheduleRead(BaseModel):
    """Représentation d'un créneau de l'emploi du temps renvoyée par l'API."""
    id: int
    session_number: int
    name: str
    start_time: time
    end_time: time
    session_type: SessionType

    model_config = ConfigDict(from_attributes=True)
