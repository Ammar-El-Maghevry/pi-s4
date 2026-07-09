"""
Routes de gestion des enseignants (CRUD + photo + présence).

Miroir de `routes/students.py`. Toutes les routes sont protégées : seul un
administrateur authentifié y accède (dépendance `get_current_user`).
"""
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.crud import teacher as crud_teacher
from app.schemas.teacher import (
    TeacherAttendanceRead,
    TeacherAttendanceSet,
    TeacherCreate,
    TeacherRead,
    TeacherUpdate,
)
from app.services import photos
from app.services.ai.face_embedding import (
    MultipleFacesDetected,
    NoFaceDetected,
    extract_single_face_embedding,
)

router = APIRouter(
    prefix="/teachers",
    tags=["Enseignants"],
    dependencies=[Depends(get_current_user)],
)


def _to_read(teacher) -> TeacherRead:
    """Convertit un modèle en schéma de lecture, en dérivant `has_face_embedding`."""
    data = TeacherRead.model_validate(teacher)
    data.has_face_embedding = teacher.face_embedding is not None
    return data


@router.get("", response_model=list[TeacherRead])
def list_teachers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: str | None = Query(None, description="Recherche par nom ou email"),
    db: Session = Depends(get_db),
):
    """Liste les enseignants avec pagination et recherche optionnelle."""
    return [_to_read(t) for t in crud_teacher.list_teachers(db, skip=skip, limit=limit, search=search)]


@router.post("", response_model=TeacherRead, status_code=status.HTTP_201_CREATED)
def create_teacher(data: TeacherCreate, db: Session = Depends(get_db)):
    """Ajoute un nouvel enseignant."""
    return _to_read(crud_teacher.create_teacher(db, data))


@router.get("/{teacher_pk}", response_model=TeacherRead)
def get_teacher(teacher_pk: int, db: Session = Depends(get_db)):
    """Récupère un enseignant par son identifiant interne."""
    teacher = crud_teacher.get_teacher(db, teacher_pk)
    if teacher is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enseignant introuvable")
    return _to_read(teacher)


@router.put("/{teacher_pk}", response_model=TeacherRead)
def update_teacher(teacher_pk: int, data: TeacherUpdate, db: Session = Depends(get_db)):
    """Modifie les informations d'un enseignant."""
    teacher = crud_teacher.get_teacher(db, teacher_pk)
    if teacher is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enseignant introuvable")
    return _to_read(crud_teacher.update_teacher(db, teacher, data))


@router.delete("/{teacher_pk}", status_code=status.HTTP_204_NO_CONTENT)
def delete_teacher(teacher_pk: int, db: Session = Depends(get_db)):
    """Supprime un enseignant."""
    teacher = crud_teacher.get_teacher(db, teacher_pk)
    if teacher is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enseignant introuvable")
    crud_teacher.delete_teacher(db, teacher)


@router.post("/{teacher_pk}/photo", response_model=TeacherRead)
async def upload_teacher_photo(
    teacher_pk: int, file: UploadFile = File(...), db: Session = Depends(get_db)
):
    """
    Enregistre la photo de reference d'un enseignant et calcule son embedding
    facial (InsightFace), pour qu'il puisse etre reconnu par la camera.
    """
    teacher = crud_teacher.get_teacher(db, teacher_pk)
    if teacher is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enseignant introuvable")

    if file.content_type not in photos.ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Format d'image non supporte (JPEG, PNG ou WebP uniquement)",
        )
    content = await file.read()
    if len(content) > photos.MAX_PHOTO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Photo trop volumineuse (8 Mo maximum)",
        )

    try:
        detected = await run_in_threadpool(extract_single_face_embedding, content)
    except NoFaceDetected as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except MultipleFacesDetected as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    relative_path = photos.save_teacher_photo(teacher_pk, content, file.content_type)
    teacher = crud_teacher.set_teacher_photo(db, teacher, relative_path, detected.embedding)
    return _to_read(teacher)


@router.get("/{teacher_pk}/photo")
def get_teacher_photo(teacher_pk: int, db: Session = Depends(get_db)):
    """Renvoie le fichier image de la photo de reference d'un enseignant."""
    teacher = crud_teacher.get_teacher(db, teacher_pk)
    if teacher is None or not teacher.photo_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo introuvable")
    path = photos.resolve_photo_path(teacher.photo_path)
    if path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo introuvable")
    return FileResponse(path)


@router.get("/attendance/today", response_model=list[TeacherAttendanceRead])
def get_attendance(
    on_date: date = Query(..., alias="date", description="Jour (AAAA-MM-JJ)"),
    db: Session = Depends(get_db),
):
    """Liste les statuts de présence des enseignants pour une date."""
    return [
        TeacherAttendanceRead(teacher_id=tid, attendance_date=on_date, is_present=present, source="")
        for tid, present in crud_teacher.get_attendance_for_date(db, on_date).items()
    ]


@router.put("/{teacher_pk}/attendance", response_model=TeacherAttendanceRead)
def set_attendance(
    teacher_pk: int,
    data: TeacherAttendanceSet,
    on_date: date = Query(..., alias="date", description="Jour (AAAA-MM-JJ)"),
    db: Session = Depends(get_db),
):
    """Positionne manuellement la présence d'un enseignant pour une date (bouton People)."""
    teacher = crud_teacher.get_teacher(db, teacher_pk)
    if teacher is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enseignant introuvable")
    record = crud_teacher.set_attendance(db, teacher_pk, on_date, data.is_present, source="manual")
    return record
