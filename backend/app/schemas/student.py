"""Schémas Pydantic pour les étudiants (création, mise à jour, lecture)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class StudentBase(BaseModel):
    full_name: str
    student_id: str
    email: EmailStr | None = None
    department: str | None = None


class StudentCreate(StudentBase):
    """Données requises pour créer un étudiant."""
    pass


class StudentUpdate(BaseModel):
    """
    Données pour modifier un étudiant.

    Tous les champs sont optionnels : on ne met à jour que ce qui est fourni.
    """
    full_name: str | None = None
    student_id: str | None = None
    email: EmailStr | None = None
    department: str | None = None


class StudentRead(StudentBase):
    """Représentation renvoyée par l'API."""
    id: int
    photo_path: str | None = None
    # Indique si l'embedding facial a déjà été calculé (booléen dérivé).
    has_face_embedding: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
