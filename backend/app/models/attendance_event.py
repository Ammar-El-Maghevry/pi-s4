"""
Modèle des événements de présence bruts.

Chaque passage détecté (entrée ou sortie) est enregistré tel quel, avec son
horodatage. Le statut de présence n'est PAS calculé ici : c'est le moteur de
calcul (phase 6) qui, plus tard, dérivera la présence par séance à partir de
ces événements.
"""
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import EventType


class AttendanceEvent(Base):
    __tablename__ = "attendance_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    event_type: Mapped[EventType] = mapped_column(Enum(EventType), nullable=False)
    # Horodatage précis du passage devant la caméra.
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, nullable=False
    )
    # Score de confiance de la reconnaissance (rempli en phase 4).
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Identifiant de la caméra source (préparé pour le multi-caméras).
    camera_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Lien optionnel vers la capture associée à l'événement.
    snapshot_id: Mapped[int | None] = mapped_column(
        ForeignKey("snapshots.id", ondelete="SET NULL"), nullable=True
    )

    student = relationship("Student")
    snapshot = relationship("Snapshot")
