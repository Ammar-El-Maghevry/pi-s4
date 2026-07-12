"""
Routes de l'emploi du temps.

L'emploi du temps est fixe (inséré au démarrage) ; ces routes permettent au
frontend d'afficher les créneaux, d'assigner la caméra de la salle à chaque
séance, et au moteur de présence de s'y référer. Toutes les routes sont
protégées par l'authentification administrateur.
"""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.crud import camera as crud_camera
from app.crud import schedule as crud_schedule
from app.schemas.schedule import ScheduleCreate, ScheduleRead, ScheduleUpdate
from app.schemas.schedule_import import (
    ScheduleImportCreated,
    ScheduleImportResult,
    ScheduleImportRowError,
)
from app.services.schedules_import import ScheduleImportError, import_schedules

router = APIRouter(
    prefix="/schedules",
    tags=["Emploi du temps"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=list[ScheduleRead])
def list_schedules(db: Session = Depends(get_db)):
    """Liste tous les créneaux de l'emploi du temps (séances et pauses)."""
    return crud_schedule.list_schedules(db)


@router.post("", response_model=ScheduleRead, status_code=status.HTTP_201_CREATED)
def create_schedule(data: ScheduleCreate, db: Session = Depends(get_db)):
    """Crée un nouveau créneau ("class plan" ajouté depuis le frontend)."""
    return crud_schedule.create_schedule(db, data)


@router.post("/import", response_model=ScheduleImportResult)
async def import_schedules_route(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Importe l'emploi du temps d'une semaine complete depuis un fichier
    CSV/XLSX (une ligne par seance : name/teacher/room/day/start_time/
    end_time, class_name et fenetres de pointage optionnelles). Chaque
    seance valide est creee cote backend ; teacher/room/day/offsets sont
    renvoyes pour que le frontend les persiste localement (voir
    frontend/src/api/schedules.ts).
    """
    filename = file.filename or ""
    if not filename.lower().endswith((".csv", ".xlsx")):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Format non supporte : utilisez un fichier .csv ou .xlsx",
        )
    content = await file.read()
    try:
        result = await run_in_threadpool(import_schedules, db, content, filename)
    except ScheduleImportError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return ScheduleImportResult(
        total_rows=result.total_rows,
        created=[
            ScheduleImportCreated(
                schedule_id=c.schedule_id,
                name=c.name,
                teacher=c.teacher,
                room=c.room,
                day=c.day,
                start_time=c.start_time,
                end_time=c.end_time,
                check_in_offset_minutes=c.check_in_offset_minutes,
                check_out_offset_minutes=c.check_out_offset_minutes,
            )
            for c in result.created
        ],
        invalid=result.invalid,
        errors=[ScheduleImportRowError(row=e.row, reason=e.reason) for e in result.errors],
    )


@router.get("/{schedule_pk}", response_model=ScheduleRead)
def get_schedule(schedule_pk: int, db: Session = Depends(get_db)):
    """Récupère un créneau par son identifiant."""
    schedule = crud_schedule.get_schedule(db, schedule_pk)
    if schedule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Creneau introuvable")
    return schedule


@router.put("/{schedule_pk}", response_model=ScheduleRead)
def update_schedule(schedule_pk: int, data: ScheduleUpdate, db: Session = Depends(get_db)):
    """Assigne (ou retire) la caméra de la salle où se déroule cette séance."""
    schedule = crud_schedule.get_schedule(db, schedule_pk)
    if schedule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Creneau introuvable")

    if data.camera_id is not None and crud_camera.get_camera(db, data.camera_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera introuvable")

    return crud_schedule.update_schedule(db, schedule, data)


@router.delete("/{schedule_pk}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(schedule_pk: int, db: Session = Depends(get_db)):
    """Supprime un créneau de l'emploi du temps."""
    schedule = crud_schedule.get_schedule(db, schedule_pk)
    if schedule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Creneau introuvable")
    crud_schedule.delete_schedule(db, schedule)
