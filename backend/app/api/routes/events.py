"""
Routes des événements de présence (saisie manuelle + consultation).

Ces routes servent principalement à TESTER le système sans caméra : on injecte
des entrées/sorties datées, puis on déclenche le moteur de calcul. En
production, les événements seront produits par le service caméra/inférence.
Toutes les routes sont protégées par l'authentification administrateur.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.crud import attendance_event as crud_event
from app.crud import student as crud_student
from app.schemas.attendance_event import AttendanceEventCreate, AttendanceEventRead

router = APIRouter(
    prefix="/events",
    tags=["Evenements de presence"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=AttendanceEventRead, status_code=status.HTTP_201_CREATED)
def create_event(data: AttendanceEventCreate, db: Session = Depends(get_db)):
    """
    Enregistre manuellement un événement d'entrée ou de sortie pour un étudiant.

    Refuse la saisie si l'étudiant n'existe pas.
    """
    if crud_student.get_student(db, data.student_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Etudiant introuvable")
    return crud_event.create_event(db, data)


@router.get("", response_model=list[AttendanceEventRead])
def list_events(
    student_id: int | None = Query(None, description="Filtrer par etudiant"),
    on_date: date | None = Query(None, alias="date", description="Filtrer par jour (AAAA-MM-JJ)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Liste les événements, filtrables par étudiant et/ou par date."""
    return crud_event.list_events(
        db, student_id=student_id, on_date=on_date, skip=skip, limit=limit
    )
