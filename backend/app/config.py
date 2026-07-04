"""
Configuration centrale de l'application.

Toutes les valeurs sensibles (secret JWT, URL de la base de données...)
sont chargées depuis les variables d'environnement ou le fichier .env.
On ne code jamais un secret en dur dans le code source.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Base de données ---
    # URL de connexion PostgreSQL (format SQLAlchemy).
    DATABASE_URL: str = "postgresql+psycopg2://attendance:attendance@localhost:5432/attendance"

    # --- Sécurité / JWT ---
    # Clé secrète utilisée pour signer les jetons. À remplacer en production.
    SECRET_KEY: str = "changez-cette-cle-en-production"
    ALGORITHM: str = "HS256"
    # Durée de validité du jeton d'accès (en minutes).
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 heures

    # --- Reconnaissance faciale (préparé pour les phases suivantes) ---
    # Dimension du vecteur d'embedding produit par InsightFace (ArcFace = 512).
    FACE_EMBEDDING_DIM: int = 512
    # Seuil de similarité cosinus au-dessus duquel deux visages sont considérés identiques.
    FACE_MATCH_THRESHOLD: float = 0.5

    # --- Général ---
    PROJECT_NAME: str = "Systeme de presence intelligent"
    API_V1_PREFIX: str = "/api/v1"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Retourne une instance unique (mise en cache) de la configuration."""
    return Settings()


settings = get_settings()
