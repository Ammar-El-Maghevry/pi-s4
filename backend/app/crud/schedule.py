"""
Couche d'accès aux données pour l'emploi du temps.

L'emploi du temps est peuplé au démarrage (voir app/initial_data.py). Seule
l'assignation de la caméra d'une séance est modifiable via l'API.
"""
from sqlalchemy.orm import Session

from app.models.schedule import Schedule
from app.schemas.schedule import ScheduleUpdate


def list_schedules(db: Session) -> list[Schedule]:
    """Retourne tous les créneaux, ordonnés par heure de début."""
    return db.query(Schedule).order_by(Schedule.start_time).all()


def get_schedule(db: Session, schedule_pk: int) -> Schedule | None:
    """Récupère un créneau par sa clé primaire."""
    return db.query(Schedule).filter(Schedule.id == schedule_pk).first()


def update_schedule(db: Session, schedule: Schedule, data: ScheduleUpdate) -> Schedule:
    """Assigne (ou retire) la caméra de la salle où se déroule la séance."""
    schedule.camera_id = data.camera_id
    db.commit()
    db.refresh(schedule)
    return schedule
