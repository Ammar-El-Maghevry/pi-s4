"""Schémas Pydantic pour les étudiants (création, mise à jour, lecture)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class StudentBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    student_id: str = Field(min_length=1, max_length=50)
    email: EmailStr | None = None
    department: str | None = Field(default=None, max_length=150)


class StudentCreate(StudentBase):
    """Données requises pour créer un étudiant."""
    pass


class StudentUpdate(BaseModel):
    """
    Données pour modifier un étudiant.

    Tous les champs sont optionnels : on ne met à jour que ce qui est fourni.
    """
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    student_id: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr | None = None
    department: str | None = Field(default=None, max_length=150)


class StudentRead(StudentBase):
    """Représentation renvoyée par l'API."""
    id: int
    # Classe auto-assignee a la creation/mise a jour (voir crud/student.py) ;
    # non modifiable directement, derivee du departement.
    class_name: str | None = None
    photo_path: str | None = None
    # Indique si l'embedding facial a déjà été calculé (booléen dérivé).
    has_face_embedding: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
