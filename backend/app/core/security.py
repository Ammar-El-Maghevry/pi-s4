"""
Primitives de sécurité : hachage des mots de passe et création/vérification
des jetons JWT.

On ne stocke jamais un mot de passe en clair : seul son hachage bcrypt est
enregistré en base.
"""
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# Contexte de hachage : bcrypt est l'algorithme recommandé pour les mots de passe.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Retourne le hachage bcrypt d'un mot de passe en clair."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie qu'un mot de passe en clair correspond au hachage stocké."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    """
    Crée un jeton JWT signé.

    `subject` : identifiant de l'utilisateur (ici son email).
    `exp`     : date d'expiration au-delà de laquelle le jeton n'est plus valide.
    """
    expire_minutes = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """
    Décode et vérifie un jeton JWT.

    Retourne l'identifiant (`sub`) si le jeton est valide, sinon `None`.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
