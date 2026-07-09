"""Schémas Pydantic pour les enseignants (création, mise à jour, lecture, présence)."""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TeacherBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr | None = None


class TeacherCreate(TeacherBase):
    """Données requises pour créer un enseignant."""
    pass


class TeacherUpdate(BaseModel):
    """Données pour modifier un enseignant ; tous les champs sont optionnels."""
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None


class TeacherRead(TeacherBase):
    """Représentation renvoyée par l'API."""
    id: int
    photo_path: str | None = None
    # Indique si l'embedding facial a déjà été calculé (booléen dérivé).
    has_face_embedding: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeacherAttendanceRead(BaseModel):
    """Statut de présence d'un enseignant pour une date donnée."""
    teacher_id: int
    attendance_date: date
    is_present: bool
    source: str

    model_config = ConfigDict(from_attributes=True)


class TeacherAttendanceSet(BaseModel):
    """Données pour positionner manuellement la présence d'un enseignant."""
    is_present: bool
