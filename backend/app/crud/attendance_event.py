"""
Couche d'accès aux données pour les événements de présence.

Les événements sont la matière première du moteur de calcul : ils sont insérés
ici (manuellement en test, par la caméra en production) puis lus par le moteur
pour reconstruire les intervalles de présence.
"""
from datetime import date, datetime, time

from sqlalchemy.orm import Session

from app.models.attendance_event import AttendanceEvent
from app.schemas.attendance_event import AttendanceEventCreate


def create_event(db: Session, data: AttendanceEventCreate) -> AttendanceEvent:
    """
    Crée un événement de présence.

    Si `timestamp` n'est pas fourni, la valeur par défaut de la base
    (`func.now()`) s'applique.
    """
    values = data.model_dump(exclude_none=True)
    event = AttendanceEvent(**values)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def list_events(
    db: Session,
    student_id: int | None = None,
    on_date: date | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[AttendanceEvent]:
    """
    Liste les événements, filtrables par étudiant et par date.

    Le filtre par date sélectionne tous les événements dont l'horodatage tombe
    dans la journée demandée (de 00:00 à 23:59:59).
    """
    query = db.query(AttendanceEvent)
    if student_id is not None:
        query = query.filter(AttendanceEvent.student_id == student_id)
    if on_date is not None:
        start = datetime.combine(on_date, time.min)
        end = datetime.combine(on_date, time.max)
        query = query.filter(AttendanceEvent.timestamp.between(start, end))
    return (
        query.order_by(AttendanceEvent.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_events_for_student_on_date(
    db: Session, student_id: int, on_date: date
) -> list[AttendanceEvent]:
    """
    Retourne les événements d'un étudiant pour une date, triés chronologiquement.

    Utilisé par le moteur de calcul pour reconstruire les intervalles de présence.
    """
    start = datetime.combine(on_date, time.min)
    end = datetime.combine(on_date, time.max)
    return (
        db.query(AttendanceEvent)
        .filter(
            AttendanceEvent.student_id == student_id,
            AttendanceEvent.timestamp.between(start, end),
        )
        .order_by(AttendanceEvent.timestamp.asc())
        .all()
    )


def distinct_student_ids_with_events_on_date(db: Session, on_date: date) -> list[int]:
    """Retourne les identifiants des étudiants ayant au moins un événement ce jour-là."""
    start = datetime.combine(on_date, time.min)
    end = datetime.combine(on_date, time.max)
    rows = (
        db.query(AttendanceEvent.student_id)
        .filter(AttendanceEvent.timestamp.between(start, end))
        .distinct()
        .all()
    )
    return [row[0] for row in rows]
