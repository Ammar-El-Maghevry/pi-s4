"""
Couche d'accès aux données pour les administrateurs.

Cette couche isole la logique de base de données des routes API, conformément
à l'architecture en couches du projet.
"""
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate


def get_user_by_email(db: Session, email: str) -> User | None:
    """Recherche un administrateur par son email."""
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, data: UserCreate) -> User:
    """Crée un administrateur en hachant son mot de passe."""
    user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """
    Vérifie les identifiants de connexion.

    Retourne l'utilisateur si l'email existe et que le mot de passe correspond,
    sinon `None`.
    """
    user = get_user_by_email(db, email)
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user
