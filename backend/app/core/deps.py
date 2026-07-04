"""
Dépendances injectables dans les routes FastAPI.

- `get_db`           : fournit une session de base de données par requête.
- `get_current_user` : vérifie le jeton JWT et retourne l'administrateur connecté.
"""
from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import decode_access_token
from app.database import SessionLocal
from app.models.user import User

# Indique à FastAPI où récupérer le jeton (endpoint de connexion).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


def get_db() -> Generator[Session, None, None]:
    """Ouvre une session de base de données et la ferme à la fin de la requête."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Récupère l'administrateur authentifié à partir du jeton JWT.

    Lève une erreur 401 si le jeton est invalide ou si l'utilisateur n'existe pas.
    Seuls les administrateurs peuvent accéder au système.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides ou jeton expire",
        headers={"WWW-Authenticate": "Bearer"},
    )

    email = decode_access_token(token)
    if email is None:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_active:
        raise credentials_exception

    return user
