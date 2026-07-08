"""
Routes de gestion des étudiants (CRUD + recherche).

Toutes ces routes sont protégées : seul un administrateur authentifié y accède
(dépendance `get_current_user`).
"""
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.crud import student as crud_student
from app.models.user import User
from app.schemas.student import StudentCreate, StudentRead, StudentUpdate
from app.services import photos
from app.services.ai.face_embedding import (
    MultipleFacesDetected,
    NoFaceDetected,
    extract_single_face_embedding,
)

router = APIRouter(
    prefix="/students",
    tags=["Etudiants"],
    dependencies=[Depends(get_current_user)],  # protège toutes les routes ci-dessous
)


def _to_read(student) -> StudentRead:
    """Convertit un modèle en schéma de lecture, en dérivant `has_face_embedding`."""
    data = StudentRead.model_validate(student)
    data.has_face_embedding = student.face_embedding is not None
    return data


@router.get("", response_model=list[StudentRead])
def list_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: str | None = Query(None, description="Recherche par nom, matricule ou departement"),
    db: Session = Depends(get_db),
):
    """Liste les étudiants avec pagination et recherche optionnelle."""
    students = crud_student.list_students(db, skip=skip, limit=limit, search=search)
    return [_to_read(s) for s in students]


@router.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def create_student(data: StudentCreate, db: Session = Depends(get_db)):
    """Ajoute un nouvel étudiant. Refuse un matricule déjà existant."""
    if crud_student.get_student_by_matricule(db, data.student_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un etudiant avec ce matricule existe deja",
        )
    student = crud_student.create_student(db, data)
    return _to_read(student)


@router.get("/{student_pk}", response_model=StudentRead)
def get_student(student_pk: int, db: Session = Depends(get_db)):
    """Récupère un étudiant par son identifiant interne."""
    student = crud_student.get_student(db, student_pk)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Etudiant introuvable")
    return _to_read(student)


@router.put("/{student_pk}", response_model=StudentRead)
def update_student(student_pk: int, data: StudentUpdate, db: Session = Depends(get_db)):
    """Modifie les informations d'un étudiant."""
    student = crud_student.get_student(db, student_pk)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Etudiant introuvable")
    # Vérifie l'unicité du matricule si celui-ci est modifié.
    if data.student_id and data.student_id != student.student_id:
        if crud_student.get_student_by_matricule(db, data.student_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Un etudiant avec ce matricule existe deja",
            )
    student = crud_student.update_student(db, student, data)
    return _to_read(student)


@router.delete("/{student_pk}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_pk: int, db: Session = Depends(get_db)):
    """Supprime un étudiant."""
    student = crud_student.get_student(db, student_pk)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Etudiant introuvable")
    crud_student.delete_student(db, student)


@router.post("/{student_pk}/photo", response_model=StudentRead)
async def upload_student_photo(
    student_pk: int, file: UploadFile = File(...), db: Session = Depends(get_db)
):
    """
    Enregistre la photo de reference d'un etudiant et calcule son embedding
    facial (InsightFace). Refuse les photos sans visage ou avec plusieurs
    visages : l'enrolement doit designer une seule personne sans ambiguite.
    """
    student = crud_student.get_student(db, student_pk)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Etudiant introuvable")

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
        detected = extract_single_face_embedding(content)
    except NoFaceDetected as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except MultipleFacesDetected as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    relative_path = photos.save_student_photo(student_pk, content, file.content_type)
    student = crud_student.set_student_photo(db, student, relative_path, detected.embedding)
    return _to_read(student)


@router.get("/{student_pk}/photo")
def get_student_photo(student_pk: int, db: Session = Depends(get_db)):
    """Renvoie le fichier image de la photo de reference d'un etudiant."""
    student = crud_student.get_student(db, student_pk)
    if student is None or not student.photo_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo introuvable")
    path = photos.resolve_photo_path(student.photo_path)
    if path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo introuvable")
    return FileResponse(path)
