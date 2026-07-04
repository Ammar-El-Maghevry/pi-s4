"""Schémas Pydantic pour les administrateurs (entrée et sortie API)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    """Données requises pour créer un administrateur."""
    password: str


class UserRead(UserBase):
    """Représentation renvoyée par l'API (sans le mot de passe)."""
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
