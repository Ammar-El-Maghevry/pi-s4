"""
Modèle des étudiants.

Le champ `face_embedding` stocke le vecteur produit par InsightFace (512
dimensions). Il est nullable : lors de la phase 1, un étudiant peut être créé
sans photo encodée. La recherche par similarité (phases suivantes) utilisera
l'extension pgvector.
"""
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.config import settings
from app.database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    # Numéro d'étudiant unique (matricule universitaire).
    student_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    department: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)
    # Chemin vers la photo de référence sur le disque (pas l'image elle-même en base).
    photo_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # Vecteur d'embedding facial ; rempli lors de l'enrôlement (phase 2).
    face_embedding: Mapped[list[float] | None] = mapped_column(
        Vector(settings.FACE_EMBEDDING_DIM), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
