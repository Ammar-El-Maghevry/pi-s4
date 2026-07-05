"""
Couche d'accès aux données pour les résultats de présence calculés.

Le moteur écrit ici le statut par (étudiant, séance, date). L'upsert respecte la
contrainte d'unicité et rend le recalcul **idempotent** : relancer le calcul
d'une date met à jour les lignes existantes au lieu d'en créer de nouvelles.
"""
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.models.attendance_result import AttendanceResult
from app.models.enums import AttendanceStatus


def upsert_result(
    db: Session,
    *,
    student_id: int,
    schedule_id: int,
    result_date: date,
    status: AttendanceStatus,
    entry_time: datetime | None,
    exit_time: datetime | None,
) -> AttendanceResult:
    """
    Insère ou met à jour le résultat d'une (étudiant, séance, date).

    Ne valide pas la transaction (`commit`) : l'appelant regroupe les écritures
    et valide une seule fois. Utilise `flush` pour rendre la ligne visible dans
    la même session.
    """
    existing = (
        db.query(AttendanceResult)
        .filter(
            AttendanceResult.student_id == student_id,
            AttendanceResult.schedule_id == schedule_id,
            AttendanceResult.result_date == result_date,
        )
        .first()
    )

    if existing is not None:
        existing.status = status
        existing.entry_time = entry_time
        existing.exit_time = exit_time
        # Datetime AVEC fuseau : la colonne est timestamptz, un utcnow() naïf
        # serait interprété dans le fuseau de la session (décalage silencieux).
        existing.computed_at = datetime.now(timezone.utc)
        db.flush()
        return existing

    result = AttendanceResult(
        student_id=student_id,
        schedule_id=schedule_id,
        result_date=result_date,
        status=status,
        entry_time=entry_time,
        exit_time=exit_time,
    )
    db.add(result)
    db.flush()
    return result


def list_results(
    db: Session,
    student_id: int | None = None,
    on_date: date | None = None,
    schedule_id: int | None = None,
    skip: int = 0,
    limit: int = 500,
) -> list[AttendanceResult]:
    """Liste les résultats de présence, filtrables par étudiant, date et séance."""
    query = db.query(AttendanceResult)
    if student_id is not None:
        query = query.filter(AttendanceResult.student_id == student_id)
    if on_date is not None:
        query = query.filter(AttendanceResult.result_date == on_date)
    if schedule_id is not None:
        query = query.filter(AttendanceResult.schedule_id == schedule_id)
    return (
        query.order_by(
            AttendanceResult.result_date.desc(),
            AttendanceResult.schedule_id.asc(),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )
