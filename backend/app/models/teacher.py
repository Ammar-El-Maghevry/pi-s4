"""
Modèle des enseignants.

Volontairement minimal (nom, email, photo, embedding) : pas d'identifiant
matricule ni de département — un enseignant n'appartient pas à une classe, il
en anime une. La photo/embedding permet de le reconnaître en direct par la
caméra, exactement comme pour un étudiant (voir `services/attendance/live_recognition.py`).
"""
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.config import settings
from app.database import Base


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Chemin vers la photo de référence sur le disque (pas l'image elle-même en base).
    photo_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # Vecteur d'embedding facial ; rempli lors de l'enrôlement de la photo.
    face_embedding: Mapped[list[float] | None] = mapped_column(
        Vector(settings.FACE_EMBEDDING_DIM), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
