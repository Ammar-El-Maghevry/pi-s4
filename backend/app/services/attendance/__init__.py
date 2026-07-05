"""
Paquet du moteur de calcul de présence.

- `intervals` : reconstruction des intervalles de présence (fonction pure).
- `engine`    : calcul du statut par séance selon le taux de chevauchement (pur).
- `service`   : orchestration lecture événements → calcul → écriture des résultats.
"""
from app.services.attendance.engine import SessionComputation, compute_session, session_window
from app.services.attendance.intervals import Interval, build_intervals
from app.services.attendance.service import (
    ComputeReport,
    compute_date,
    compute_student_date,
)

__all__ = [
    "Interval",
    "build_intervals",
    "SessionComputation",
    "compute_session",
    "session_window",
    "ComputeReport",
    "compute_date",
    "compute_student_date",
]
