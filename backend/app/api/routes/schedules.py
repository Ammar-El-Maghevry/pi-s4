"""
Routes de l'emploi du temps (lecture seule).

L'emploi du temps est fixe (inséré au démarrage) ; ces routes permettent au
frontend d'afficher les créneaux et au moteur de présence de s'y référer.
Toutes les routes sont protégées par l'authentification administrateur.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.crud import schedule as crud_schedule
from app.schemas.schedule import ScheduleRead

router = APIRouter(
    prefix="/schedules",
    tags=["Emploi du temps"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=list[ScheduleRead])
def list_schedules(db: Session = Depends(get_db)):
    """Liste tous les créneaux de l'emploi du temps (séances et pauses)."""
    return crud_schedule.list_schedules(db)


@router.get("/{schedule_pk}", response_model=ScheduleRead)
def get_schedule(schedule_pk: int, db: Session = Depends(get_db)):
    """Récupère un créneau par son identifiant."""
    schedule = crud_schedule.get_schedule(db, schedule_pk)
    if schedule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Creneau introuvable")
    return schedule
