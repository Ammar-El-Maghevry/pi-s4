"""
Modèle de présence des enseignants.

Contrairement aux étudiants (évènements bruts + moteur de calcul par séance,
voir `attendance_event.py`/`attendance_result.py`), un enseignant n'est pas
assigné à une classe : sa présence est un simple drapeau présent/absent par
jour, positionné soit manuellement (page People), soit automatiquement dès
qu'il est reconnu par la caméra d'une séance en cours (voir
`services/attendance/live_recognition.py`).
"""
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TeacherAttendance(Base):
    __tablename__ = "teacher_attendance"
    __table_args__ = (
        UniqueConstraint("teacher_id", "attendance_date", name="uq_teacher_attendance_unique"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    attendance_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    is_present: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # "manual" (bouton People) ou "camera" (reconnaissance en direct).
    source: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)
    marked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    teacher = relationship("Teacher")
