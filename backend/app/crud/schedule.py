"""
Couche d'accès aux données pour l'emploi du temps.

L'emploi du temps est peuplé au démarrage (voir app/initial_data.py) et n'est,
à ce stade, accessible qu'en lecture.
"""
from sqlalchemy.orm import Session

from app.models.schedule import Schedule


def list_schedules(db: Session) -> list[Schedule]:
    """Retourne tous les créneaux, ordonnés par heure de début."""
    return db.query(Schedule).order_by(Schedule.start_time).all()


def get_schedule(db: Session, schedule_pk: int) -> Schedule | None:
    """Récupère un créneau par sa clé primaire."""
    return db.query(Schedule).filter(Schedule.id == schedule_pk).first()
