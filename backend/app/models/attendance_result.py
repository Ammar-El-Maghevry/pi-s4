"""
Modèle des résultats de présence.

Une ligne = le statut d'un étudiant pour une séance donnée à une date donnée.
Ces lignes sont produites par le moteur de calcul (phase 6) à partir des
événements bruts. La contrainte d'unicité (étudiant, séance, date) empêche les
doublons de présence.
"""
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import AttendanceStatus


class AttendanceResult(Base):
    __tablename__ = "attendance_results"
    __table_args__ = (
        UniqueConstraint("student_id", "schedule_id", "result_date", name="uq_presence_unique"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    schedule_id: Mapped[int] = mapped_column(
        ForeignKey("schedules.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # Date du jour concerné par le calcul.
    result_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    status: Mapped[AttendanceStatus] = mapped_column(Enum(AttendanceStatus), nullable=False)
    # Première entrée et dernière sortie retenues pour la séance (informatif).
    entry_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    exit_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    student = relationship("Student")
    schedule = relationship("Schedule")
