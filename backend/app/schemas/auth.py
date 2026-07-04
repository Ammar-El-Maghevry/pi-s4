"""Schémas liés à l'authentification (jeton et connexion)."""
from pydantic import BaseModel


class Token(BaseModel):
    """Réponse renvoyée après une connexion réussie."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Contenu utile extrait d'un jeton."""
    email: str | None = None
