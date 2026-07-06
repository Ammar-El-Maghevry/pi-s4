"""
Script d'initialisation des données de base.

À exécuter une fois après les migrations :
    python -m app.initial_data

Crée :
- un administrateur par défaut (admin@example.com / admin123) si aucun n'existe ;
- les cinq séances quotidiennes et les pauses de l'emploi du temps.

Le mot de passe par défaut doit être changé immédiatement en production.
"""
from datetime import time

from app.database import SessionLocal
from app.models.enums import SessionType
from app.models.schedule import Schedule
from app.models.user import User
from app.schemas.user import UserCreate
from app.crud.user import create_user, get_user_by_email

# Emploi du temps : (numéro, nom, début, fin, type)
SCHEDULE = [
    (1, "Seance 1", time(8, 0), time(9, 30), SessionType.SESSION),
    (0, "Pause", time(9, 30), time(9, 45), SessionType.BREAK),
    (2, "Seance 2", time(9, 45), time(11, 15), SessionType.SESSION),
    (0, "Pause", time(11, 15), time(11, 30), SessionType.BREAK),
    (3, "Seance 3", time(11, 30), time(13, 0), SessionType.SESSION),
    (0, "Pause dejeuner", time(13, 0), time(15, 0), SessionType.BREAK),
    (4, "Seance 4", time(15, 0), time(16, 30), SessionType.SESSION),
    (0, "Pause", time(16, 30), time(16, 45), SessionType.BREAK),
    (5, "Seance 5", time(16, 45), time(18, 0), SessionType.SESSION),
]


def seed() -> None:
    db = SessionLocal()
    try:
        # 1) Administrateur par défaut
        if get_user_by_email(db, "admin@example.com") is None:
            create_user(
                db,
                UserCreate(
                    email="admin@example.com",
                    full_name="Administrateur",
                    password="admin123",
                ),
            )
            print("Administrateur cree : admin@example.com / admin123")
        else:
            print("Administrateur deja present.")

        # 2) Emploi du temps
        if db.query(Schedule).count() == 0:
            for num, name, start, end, stype in SCHEDULE:
                db.add(
                    Schedule(
                        session_number=num,
                        name=name,
                        start_time=start,
                        end_time=end,
                        session_type=stype,
                    )
                )
            db.commit()
            print(f"{len(SCHEDULE)} creneaux inseres dans l'emploi du temps.")
        else:
            print("Emploi du temps deja present.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
