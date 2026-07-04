"""
Modèle des captures d'image.

Le système ne conserve JAMAIS la vidéo complète : uniquement une capture au
moment de l'entrée et une au moment de la sortie. Seul le chemin du fichier est
stocké en base ; l'image reste sur le disque.
"""
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import EventType


class Snapshot(Base):
    __tablename__ = "snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int | None] = mapped_column(
        ForeignKey("students.id", ondelete="SET NULL"), index=True, nullable=True
    )
    # Chemin du fichier image sur le disque.
    image_path: Mapped[str] = mapped_column(String(512), nullable=False)
    # Précise s'il s'agit d'une capture d'entrée ou de sortie.
    event_type: Mapped[EventType] = mapped_column(Enum(EventType), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    student = relationship("Student")
