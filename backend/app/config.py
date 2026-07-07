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

    # --- Reconnaissance faciale ---
    # Dimension du vecteur d'embedding produit par InsightFace (ArcFace = 512).
    FACE_EMBEDDING_DIM: int = 512
    # Seuil de similarité cosinus au-dessus duquel deux visages sont considérés identiques.
    FACE_MATCH_THRESHOLD: float = 0.5
    # Repertoire de stockage des photos de reference (monte en volume dans docker).
    PHOTO_STORAGE_DIR: str = "./photos"

    # --- Moteur de calcul de présence (valeurs par défaut du moteur) ---
    # Part minimale de la séance passée en salle pour être compté PRÉSENT.
    ATTENDANCE_PRESENT_THRESHOLD: float = 0.7  # ≥ 70 % du créneau
    # Part minimale pour être compté EN RETARD (présence partielle) ; en dessous = ABSENT.
    ATTENDANCE_LATE_THRESHOLD: float = 0.2  # ≥ 20 % du créneau

    # NB : les paramètres propres à une caméra (source du flux, ligne de
    # franchissement, seuils, cooldown, sens de traversée) ne vivent plus ici ni
    # dans le .env. Ils sont configurés par l'administrateur via l'API et stockés
    # en base (table `cameras`). Le .env ne contient que les secrets
    # d'infrastructure (SECRET_KEY, DATABASE_URL).

    # --- Général ---
    PROJECT_NAME: str = "Systeme de presence intelligent"
    API_V1_PREFIX: str = "/api/v1"

    # --- CORS ---
    # Origines autorisees a appeler l'API (liste separee par des virgules dans .env).
    # Permet de pointer vers le frontend sans modifier le code (docker, autre port...).
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # --- Envoi d'e-mails (lien d'appairage d'une camera telephone) ---
    # SMTP_HOST vide = envoi desactive (dev local sans boite mail configuree).
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "no-reply@presence.sys"
    SMTP_USE_TLS: bool = True
    # Origine (schema+hote+port) a partir de laquelle construire le lien
    # /phone-camera/<token> envoye par email (le port HTTPS du frontend).
    PHONE_PAIRING_BASE_URL: str = "https://localhost:8443"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Retourne une instance unique (mise en cache) de la configuration."""
    return Settings()


settings = get_settings()
