"""
Routes du calcul de présence.

- Déclenchement du calcul d'une date (moteur de présence).
- Consultation des résultats calculés (par étudiant, date, séance).

Toutes les routes sont protégées par l'authentification administrateur.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.crud import attendance_result as crud_result
from app.crud import student as crud_student
from app.schemas.attendance_result import AttendanceResultRead, ComputeReportRead
from app.services.attendance import service as attendance_service

router = APIRouter(
    prefix="/attendance",
    tags=["Presence"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/compute", response_model=ComputeReportRead)
def compute_attendance(
    on_date: date = Query(..., alias="date", description="Jour a calculer (AAAA-MM-JJ)"),
    student_id: int | None = Query(
        None, description="Limiter le calcul a un etudiant (recalcul cible)"
    ),
    db: Session = Depends(get_db),
):
    """
    Déclenche le calcul de présence pour une date.

    Sans `student_id` : traite tous les étudiants ayant des événements ce jour-là.
    Avec `student_id` : ne recalcule que cet étudiant. Opération idempotente.
    """
    if student_id is not None and crud_student.get_student(db, student_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Etudiant introuvable")

    report = attendance_service.compute_date(db, on_date, student_id=student_id)
    return ComputeReportRead(
        result_date=report.result_date,
        students_processed=report.students_processed,
        sessions_per_student=report.sessions_per_student,
        results_written=report.results_written,
    )


@router.get("/results", response_model=list[AttendanceResultRead])
def list_results(
    student_id: int | None = Query(None, description="Filtrer par etudiant"),
    on_date: date | None = Query(None, alias="date", description="Filtrer par jour"),
    schedule_id: int | None = Query(None, description="Filtrer par seance"),
    skip: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Consulte les résultats de présence calculés, avec filtres cumulables."""
    return crud_result.list_results(
        db,
        student_id=student_id,
        on_date=on_date,
        schedule_id=schedule_id,
        skip=skip,
        limit=limit,
    )
