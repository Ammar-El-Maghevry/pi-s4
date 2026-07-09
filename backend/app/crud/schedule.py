"""
Couche d'accès aux données pour l'emploi du temps.

L'emploi du temps est peuplé au démarrage (voir app/initial_data.py). Seule
l'assignation de la caméra d'une séance est modifiable via l'API.
"""
from sqlalchemy.orm import Session

from app.models.enums import SessionType
from app.models.schedule import Schedule
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate


def list_schedules(db: Session) -> list[Schedule]:
    """Retourne tous les créneaux, ordonnés par heure de début."""
    return db.query(Schedule).order_by(Schedule.start_time).all()


def create_schedule(db: Session, data: ScheduleCreate) -> Schedule:
    """Crée un créneau ("class plan" créé depuis le frontend)."""
    schedule = Schedule(
        session_number=0,
        name=data.name,
        start_time=data.start_time,
        end_time=data.end_time,
        session_type=SessionType.SESSION,
        class_name=data.class_name,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


def get_schedule(db: Session, schedule_pk: int) -> Schedule | None:
    """Récupère un créneau par sa clé primaire."""
    return db.query(Schedule).filter(Schedule.id == schedule_pk).first()


def update_schedule(db: Session, schedule: Schedule, data: ScheduleUpdate) -> Schedule:
    """
    Assigne (ou retire) la caméra et/ou la classe de la séance.

    `exclude_unset=True` : un appel qui ne transmet que `camera_id` (ex.
    l'assignation de caméra depuis la page Class plans) ne doit pas écraser
    `class_name` avec None, et inversement.
    """
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(schedule, field, value)
    db.commit()
    db.refresh(schedule)
    return schedule


def delete_schedule(db: Session, schedule: Schedule) -> None:
    """Supprime un créneau (les résultats de présence associés sont supprimés en cascade)."""
    db.delete(schedule)
    db.commit()
