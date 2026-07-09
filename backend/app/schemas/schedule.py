"""Schémas Pydantic pour l'emploi du temps."""
from datetime import time

from pydantic import BaseModel, ConfigDict

from app.models.enums import SessionType
from app.schemas.camera import CameraRead


class ScheduleRead(BaseModel):
    """Représentation d'un créneau de l'emploi du temps renvoyée par l'API."""
    id: int
    session_number: int
    name: str
    start_time: time
    end_time: time
    session_type: SessionType
    camera_id: int | None = None
    camera: CameraRead | None = None

    model_config = ConfigDict(from_attributes=True)


class ScheduleUpdate(BaseModel):
    """Données pour assigner (ou retirer) la caméra d'une séance."""
    camera_id: int | None = None


class ScheduleCreate(BaseModel):
    """
    Données pour créer un créneau depuis le frontend ("class plan").

    Seuls `name`, `start_time`, `end_time` sont persistés côté backend ;
    teacher/room/day restent des "extras" gérés côté frontend (voir
    frontend/src/api/schedules.ts) tant que le modèle n'a pas ces colonnes.
    """
    name: str
    start_time: time
    end_time: time
