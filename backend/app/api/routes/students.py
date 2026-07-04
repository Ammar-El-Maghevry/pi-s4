"""
Routes de gestion des étudiants (CRUD + recherche).

Toutes ces routes sont protégées : seul un administrateur authentifié y accède
(dépendance `get_current_user`).
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.crud import student as crud_student
from app.models.user import User
from app.schemas.student import StudentCreate, StudentRead, StudentUpdate

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
