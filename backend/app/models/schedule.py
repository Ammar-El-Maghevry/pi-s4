"""
Modèle de l'emploi du temps.

Chaque ligne représente un créneau (séance ou pause) avec son heure de début
et de fin. Les cinq séances quotidiennes sont insérées au démarrage
(voir app/initial_data.py).
"""
from sqlalchemy import Enum, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import SessionType


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Numéro d'ordre de la séance dans la journée (1 à 5).
    session_number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_time: Mapped["Time"] = mapped_column(Time, nullable=False)
    end_time: Mapped["Time"] = mapped_column(Time, nullable=False)
    session_type: Mapped[SessionType] = mapped_column(
        Enum(SessionType), default=SessionType.SESSION, nullable=False
    )
