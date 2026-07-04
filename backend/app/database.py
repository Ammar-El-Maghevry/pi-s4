"""
Connexion à la base de données et gestion des sessions SQLAlchemy.

- `engine` : le moteur de connexion à PostgreSQL.
- `SessionLocal` : fabrique de sessions (une session = une transaction).
- `Base` : classe de base dont héritent tous les modèles ORM.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# `pool_pre_ping` vérifie que la connexion est encore vivante avant chaque requête,
# ce qui évite les erreurs de connexion expirée.
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Classe de base commune à tous les modèles de la base de données."""
    pass
