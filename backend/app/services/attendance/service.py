"""
Orchestration du calcul de présence (couche entre le moteur pur et la base).

Rôle :
1. lire les événements d'un étudiant pour une date ;
2. reconstruire ses intervalles de présence (`intervals.build_intervals`) ;
3. calculer, pour chaque SÉANCE de l'emploi du temps, le statut (`engine`) ;
4. écrire les résultats via l'upsert idempotent.

Les pauses (`SessionType.BREAK`) sont ignorées : on ne calcule la présence que
pour les créneaux de type séance.
"""
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.crud import attendance_event as crud_event
from app.crud import attendance_result as crud_result
from app.crud import schedule as crud_schedule
from app.models.enums import SessionType
from app.services.attendance.engine import compute_session, session_window
from app.services.attendance.intervals import build_intervals


@dataclass
class ComputeReport:
    """Bilan d'un calcul de présence sur une date."""
    result_date: date
    students_processed: int
    sessions_per_student: int
    results_written: int


def _session_schedules(db: Session):
    """Retourne uniquement les créneaux de type séance, triés par heure de début."""
    return [s for s in crud_schedule.list_schedules(db) if s.session_type == SessionType.SESSION]


def compute_student_date(db: Session, student_id: int, on_date: date) -> int:
    """
    Calcule et enregistre la présence d'un étudiant pour toutes les séances d'une date.

    Retourne le nombre de résultats écrits. Ne valide pas la transaction :
    l'appelant s'en charge (permet de traiter plusieurs étudiants en un lot).
    """
    events = crud_event.get_events_for_student_on_date(db, student_id, on_date)
    intervals = build_intervals(events)

    written = 0
    for schedule in _session_schedules(db):
        window_start, window_end = session_window(
            on_date, schedule.start_time, schedule.end_time
        )
        computation = compute_session(intervals, window_start, window_end)
        crud_result.upsert_result(
            db,
            student_id=student_id,
            schedule_id=schedule.id,
            result_date=on_date,
            status=computation.status,
            entry_time=computation.entry_time,
            exit_time=computation.exit_time,
        )
        written += 1
    return written


def compute_date(
    db: Session, on_date: date, student_id: int | None = None
) -> ComputeReport:
    """
    Calcule la présence pour une date.

    - Si `student_id` est fourni : ne traite que cet étudiant (utile pour forcer
      un recalcul, y compris un étudiant sans événement = absent partout).
    - Sinon : traite tous les étudiants ayant au moins un événement ce jour-là.

    Idempotent : relancer le calcul met à jour les lignes existantes.
    """
    if student_id is not None:
        student_ids = [student_id]
    else:
        student_ids = crud_event.distinct_student_ids_with_events_on_date(db, on_date)

    sessions = _session_schedules(db)
    total_written = 0
    for sid in student_ids:
        total_written += compute_student_date(db, sid, on_date)

    db.commit()

    return ComputeReport(
        result_date=on_date,
        students_processed=len(student_ids),
        sessions_per_student=len(sessions),
        results_written=total_written,
    )
