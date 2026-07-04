"""
Requêtes d'agrégation pour le tableau de bord.

Regroupe les compteurs affichés sur la page d'accueil de l'administrateur :
effectif total, présents / absents du jour, derniers événements.
"""
from datetime import date

from sqlalchemy.orm import Session

from app.models.attendance_event import AttendanceEvent
from app.models.attendance_result import AttendanceResult
from app.models.enums import AttendanceStatus
from app.models.student import Student


def count_students(db: Session) -> int:
    """Effectif total d'étudiants enregistrés."""
    return db.query(Student).count()


def count_present_students(db: Session, on_date: date) -> int:
    """
    Nombre d'étudiants considérés présents ce jour-là.

    Un étudiant est « présent aujourd'hui » s'il a au moins une séance dont le
    statut calculé n'est pas `absent` (present ou late).
    """
    return (
        db.query(AttendanceResult.student_id)
        .filter(
            AttendanceResult.result_date == on_date,
            AttendanceResult.status != AttendanceStatus.ABSENT,
        )
        .distinct()
        .count()
    )


def recent_events(db: Session, limit: int = 10):
    """
    Retourne les derniers événements, chacun accompagné du nom de l'étudiant.

    Résultat : liste de tuples (AttendanceEvent, full_name).
    """
    return (
        db.query(AttendanceEvent, Student.full_name)
        .join(Student, AttendanceEvent.student_id == Student.id)
        .order_by(AttendanceEvent.timestamp.desc())
        .limit(limit)
        .all()
    )
