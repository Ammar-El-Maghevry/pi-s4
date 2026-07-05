"""
Schémas Pydantic pour les événements de présence bruts.

Ces événements représentent un passage détecté (entrée ou sortie). En phase de
test, ils sont saisis manuellement via l'API ; en production, ils seront émis
par le service caméra/inférence (phase future).
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import EventType


class AttendanceEventCreate(BaseModel):
    """
    Données pour enregistrer manuellement un événement.

    `timestamp` est optionnel : s'il n'est pas fourni, l'instant courant est
    utilisé (côté base de données). Cela permet de tester le système sans
    caméra en injectant des passages datés.
    """
    student_id: int
    event_type: EventType
    timestamp: datetime | None = None
    confidence: float | None = None
    camera_id: str | None = None


class AttendanceEventRead(BaseModel):
    """Représentation d'un événement renvoyée par l'API."""
    id: int
    student_id: int
    event_type: EventType
    timestamp: datetime
    confidence: float | None = None
    camera_id: str | None = None
    snapshot_id: int | None = None

    model_config = ConfigDict(from_attributes=True)
